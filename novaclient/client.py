# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.

# All Rights Reserved.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import httplib2
import logging
import os
import urlparse

try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl

from novaclient import exceptions
from novaclient import service_catalog
from novaclient import utils


_logger = logging.getLogger(__name__)


class HTTPClient(httplib2.Http):

    USER_AGENT = 'python-novaclient'

    def __init__(self, user, password, projectid, auth_url, insecure=False,
                 timeout=None, token=None, region_name=None,
                 endpoint_type='publicURL', service_name=None):
        super(HTTPClient, self).__init__(timeout=timeout)
        self.user = user
        self.password = password
        self.projectid = projectid
        self.auth_url = auth_url
        self.version = 'v1.1'
        self.region_name = region_name
        self.endpoint_type = endpoint_type
        self.service_name = service_name

        self.management_url = None
        self.auth_token = None
        self.proxy_token = token

        # httplib2 overrides
        self.force_exception_to_status_code = True
        self.disable_ssl_certificate_validation = insecure

    def http_log(self, args, kwargs, resp, body):
        if 'NOVACLIENT_DEBUG' in os.environ and os.environ['NOVACLIENT_DEBUG']:
            ch = logging.StreamHandler()
            _logger.setLevel(logging.DEBUG)
            _logger.addHandler(ch)
        elif not _logger.isEnabledFor(logging.DEBUG):
            return

        string_parts = ['curl -i']
        for element in args:
            if element in ('GET', 'POST'):
                string_parts.append(' -X %s' % element)
            else:
                string_parts.append(' %s' % element)

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        _logger.debug("REQ: %s\n" % "".join(string_parts))
        if 'body' in kwargs:
            _logger.debug("REQ BODY: %s\n" % (kwargs['body']))
        _logger.debug("RESP:%s %s\n", resp, body)

    def request(self, *args, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['User-Agent'] = self.USER_AGENT
        kwargs['headers']['Accept'] = 'application/json'
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['body'] = json.dumps(kwargs['body'])

        resp, body = super(HTTPClient, self).request(*args, **kwargs)

        self.http_log(args, kwargs, resp, body)

        if body:
            try:
                body = json.loads(body)
            except ValueError, e:
                pass
        else:
            body = None

        if resp.status in (400, 401, 403, 404, 408, 409, 413, 500, 501):
            raise exceptions.from_response(resp, body)

        return resp, body

    def _cs_request(self, url, method, **kwargs):
        if not self.management_url:
            self.authenticate()

        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            kwargs.setdefault('headers', {})['X-Auth-Token'] = self.auth_token
            if self.projectid:
                kwargs['headers']['X-Auth-Project-Id'] = self.projectid

            resp, body = self.request(self.management_url + url, method,
                                      **kwargs)
            return resp, body
        except exceptions.Unauthorized, ex:
            try:
                self.authenticate()
                resp, body = self.request(self.management_url + url, method,
                                          **kwargs)
                return resp, body
            except exceptions.Unauthorized:
                raise ex

    def get(self, url, **kwargs):
        return self._cs_request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)

    def _extract_service_catalog(self, url, resp, body, extract_token=True):
        """See what the auth service told us and process the response.
        We may get redirected to another site, fail or actually get
        back a service catalog with a token and our endpoints."""

        if resp.status == 200:  # content must always present
            try:
                self.auth_url = url
                self.service_catalog = \
                    service_catalog.ServiceCatalog(body)

                if extract_token:
                    self.auth_token = self.service_catalog.get_token()
                self.management_url = self.service_catalog.url_for(
                                           attr='region',
                                           filter_value=self.region_name,
                                           endpoint_type=self.endpoint_type,
                                           service_name=self.service_name)
                return None
            except exceptions.AmbiguousEndpoints, exc:
                print "Found more than one valid endpoint. Use a more " \
                      "restrictive filter"
                raise
            except KeyError:
                raise exceptions.AuthorizationFailure()
            except exceptions.EndpointNotFound:
                print "Could not find any suitable endpoint. Correct region?"
                raise

        elif resp.status == 305:
            return resp['location']
        else:
            raise exceptions.from_response(resp, body)

    def _fetch_endpoints_from_auth(self, url):
        """We have a token, but don't know the final endpoint for
        the region. We have to go back to the auth service and
        ask again. This request requires an admin-level token
        to work. The proxy token supplied could be from a low-level enduser.

        We can't get this from the keystone service endpoint, we have to use
        the admin endpoint.

        This will overwrite our admin token with the user token.
        """

        # GET ...:5001/v2.0/tokens/#####/endpoints
        end = '/'.join(['tokens', self.proxy_token, 'endpoints'])
        url = urlparse.urljoin(url, end)
        _logger.debug("Using Endpoint URL: %s" % url)
        resp, body = self.request(url, "GET",
                                  headers={'X-Auth_Token': self.auth_token})
        return self._extract_service_catalog(url, resp, body,
                                             extract_token=False)

    def authenticate(self):
        magic_tuple = urlparse.urlsplit(self.auth_url)
        scheme, netloc, path, query, frag = magic_tuple
        port = magic_tuple.port
        if port is None:
            port = 80
        path_parts = path.split('/')
        for part in path_parts:
            if len(part) > 0 and part[0] == 'v':
                self.version = part
                break

        # TODO(sandy): Assume admin endpoint is 35357 for now.
        # Ideally this is going to have to be provided by the service catalog.
        new_netloc = netloc.replace(':%d' % port, ':%d' % (35357,))
        admin_url = urlparse.urlunsplit(
                        (scheme, new_netloc, path, query, frag))

        auth_url = self.auth_url
        if self.version == "v2.0":  # FIXME(chris): This should be better.
            while auth_url:
                if "NOVA_RAX_AUTH" in os.environ:
                    auth_url = self._rax_auth(auth_url)
                else:
                    auth_url = self._v2_auth(auth_url)

            # Are we acting on behalf of another user via an
            # existing token? If so, our actual endpoints may
            # be different than that of the admin token.
            if self.proxy_token:
                self._fetch_endpoints_from_auth(admin_url)
                # Since keystone no longer returns the user token
                # with the endpoints any more, we need to replace
                # our service account token with the user token.
                self.auth_token = self.proxy_token
        else:
            try:
                while auth_url:
                    auth_url = self._v1_auth(auth_url)
            # In some configurations nova makes redirection to
            # v2.0 keystone endpoint. Also, new location does not contain
            # real endpoint, only hostname and port.
            except exceptions.AuthorizationFailure:
                if auth_url.find('v2.0') < 0:
                    auth_url = urlparse.urljoin(auth_url, 'v2.0/')
                self._v2_auth(auth_url)

    def _v1_auth(self, url):
        if self.proxy_token:
            raise exceptions.NoTokenLookupException()

        headers = {'X-Auth-User': self.user,
                   'X-Auth-Key': self.password}
        if self.projectid:
            headers['X-Auth-Project-Id'] = self.projectid

        resp, body = self.request(url, 'GET', headers=headers)
        if resp.status in (200, 204):  # in some cases we get No Content
            try:
                self.management_url = resp['x-server-management-url']
                self.auth_token = resp['x-auth-token']
                self.auth_url = url
            except KeyError:
                raise exceptions.AuthorizationFailure()
        elif resp.status == 305:
            return resp['location']
        else:
            raise exceptions.from_response(resp, body)

    def _v2_auth(self, url):
        """Authenticate against a v2.0 auth service."""
        body = {"auth": {
                   "passwordCredentials": {"username": self.user,
                                           "password": self.password}}}

        if self.projectid:
            body['auth']['tenantName'] = self.projectid

        self._authenticate(url, body)

    def _rax_auth(self, url):
        """Authenticate against the Rackspace auth service."""
        body = {"auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                        "username": self.user,
                        "apiKey": self.password,
                        "tenantName": self.projectid}}}

        self._authenticate(url, body)

    def _authenticate(self, url, body):
        """Authenticate and extract the service catalog."""
        token_url = urlparse.urljoin(url, "tokens")

        # Make sure we follow redirects when trying to reach Keystone
        tmp_follow_all_redirects = self.follow_all_redirects
        self.follow_all_redirects = True

        try:
            resp, body = self.request(token_url, "POST", body=body)
        finally:
            self.follow_all_redirects = tmp_follow_all_redirects

        return self._extract_service_catalog(url, resp, body)


def get_client_class(version):
    version_map = {
        '1.1': 'novaclient.v1_1.client.Client',
        '2': 'novaclient.v1_1.client.Client',
    }
    try:
        client_path = version_map[str(version)]
    except (KeyError, ValueError):
        msg = "Invalid client version '%s'. must be one of: %s" % (
              (version, ', '.join(version_map.keys())))
        raise exceptions.UnsupportedVersion(msg)

    return utils.import_class(client_path)


def Client(version, *args, **kwargs):
    client_class = get_client_class(version)
    return client_class(*args, **kwargs)

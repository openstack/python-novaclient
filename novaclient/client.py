# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.

# All Rights Reserved.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import httplib2

has_keyring = False
try:
    import keyring
    has_keyring = True
except ImportError:
    pass

import logging
import os
import time
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


class HTTPClient(httplib2.Http):

    USER_AGENT = 'python-novaclient'

    def __init__(self, user, password, projectid, auth_url, insecure=False,
                 timeout=None, proxy_tenant_id=None,
                 proxy_token=None, region_name=None,
                 endpoint_type='publicURL', service_type=None,
                 service_name=None, volume_service_name=None,
                 timings=False, bypass_url=None, no_cache=False,
                 http_log_debug=False):
        super(HTTPClient, self).__init__(timeout=timeout)
        self.user = user
        self.password = password
        self.projectid = projectid
        self.auth_url = auth_url.rstrip('/')
        self.version = 'v1.1'
        self.region_name = region_name
        self.endpoint_type = endpoint_type
        self.service_type = service_type
        self.service_name = service_name
        self.volume_service_name = volume_service_name
        self.timings = timings
        self.bypass_url = bypass_url
        self.no_cache = no_cache
        self.http_log_debug = http_log_debug

        self.times = []  # [("item", starttime, endtime), ...]

        self.management_url = None
        self.auth_token = None
        self.proxy_token = proxy_token
        self.proxy_tenant_id = proxy_tenant_id
        self.used_keyring = False

        # httplib2 overrides
        self.force_exception_to_status_code = True
        self.disable_ssl_certificate_validation = insecure

        self._logger = logging.getLogger(__name__)
        if self.http_log_debug:
            ch = logging.StreamHandler()
            self._logger.setLevel(logging.DEBUG)
            self._logger.addHandler(ch)

    def use_token_cache(self, use_it):
        # One day I'll stop using negative naming.
        self.no_cache = not use_it

    def unauthenticate(self):
        """Forget all of our authentication information."""
        self.management_url = None
        self.auth_token = None
        self.used_keyring = False

    def set_management_url(self, url):
        self.management_url = url

    def get_timings(self):
        return self.times

    def reset_timings(self):
        self.times = []

    def http_log(self, args, kwargs, resp, body):
        if not self.http_log_debug:
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

        self._logger.debug("\nREQ: %s\n" % "".join(string_parts))
        if 'body' in kwargs:
            self._logger.debug("REQ BODY: %s\n" % (kwargs['body']))
        self._logger.debug("RESP:%s %s\n", resp, body)

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
            except ValueError:
                pass
        else:
            body = None

        if resp.status >= 400:
            raise exceptions.from_response(resp, body)

        return resp, body

    def _time_request(self, url, method, **kwargs):
        start_time = time.time()
        resp, body = self.request(url, method, **kwargs)
        self.times.append(("%s %s" % (method, url),
                           start_time, time.time()))
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

            resp, body = self._time_request(self.management_url + url, method,
                                      **kwargs)
            return resp, body
        except exceptions.Unauthorized, ex:
            try:
                self.authenticate()
                resp, body = self._time_request(self.management_url + url,
                                                method, **kwargs)
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

                management_url = self.service_catalog.url_for(
                               attr='region',
                               filter_value=self.region_name,
                               endpoint_type=self.endpoint_type,
                               service_type=self.service_type,
                               service_name=self.service_name,
                               volume_service_name=self.volume_service_name,)
                self.management_url = management_url.rstrip('/')
                return None
            except exceptions.AmbiguousEndpoints:
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
        url = '/'.join([url, 'tokens', '%s?belongsTo=%s'
                        % (self.proxy_token, self.proxy_tenant_id)])
        self._logger.debug("Using Endpoint URL: %s" % url)
        resp, body = self._time_request(url, "GET",
                                  headers={'X-Auth_Token': self.auth_token})
        return self._extract_service_catalog(url, resp, body,
                                             extract_token=False)

    def authenticate(self):
        if has_keyring:
            keys = [self.auth_url, self.user, self.region_name,
                    self.endpoint_type, self.service_type, self.service_name,
                    self.volume_service_name]
            for index, key in enumerate(keys):
                if key is None:
                    keys[index] = '?'
            keyring_key = "/".join(keys)
            if not self.no_cache and not self.used_keyring:
                # Lookup the token/mgmt url from the keyring first time
                # through.
                # If we come through again, it's because the old token
                # was rejected.
                try:
                    block = keyring.get_password("novaclient_auth",
                                                 keyring_key)
                    if block:
                        self.used_keyring = True
                        self.auth_token, self.management_url = block.split('|')
                        return
                except Exception:
                    pass

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
                    auth_url = auth_url + '/v2.0'
                self._v2_auth(auth_url)

        if self.bypass_url:
            self.set_management_url(self.bypass_url)

        # Store the token/mgmt url in the keyring for later requests.
        if has_keyring and not self.no_cache:
            try:
                keyring_value = "%s|%s" % (self.auth_token,
                                           self.management_url)
                keyring.set_password("novaclient_auth",
                                     keyring_key, keyring_value)
            except Exception:
                pass

    def _v1_auth(self, url):
        if self.proxy_token:
            raise exceptions.NoTokenLookupException()

        headers = {'X-Auth-User': self.user,
                   'X-Auth-Key': self.password}
        if self.projectid:
            headers['X-Auth-Project-Id'] = self.projectid

        resp, body = self._time_request(url, 'GET', headers=headers)
        if resp.status in (200, 204):  # in some cases we get No Content
            try:
                mgmt_header = 'x-server-management-url'
                self.management_url = resp[mgmt_header].rstrip('/')
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
        token_url = url + "/tokens"

        # Make sure we follow redirects when trying to reach Keystone
        tmp_follow_all_redirects = self.follow_all_redirects
        self.follow_all_redirects = True

        try:
            resp, body = self._time_request(token_url, "POST", body=body)
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

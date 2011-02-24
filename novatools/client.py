# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import time
import urlparse
import urllib
import httplib2
try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl

import novatools
from novatools import exceptions


class OpenStackClient(httplib2.Http):

    USER_AGENT = 'python-novatools/%s' % novatools.__version__

    def __init__(self, user, apikey, auth_url):
        super(OpenStackClient, self).__init__()
        self.user = user
        self.apikey = apikey
        self.auth_url = auth_url

        self.management_url = None
        self.auth_token = None

        # httplib2 overrides
        self.force_exception_to_status_code = True

    def request(self, *args, **kwargs):
        kwargs.setdefault('headers', {})
        kwargs['headers']['User-Agent'] = self.USER_AGENT
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['body'] = json.dumps(kwargs['body'])

        if httplib2.debuglevel == 1:
            print "ARGS:", args
        resp, body = super(OpenStackClient, self).request(*args, **kwargs)
        if httplib2.debuglevel == 1:
            print "RESPONSE", resp
            print "BODY", body
        if body:
            try:
                body = json.loads(body)
            except ValueError, e:
                pass
        else:
            body = None

        if resp.status in (400, 401, 403, 404, 413, 500, 501):
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
        url = self._munge_get_url(url)
        return self._cs_request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)

    def authenticate(self):
        headers = {'X-Auth-User': self.user, 'X-Auth-Key': self.apikey}
        resp, body = self.request(self.auth_url, 'GET', headers=headers)
        self.management_url = resp['x-server-management-url']
        self.auth_token = resp['x-auth-token']

    def _munge_get_url(self, url):
        """
        Munge GET URLs to always return uncached content.

        The OpenStack Nova API caches data *very* agressively and doesn't
        respect cache headers. To avoid stale data, then, we append a little
        bit of nonsense onto GET parameters; this appears to force the data not
        to be cached.
        """
        scheme, netloc, path, query, frag = urlparse.urlsplit(url)
        query = urlparse.parse_qsl(query)
        query.append(('fresh', str(time.time())))
        query = urllib.urlencode(query)
        return urlparse.urlunsplit((scheme, netloc, path, query, frag))

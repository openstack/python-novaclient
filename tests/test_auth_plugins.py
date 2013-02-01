# Copyright 2012 OpenStack LLC.
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

import mock
import pkg_resources
import requests

try:
    import json
except ImportError:
    import simplejson as json

from novaclient import exceptions
from novaclient.v1_1 import client
from tests import utils


def mock_http_request(resp=None):
    """Mock an HTTP Request."""
    if not resp:
        resp = {
            "access": {
                "token": {
                    "expires": "12345",
                    "id": "FAKE_ID",
                    "tenant": {
                        "id": "FAKE_TENANT_ID",
                    }
                },
                "serviceCatalog": [
                    {
                        "type": "compute",
                        "endpoints": [
                            {
                                "region": "RegionOne",
                                "adminURL": "http://localhost:8774/v1.1",
                                "internalURL":"http://localhost:8774/v1.1",
                                "publicURL": "http://localhost:8774/v1.1/",
                            },
                        ],
                    },
                ],
            },
        }

    auth_response = utils.TestResponse({
        "status_code": 200,
        "text": json.dumps(resp),
    })
    return mock.Mock(return_value=(auth_response))


def requested_headers(cs):
    """Return requested passed headers."""
    return {
        'User-Agent': cs.client.USER_AGENT,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


class AuthPluginTest(utils.TestCase):
    def test_auth_system_success(self):
        class MockEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return self.authenticate

            def authenticate(self, cls, auth_url):
                cls._authenticate(auth_url, {"fake": "me"})

        def mock_iter_entry_points(_type):
            if _type == 'openstack.client.authenticate':
                return [MockEntrypoint("fake", "fake", ["fake"])]

        mock_request = mock_http_request()

        @mock.patch.object(pkg_resources, "iter_entry_points",
                           mock_iter_entry_points)
        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            cs = client.Client("username", "password", "project_id",
                               "auth_url/v2.0", auth_system="fake")
            cs.client.authenticate()

            headers = requested_headers(cs)
            token_url = cs.client.auth_url + "/tokens"

            mock_request.assert_called_with(
                "POST",
                token_url,
                headers=headers,
                data='{"fake": "me"}',
                allow_redirects=True,
                **self.TEST_REQUEST_BASE)

        test_auth_call()

    def test_auth_system_not_exists(self):
        def mock_iter_entry_points(_t):
            return [pkg_resources.EntryPoint("fake", "fake", ["fake"])]

        mock_request = mock_http_request()

        @mock.patch.object(pkg_resources, "iter_entry_points",
                           mock_iter_entry_points)
        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            cs = client.Client("username", "password", "project_id",
                               "auth_url/v2.0", auth_system="notexists")
            self.assertRaises(exceptions.AuthSystemNotFound,
                              cs.client.authenticate)

        test_auth_call()

    def test_auth_system_defining_auth_url(self):
        class MockAuthUrlEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return self.auth_url

            def auth_url(self):
                return "http://faked/v2.0"

        class MockAuthenticateEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return self.authenticate

            def authenticate(self, cls, auth_url):
                cls._authenticate(auth_url, {"fake": "me"})

        def mock_iter_entry_points(_type):
            if _type == 'openstack.client.auth_url':
                return [MockAuthUrlEntrypoint("fakewithauthurl",
                                           "fakewithauthurl.plugin",
                                           ["auth_url"])]
            elif _type == 'openstack.client.authenticate':
                return [MockAuthenticateEntrypoint("fakewithauthurl",
                                                   "fakewithauthurl.plugin",
                                                   ["auth_url"])]
        mock_request = mock_http_request()

        @mock.patch.object(pkg_resources, "iter_entry_points",
                           mock_iter_entry_points)
        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            cs = client.Client("username", "password", "project_id",
                               auth_system="fakewithauthurl")
            cs.client.authenticate()
            self.assertEquals(cs.client.auth_url, "http://faked/v2.0")

        test_auth_call()

    def test_auth_system_raises_exception_when_missing_auth_url(self):
        class MockAuthUrlEntrypoint(pkg_resources.EntryPoint):
            def load(self):
                return self.auth_url

            def auth_url(self):
                return None

        def mock_iter_entry_points(_type):
            return [MockAuthUrlEntrypoint("fakewithauthurl",
                                          "fakewithauthurl.plugin",
                                          ["auth_url"])]

        @mock.patch.object(pkg_resources, "iter_entry_points",
                           mock_iter_entry_points)
        def test_auth_call():
            self.assertRaises(
                exceptions.EndpointNotFound,
                client.Client, "username", "password", "project_id",
                auth_system="fakewithauthurl")

        test_auth_call()

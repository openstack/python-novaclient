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
import requests

import novaclient.client
import novaclient.v1_1.client
from tests import utils


class ClientTest(utils.TestCase):

    def test_client_with_timeout(self):
        instance = novaclient.client.HTTPClient(user='user',
                                                password='password',
                                                projectid='project',
                                                timeout=2,
                                                auth_url="http://www.blah.com")
        self.assertEqual(instance.timeout, 2)
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
            'x-auth-token': 'blah',
        }
        with mock.patch('requests.request', mock_request):
            instance.authenticate()
            requests.request.assert_called_with(mock.ANY, mock.ANY,
                                                timeout=2,
                                                headers=mock.ANY,
                                                verify=mock.ANY)

    def test_get_client_class_v2(self):
        output = novaclient.client.get_client_class('2')
        self.assertEqual(output, novaclient.v1_1.client.Client)

    def test_get_client_class_v2_int(self):
        output = novaclient.client.get_client_class(2)
        self.assertEqual(output, novaclient.v1_1.client.Client)

    def test_get_client_class_v1_1(self):
        output = novaclient.client.get_client_class('1.1')
        self.assertEqual(output, novaclient.v1_1.client.Client)

    def test_get_client_class_unknown(self):
        self.assertRaises(novaclient.exceptions.UnsupportedVersion,
                          novaclient.client.get_client_class, '0')

    def test_client_with_os_cache_enabled(self):
        cs = novaclient.v1_1.client.Client("user", "password", "project_id",
                                           auth_url="foo/v2", os_cache=True)
        self.assertEqual(True, cs.os_cache)
        self.assertEqual(True, cs.client.os_cache)

    def test_client_with_os_cache_disabled(self):
        cs = novaclient.v1_1.client.Client("user", "password", "project_id",
                                           auth_url="foo/v2", os_cache=False)
        self.assertEqual(False, cs.os_cache)
        self.assertEqual(False, cs.client.os_cache)

    def test_client_with_no_cache_enabled(self):
        cs = novaclient.v1_1.client.Client("user", "password", "project_id",
                                           auth_url="foo/v2", no_cache=True)
        self.assertEqual(False, cs.os_cache)
        self.assertEqual(False, cs.client.os_cache)

    def test_client_with_no_cache_disabled(self):
        cs = novaclient.v1_1.client.Client("user", "password", "project_id",
                                           auth_url="foo/v2", no_cache=False)
        self.assertEqual(True, cs.os_cache)
        self.assertEqual(True, cs.client.os_cache)

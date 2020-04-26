# Copyright 2015 NEC Corporation.  All rights reserved.
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

from unittest import mock

from novaclient import api_versions
from novaclient import exceptions as exc
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import versions


class VersionsTest(utils.TestCase):
    def setUp(self):
        super(VersionsTest, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.0"))
        self.service_type = versions.Version

    def test_list_services(self):
        vl = self.cs.versions.list()
        self.assert_request_id(vl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', 'http://nova-api:8774')

    def test_get_current(self):
        self.cs.callback = []
        v = self.cs.versions.get_current()
        self.assert_request_id(v, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', 'http://nova-api:8774/v2.1/')

    @mock.patch.object(versions.VersionManager, '_get',
                       side_effect=exc.Unauthorized("401 RAX"))
    def test_get_current_with_rax_workaround(self, get):
        self.cs.callback = []
        self.assertIsNone(self.cs.versions.get_current())

    def test_get_endpoint_without_project_id(self):
        # create a fake client such that get_endpoint()
        # doesn't return uuid in url
        endpoint_type = 'v2.1'
        expected_endpoint = 'http://nova-api:8774/v2.1/'
        cs_2_1 = fakes.FakeClient(api_versions.APIVersion("2.0"),
                                  endpoint_type=endpoint_type)

        result = cs_2_1.versions.get_current()
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(result.manager.api.client.endpoint_type,
                         endpoint_type, "Check endpoint_type was set")

        # check that the full request works as expected
        cs_2_1.assert_called('GET', expected_endpoint)

    def test_v2_get_endpoint_without_project_id(self):
        # create a fake client such that get_endpoint()
        #  doesn't return uuid in url
        endpoint_type = 'v2'
        expected_endpoint = 'http://nova-api:8774/v2/'
        cs_2 = fakes.FakeClient(api_versions.APIVersion("2.0"),
                                endpoint_type=endpoint_type)

        result = cs_2.versions.get_current()
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(result.manager.api.client.endpoint_type,
                         endpoint_type, "Check v2 endpoint_type was set")

        # check that the full request works as expected
        cs_2.assert_called('GET', expected_endpoint)

    def test_list_versions(self):
        fapi = mock.Mock()
        version_mgr = versions.VersionManager(fapi)
        version_mgr._list = mock.Mock()
        data = [
            ("https://example.com:777/v2", "https://example.com:777"),
            ("https://example.com/v2", "https://example.com"),
            ("http://example.com/compute/v2", "http://example.com/compute"),
            ("https://example.com/v2/prrrooojeect-uuid",
             "https://example.com"),
            ("https://example.com:777/v2.1", "https://example.com:777"),
            ("https://example.com/v2.1", "https://example.com"),
            ("http://example.com/compute/v2.1", "http://example.com/compute"),
            ("https://example.com/v2.1/prrrooojeect-uuid",
             "https://example.com"),
            ("http://example.com/compute", "http://example.com/compute"),
            ("http://compute.example.com", "http://compute.example.com"),
        ]

        for endpoint, expected in data:
            version_mgr._list.reset_mock()
            fapi.client.get_endpoint.return_value = endpoint
            version_mgr.list()
            version_mgr._list.assert_called_once_with(expected, "versions")

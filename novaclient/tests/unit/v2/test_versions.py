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

import mock

from novaclient import exceptions as exc
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import versions


class VersionsTest(utils.TestCase):
    def setUp(self):
        super(VersionsTest, self).setUp()
        self.cs = fakes.FakeClient()
        self.service_type = versions.Version

    @mock.patch.object(versions.VersionManager, '_is_session_client',
                       return_value=False)
    def test_list_services_with_http_client(self, mock_is_session_client):
        self.cs.versions.list()
        self.cs.assert_called('GET', None)

    @mock.patch.object(versions.VersionManager, '_is_session_client',
                       return_value=True)
    def test_list_services_with_session_client(self, mock_is_session_client):
        self.cs.versions.list()
        self.cs.assert_called('GET', 'http://nova-api:8774/')

    @mock.patch.object(versions.VersionManager, '_is_session_client',
                       return_value=False)
    @mock.patch.object(versions.VersionManager, 'list')
    def test_get_current_with_http_client(self, mock_list,
                                          mock_is_session_client):
        current_version = versions.Version(
            None, {"links": [{"href": "http://nova-api:8774/v2.1"}]},
            loaded=True)

        mock_list.return_value = [
            versions.Version(
                None, {"links": [{"href": "http://url/v1"}]}, loaded=True),
            versions.Version(
                None, {"links": [{"href": "http://url/v2"}]}, loaded=True),
            versions.Version(
                None, {"links": [{"href": "http://url/v3"}]}, loaded=True),
            current_version,
            versions.Version(
                None, {"links": [{"href": "http://url/v21"}]}, loaded=True)]
        self.assertEqual(current_version, self.cs.versions.get_current())

    @mock.patch.object(versions.VersionManager, '_is_session_client',
                       return_value=True)
    def test_get_current_with_session_client(self, mock_is_session_client):
        self.cs.callback = []
        self.cs.versions.get_current()
        self.cs.assert_called('GET', 'http://nova-api:8774/v2.1/')

    @mock.patch.object(versions.VersionManager, '_is_session_client',
                       return_value=True)
    @mock.patch.object(versions.VersionManager, '_get',
                       side_effect=exc.Unauthorized("401 RAX"))
    def test_get_current_with_rax_workaround(self, session, get):
        self.cs.callback = []
        self.assertIsNone(self.cs.versions.get_current())

    @mock.patch.object(versions.VersionManager, '_is_session_client',
                       return_value=False)
    @mock.patch.object(versions.VersionManager, '_list',
                       side_effect=exc.Unauthorized("401 RAX"))
    def test_get_current_with_rax_auth_plugin_workaround(self, session, _list):
        self.cs.callback = []
        self.assertIsNone(self.cs.versions.get_current())

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

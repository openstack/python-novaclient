# Copyright 2013 Rackspace Hosting
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

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import instance_action


class InstanceActionExtensionTests(utils.TestCase):
    def setUp(self):
        super(InstanceActionExtensionTests, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.1"))

    def test_list_instance_actions(self):
        server_uuid = '1234'
        ial = self.cs.instance_action.list(server_uuid)
        self.assert_request_id(ial, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called(
            'GET', '/servers/%s/os-instance-actions' %
            server_uuid)

    def test_get_instance_action(self):
        server_uuid = '1234'
        request_id = 'req-abcde12345'
        ia = self.cs.instance_action.get(server_uuid, request_id)
        self.assert_request_id(ia, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called(
            'GET', '/servers/%s/os-instance-actions/%s'
            % (server_uuid, request_id))


class InstanceActionExtensionV258Tests(InstanceActionExtensionTests):
    def setUp(self):
        super(InstanceActionExtensionV258Tests, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.58")

    def test_list_instance_actions_with_limit_marker_params(self):
        server_uuid = '1234'
        marker = '12140183-c814-4ddf-8453-6df43028aa67'

        ias = self.cs.instance_action.list(
            server_uuid, marker=marker, limit=10,
            changes_since='2016-02-29T06:23:22')
        self.assert_request_id(ias, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called(
            'GET',
            '/servers/%s/os-instance-actions?changes-since=%s&limit=10&'
            'marker=%s' % (server_uuid, '2016-02-29T06%3A23%3A22', marker))
        for ia in ias:
            self.assertIsInstance(ia, instance_action.InstanceAction)


class InstanceActionExtensionV266Tests(InstanceActionExtensionV258Tests):
    def setUp(self):
        super(InstanceActionExtensionV266Tests, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.66")

    def test_list_instance_actions_with_changes_before(self):
        server_uuid = '1234'

        ias = self.cs.instance_action.list(
            server_uuid, marker=None, limit=None, changes_since=None,
            changes_before='2016-02-29T06:23:22')
        self.assert_request_id(ias, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called(
            'GET',
            '/servers/%s/os-instance-actions?changes-before=%s' %
            (server_uuid, '2016-02-29T06%3A23%3A22'))
        for ia in ias:
            self.assertIsInstance(ia, instance_action.InstanceAction)

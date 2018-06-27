# Copyright (c) 2014 VMware, Inc.
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
from novaclient import exceptions
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import server_groups as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import server_groups


class ServerGroupsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.Fixture

    def test_list_server_groups(self):
        result = self.cs.server_groups.list()
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-server-groups')
        self.assertEqual(4, len(result))
        for server_group in result:
            self.assertIsInstance(server_group,
                                  server_groups.ServerGroup)

    def test_list_server_groups_with_all_projects(self):
        result = self.cs.server_groups.list(all_projects=True)
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-server-groups?all_projects=True')
        self.assertEqual(8, len(result))
        for server_group in result:
            self.assertIsInstance(server_group,
                                  server_groups.ServerGroup)

    def test_list_server_groups_with_limit_and_offset(self):
        all_groups = self.cs.server_groups.list()
        result = self.cs.server_groups.list(limit=2, offset=1)
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-server-groups?limit=2&offset=1')
        self.assertEqual(2, len(result))
        for server_group in result:
            self.assertIsInstance(server_group,
                                  server_groups.ServerGroup)
        self.assertEqual(all_groups[1:3], result)

    def test_create_server_group(self):
        kwargs = {'name': 'ig1',
                  'policies': ['anti-affinity']}
        server_group = self.cs.server_groups.create(**kwargs)
        self.assert_request_id(server_group, fakes.FAKE_REQUEST_ID_LIST)
        body = {'server_group': kwargs}
        self.assert_called('POST', '/os-server-groups', body)
        self.assertIsInstance(server_group,
                              server_groups.ServerGroup)

    def test_get_server_group(self):
        id = '2cbd51f4-fafe-4cdb-801b-cf913a6f288b'
        server_group = self.cs.server_groups.get(id)
        self.assert_request_id(server_group, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-server-groups/%s' % id)
        self.assertIsInstance(server_group,
                              server_groups.ServerGroup)

    def test_delete_server_group(self):
        id = '2cbd51f4-fafe-4cdb-801b-cf913a6f288b'
        ret = self.cs.server_groups.delete(id)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/os-server-groups/%s' % id)

    def test_delete_server_group_object(self):
        id = '2cbd51f4-fafe-4cdb-801b-cf913a6f288b'
        server_group = self.cs.server_groups.get(id)
        ret = server_group.delete()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/os-server-groups/%s' % id)

    def test_find_server_groups_by_name(self):
        expected_name = 'ig1'
        kwargs = {self.cs.server_groups.resource_class.NAME_ATTR:
                  expected_name}
        server_group = self.cs.server_groups.find(**kwargs)
        self.assert_request_id(server_group, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-server-groups')
        self.assertIsInstance(server_group, server_groups.ServerGroup)
        actual_name = getattr(server_group,
                              self.cs.server_groups.resource_class.NAME_ATTR)
        self.assertEqual(expected_name, actual_name)

    def test_find_no_existing_server_groups_by_name(self):
        expected_name = 'no-exist'
        kwargs = {self.cs.server_groups.resource_class.NAME_ATTR:
                  expected_name}
        self.assertRaises(exceptions.NotFound,
                          self.cs.server_groups.find,
                          **kwargs)
        self.assert_called('GET', '/os-server-groups')


class ServerGroupsTestV264(ServerGroupsTest):
    def setUp(self):
        super(ServerGroupsTestV264, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.64")

    def test_create_server_group(self):
        name = 'ig1'
        policy = 'anti-affinity'
        server_group = self.cs.server_groups.create(name, policy)
        self.assert_request_id(server_group, fakes.FAKE_REQUEST_ID_LIST)
        body = {'server_group': {'name': name, 'policy': policy}}
        self.assert_called('POST', '/os-server-groups', body)
        self.assertIsInstance(server_group,
                              server_groups.ServerGroup)

    def test_create_server_group_with_rules(self):
        kwargs = {'name': 'ig1',
                  'policy': 'anti-affinity',
                  'rules': {'max_server_per_host': 3}}
        server_group = self.cs.server_groups.create(**kwargs)
        self.assert_request_id(server_group, fakes.FAKE_REQUEST_ID_LIST)
        body = {
            'server_group': {
                'name': 'ig1',
                'policy': 'anti-affinity',
                'rules': {'max_server_per_host': 3}
            }
        }
        self.assert_called('POST', '/os-server-groups', body)
        self.assertIsInstance(server_group,
                              server_groups.ServerGroup)

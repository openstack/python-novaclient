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

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import migrations


class MigrationsTest(utils.TestCase):
    def setUp(self):
        super(MigrationsTest, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.1"))

    def test_list_migrations(self):
        ml = self.cs.migrations.list()
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-migrations')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
            self.assertRaises(AttributeError, getattr, m, "migration_type")

    def test_list_migrations_v223(self):
        cs = fakes.FakeClient(api_versions.APIVersion("2.23"))
        ml = cs.migrations.list()
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        cs.assert_called('GET', '/os-migrations')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
            self.assertEqual(m.migration_type, 'live-migration')

    @mock.patch('novaclient.v2.migrations.warnings.warn')
    def test_list_migrations_with_cell_name(self, mock_warn):
        ml = self.cs.migrations.list(cell_name="abc")
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-migrations?cell_name=abc')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
        self.assertTrue(mock_warn.called)

    def test_list_migrations_with_filters(self):
        ml = self.cs.migrations.list('host1', 'finished', 'child1')
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)

        self.cs.assert_called(
            'GET',
            '/os-migrations?cell_name=child1&host=host1&status=finished')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)

    def test_list_migrations_with_instance_uuid_filter(self):
        ml = self.cs.migrations.list('host1', 'finished', 'child1',
                                     'instance_id_456')
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)

        self.cs.assert_called(
            'GET',
            ('/os-migrations?cell_name=child1&host=host1&'
             'instance_uuid=instance_id_456&status=finished'))
        self.assertEqual(1, len(ml))
        self.assertEqual('instance_id_456', ml[0].instance_uuid)

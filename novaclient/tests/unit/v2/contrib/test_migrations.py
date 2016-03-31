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
from novaclient import extension
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2.contrib import migrations


class MigrationsTest(utils.TestCase):
    def setUp(self):
        super(MigrationsTest, self).setUp()
        self.extensions = [
            extension.Extension(migrations.__name__.split(".")[-1],
                                migrations),
        ]
        self.cs = fakes.FakeClient(extensions=self.extensions)

    def test_list_migrations(self):
        ml = self.cs.migrations.list()
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-migrations')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
            self.assertRaises(AttributeError, getattr, m, "migration_type")

    def test_list_migrations_v223(self):
        cs = fakes.FakeClient(extensions=self.extensions,
                              api_version=api_versions.APIVersion("2.23"))
        ml = cs.migrations.list()
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        cs.assert_called('GET', '/os-migrations')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
            self.assertEqual(m.migration_type, 'live-migration')

    def test_list_migrations_with_filters(self):
        ml = self.cs.migrations.list('host1', 'finished', 'child1')
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)

        self.cs.assert_called(
            'GET',
            '/os-migrations?cell_name=child1&host=host1&status=finished')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)

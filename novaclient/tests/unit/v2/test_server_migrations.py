# Copyright 2016 OpenStack Foundation
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
from novaclient import base
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import server_migrations as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import server_migrations


class ServerMigrationsTest(utils.FixturedTestCase):
    client_fixture_class = client.V1
    data_fixture_class = data.Fixture

    def setUp(self):
        super(ServerMigrationsTest, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.22")

    def test_live_migration_force_complete(self):
        body = {'force_complete': None}
        self.cs.server_migrations.live_migrate_force_complete(1234, 1)
        self.assert_called('POST', '/servers/1234/migrations/1/action', body)


class ServerMigrationsTestV223(ServerMigrationsTest):

    migration = {
        "created_at": "2016-01-29T13:42:02.000000",
        "dest_compute": "compute2",
        "dest_host": "1.2.3.4",
        "dest_node": "node2",
        "id": 1,
        "server_uuid": "4cfba335-03d8-49b2-8c52-e69043d1e8fe",
        "source_compute": "compute1",
        "source_node": "node1",
        "status": "running",
        "memory_total_bytes": 123456,
        "memory_processed_bytes": 12345,
        "memory_remaining_bytes": 120000,
        "disk_total_bytes": 234567,
        "disk_processed_bytes": 23456,
        "disk_remaining_bytes": 230000,
        "updated_at": "2016-01-29T13:42:02.000000"
    }

    def setUp(self):
        super(ServerMigrationsTestV223, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.23")

    def test_list_migrations(self):
        ml = self.cs.server_migrations.list(1234)

        self.assertIsInstance(ml, base.ListWithMeta)
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        for k in self.migration:
            self.assertEqual(self.migration[k], getattr(ml[0], k))

        self.assert_called('GET', '/servers/1234/migrations')

    def test_get_migration(self):
        migration = self.cs.server_migrations.get(1234, 1)

        self.assertIsInstance(migration, server_migrations.ServerMigration)
        for k in migration._info:
            self.assertEqual(self.migration[k], migration._info[k])
        self.assert_request_id(migration, fakes.FAKE_REQUEST_ID_LIST)

        self.assert_called('GET', '/servers/1234/migrations/1')


class ServerMigrationsTestV224(ServerMigrationsTest):
    def setUp(self):
        super(ServerMigrationsTestV224, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.24")

    def test_live_migration_abort(self):
        self.cs.server_migrations.live_migration_abort(1234, 1)
        self.assert_called('DELETE', '/servers/1234/migrations/1')

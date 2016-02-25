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
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import server_migrations as data
from novaclient.tests.unit import utils


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

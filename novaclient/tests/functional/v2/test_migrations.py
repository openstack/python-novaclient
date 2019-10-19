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

from oslo_utils import uuidutils

from novaclient.tests.functional import base


class TestMigrationList(base.ClientTestBase):
    """Tests the "nova migration-list" command."""

    def _filter_migrations(
            self, version, migration_type, source_compute):
        """
        Filters migrations by --migration-type and --source-compute.

        :param version: The --os-compute-api-version to use.
        :param migration_type: The type of migrations to filter.
        :param source_compute: The source compute service hostname to filter.
        :return: output of the nova migration-list command with filters applied
        """
        return self.nova('migration-list',
                         flags='--os-compute-api-version %s' % version,
                         params='--migration-type %s --source-compute %s' % (
                             migration_type, source_compute))

    def test_migration_list(self):
        """Tests creating a server, resizing it and then listing and filtering
        migrations using various microversion milestones.
        """
        server_id = self._create_server(flavor=self.flavor.id).id
        # Find the source compute by getting OS-EXT-SRV-ATTR:host from the
        # nova show output.
        server = self.nova('show', params='%s' % server_id)
        server_user_id = self._get_value_from_the_table(server, 'user_id')
        tenant_id = self._get_value_from_the_table(server, 'tenant_id')
        source_compute = self._get_value_from_the_table(
            server, 'OS-EXT-SRV-ATTR:host')
        # now resize up
        alternate_flavor = self._pick_alternate_flavor()
        self.nova('resize',
                  params='%s %s --poll' % (server_id, alternate_flavor))
        # now confirm the resize
        self.nova('resize-confirm', params='%s' % server_id)
        # wait for the server to be active and then check the migration list
        self._wait_for_state_change(server_id, 'active')
        # First, list migrations with v2.1 and our server id should be in the
        # output. There should only be the one migration.
        migrations = self.nova('migration-list',
                               flags='--os-compute-api-version 2.1')
        instance_uuid = self._get_column_value_from_single_row_table(
            migrations, 'Instance UUID')
        self.assertEqual(server_id, instance_uuid)
        # A successfully confirmed resize should have the migration status
        # of "confirmed".
        migration_status = self._get_column_value_from_single_row_table(
            migrations, 'Status')
        self.assertEqual('confirmed', migration_status)
        # Now listing migrations with 2.23 should give us the Type column which
        # should have a value of "resize".
        migrations = self.nova('migration-list',
                               flags='--os-compute-api-version 2.23')
        migration_type = self._get_column_value_from_single_row_table(
            migrations, 'Type')
        self.assertEqual('resize', migration_type)
        # Filter migrations with v2.1.
        migrations = self._filter_migrations('2.1', 'resize', source_compute)
        # Make sure we got something back.
        src_compute = self._get_column_value_from_single_row_table(
            migrations, 'Source Compute')
        self.assertEqual(source_compute, src_compute)
        # Filter migrations with v2.59 and make sure there is a migration UUID
        # value in the output.
        migrations = self._filter_migrations('2.59', 'resize', source_compute)
        # _get_column_value_from_single_row_table will raise ValueError if a
        # value is not found for the given column. We don't actually care what
        # the migration UUID value is just that the filter works and the UUID
        # is shown.
        self._get_column_value_from_single_row_table(migrations, 'UUID')
        # Filter migrations with v2.66, same as 2.59.
        migrations = self._filter_migrations('2.66', 'resize', source_compute)
        self._get_column_value_from_single_row_table(migrations, 'UUID')
        # Now do a negative test to show that filtering on a migration type
        # that we don't have a migration for will not return anything.
        migrations = self._filter_migrations(
            '2.1', 'evacuation', source_compute)
        self.assertNotIn(server_id, migrations)
        # Similarly, make sure we don't get anything back when filtering on
        # a --source-compute that doesn't exist.
        migrations = self._filter_migrations(
            '2.66', 'resize', uuidutils.generate_uuid())
        self.assertNotIn(server_id, migrations)

        # Listing migrations with v2.80 and make sure there are the User ID
        # and Project ID values in the output.
        migrations = self.nova('migration-list',
                               flags='--os-compute-api-version 2.80')
        user_id = self._get_column_value_from_single_row_table(
            migrations, 'User ID')
        self.assertEqual(server_user_id, user_id)
        project_id = self._get_column_value_from_single_row_table(
            migrations, 'Project ID')
        self.assertEqual(tenant_id, project_id)

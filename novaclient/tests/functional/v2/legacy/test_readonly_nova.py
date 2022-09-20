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

from tempest.lib import decorators
from tempest.lib import exceptions

from novaclient.tests.functional import base


class SimpleReadOnlyNovaClientTest(base.ClientTestBase):

    """Read only functional python-novaclient tests.

    This only exercises client commands that are read only.
    """

    COMPUTE_API_VERSION = "2.1"

    def test_admin_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'this-does-nova-exist')

    # NOTE(jogo): Commands in order listed in 'nova help'

    def test_admin_aggregate_list(self):
        self.nova('aggregate-list')

    def test_admin_availability_zone_list(self):
        self.assertIn("internal", self.nova('availability-zone-list'))

    def test_admin_flavor_access_list(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'flavor-access-list')
        # Failed to get access list for public flavor type
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'flavor-access-list',
                          params='--flavor m1.tiny')

    def test_admin_flavor_list(self):
        self.assertIn("Memory_MiB", self.nova('flavor-list'))

    def test_admin_hypervisor_list(self):
        self.nova('hypervisor-list')

    @decorators.skip_because(bug="1157349")
    def test_admin_interface_list(self):
        self.nova('interface-list')

    def test_admin_keypair_list(self):
        self.nova('keypair-list')

    def test_admin_list(self):
        self.nova('list')
        self.nova('list', params='--all-tenants 1')
        self.nova('list', params='--all-tenants 0')
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'list',
                          params='--all-tenants bad')

    def test_admin_server_group_list(self):
        self.nova('server-group-list')

    def test_admin_service_list(self):
        self.nova('service-list')

    def test_admin_usage(self):
        self.nova('usage')

    def test_admin_usage_list(self):
        self.nova('usage-list')

    def test_admin_help(self):
        self.nova('help')

    def test_agent_list(self):
        ex = self.assertRaises(exceptions.CommandFailed,
                               self.nova, 'agent-list')
        self.assertIn(
            "This resource is no longer available. "
            "No forwarding address is given. (HTTP 410)", str(ex))
        self.assertIn(
            "This command has been deprecated since 23.0.0 Wallaby Release "
            "and will be removed in the first major release "
            "after the Nova server 24.0.0 X release.", str(ex.stderr))
        ex = self.assertRaises(exceptions.CommandFailed,
                               self.nova, 'agent-list', flags='--debug')
        self.assertIn(
            "This resource is no longer available. "
            "No forwarding address is given. (HTTP 410)", str(ex))
        self.assertIn(
            "This command has been deprecated since 23.0.0 Wallaby Release "
            "and will be removed in the first major release "
            "after the Nova server 24.0.0 X release.", str(ex.stderr))

    def test_migration_list(self):
        self.nova('migration-list')
        self.nova('migration-list', flags='--debug')

    def test_version_list(self):
        self.nova('version-list', flags='--debug')

    def test_quota_defaults(self):
        self.nova('quota-defaults')
        self.nova('quota-defaults', flags='--debug')

    def test_bash_completion(self):
        self.nova('bash-completion')

    # Optional arguments:

    def test_admin_version(self):
        self.nova('', flags='--version')

    def test_admin_debug_list(self):
        self.nova('list', flags='--debug')

    def test_admin_timeout(self):
        self.nova('list', flags='--timeout %d' % 60)

    def test_admin_timing(self):
        self.nova('list', flags='--timing')

    def test_admin_invalid_bypass_url(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'list',
                          flags='--os-endpoint-override badurl')

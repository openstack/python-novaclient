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

import time

from tempest.lib import decorators

from novaclient.tests.functional import base
from novaclient.v2 import shell


@decorators.skip_because(bug="1675526")
class TestTriggerCrashDumpNovaClientV217(base.TenantTestBase):
    """Functional tests for trigger crash dump"""

    COMPUTE_API_VERSION = "2.17"

    # It's a resource-consuming task to implement full-flow (up to getting
    # and reading a dump file) functional test for trigger-crash-dump.
    # We need to upload Ubuntu image for booting an instance based on it,
    # and to install kdump with its further configuring on this instance.
    # Here, the "light" version of functional test is proposed.
    # It's based on knowledge that trigger-crash-dump uses a NMI injection,
    # and when the 'trigger-crash-dump' operation is executed,
    # instance's kernel receives the NMI signal, and an appropriate
    # message will appear in the instance's log.

    # The server status must be ACTIVE, PAUSED, RESCUED, RESIZED or ERROR.
    # If not, the conflictingRequest(409) code is returned

    def _assert_nmi(self, server_id, timeout=60, poll_interval=1):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if 'trigger_crash_dump' in self.nova('instance-action-list %s ' %
                                                 server_id):
                break
            time.sleep(poll_interval)
        else:
            self.fail("Trigger crash dump hasn't been executed for server %s"
                      % server_id)

    def test_trigger_crash_dump_in_active_state(self):
        server = self._create_server()
        self.wait_for_server_os_boot(server.id)
        self.nova('trigger-crash-dump %s ' % server.id)
        self._assert_nmi(server.id)

    def test_trigger_crash_dump_in_error_state(self):
        server = self._create_server()
        self.wait_for_server_os_boot(server.id)
        self.nova('reset-state %s ' % server.id)
        shell._poll_for_status(
            self.client.servers.get, server.id,
            'active', ['error'])
        self.nova('trigger-crash-dump %s ' % server.id)
        self._assert_nmi(server.id)

    def test_trigger_crash_dump_in_paused_state(self):
        server = self._create_server()
        self.wait_for_server_os_boot(server.id)
        self.nova('pause %s ' % server.id)
        shell._poll_for_status(
            self.client.servers.get, server.id,
            'active', ['paused'])
        self.nova('trigger-crash-dump %s ' % server.id)
        self._assert_nmi(server.id)

    def test_trigger_crash_dump_in_rescued_state(self):
        server = self._create_server()
        self.wait_for_server_os_boot(server.id)
        self.nova('rescue %s ' % server.id)
        shell._poll_for_status(
            self.client.servers.get, server.id,
            'active', ['rescue'])
        self.wait_for_server_os_boot(server.id)
        self.nova('trigger-crash-dump %s ' % server.id)
        self._assert_nmi(server.id)

    def test_trigger_crash_dump_in_resized_state(self):
        server = self._create_server()
        self.wait_for_server_os_boot(server.id)
        self.nova('resize %s %s' % (server.id, 'm1.small'))
        shell._poll_for_status(
            self.client.servers.get, server.id,
            'active', ['verify_resize'])
        self.nova('trigger-crash-dump %s ' % server.id)
        self._assert_nmi(server.id)

    def test_trigger_crash_dump_in_shutoff_state(self):
        server = self._create_server()
        self.wait_for_server_os_boot(server.id)
        self.nova('stop %s ' % server.id)
        shell._poll_for_status(
            self.client.servers.get, server.id,
            'active', ['shutoff'])
        output = self.nova('trigger-crash-dump %s ' %
                           server.id, fail_ok=True, merge_stderr=True)
        self.assertIn("ERROR (Conflict): "
                      "Cannot 'trigger_crash_dump' instance %s "
                      "while it is in vm_state stopped (HTTP 409) " %
                      server.id, output)

    # If the specified server is locked, the conflictingRequest(409) code
    # is returned to a user without administrator privileges.
    def test_trigger_crash_dump_in_locked_state_admin(self):
        server = self._create_server()
        self.wait_for_server_os_boot(server.id)
        self.nova('lock %s ' % server.id)
        self.nova('trigger-crash-dump %s ' % server.id)
        self._assert_nmi(server.id)

    def test_trigger_crash_dump_in_locked_state_nonadmin(self):
        name = self.name_generate(prefix='server')
        server = self.another_nova('boot --flavor %s --image %s --poll %s' %
                                   (self.flavor.name, self.image.name, name))
        self.addCleanup(self.another_nova, 'delete', params=name)
        server_id = self._get_value_from_the_table(
            server, 'id')
        self.wait_for_server_os_boot(server_id)
        self.another_nova('lock %s ' % server_id)
        self.addCleanup(self.another_nova, 'unlock', params=name)
        output = self.another_nova('trigger-crash-dump %s ' %
                                   server_id, fail_ok=True, merge_stderr=True)
        # NOTE(mriedem): Depending on the version of the server you can get
        # different error messages back from this, so just assert that it's a
        # 409 either way.
        self.assertIn("ERROR (Conflict)", output)

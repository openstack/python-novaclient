# Copyright 2015 IBM Corp.
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

from tempest.lib import exceptions

from novaclient.tests.functional import base


class TestConsolesNovaClient(base.ClientTestBase):
    """Consoles functional tests."""

    COMPUTE_API_VERSION = "2.1"

    def _test_console_get(self, command, expected_response_type):
        server = self._create_server()
        completed_command = command % server.id

        try:
            output = self.nova(completed_command)
            # if we didn't fail, check that the expected response type is in
            # the output
            console_type = self._get_column_value_from_single_row_table(
                output, 'Type')
            self.assertEqual(expected_response_type, console_type, output)
        except exceptions.CommandFailed as cf:
            self.assertIn('HTTP 400', str(cf.stderr))

    def _test_vnc_console_get(self):
        self._test_console_get('get-vnc-console %s novnc', 'novnc')

    def _test_spice_console_get(self):
        self._test_console_get('get-spice-console %s spice-html5',
                               'spice-html5')

    def _test_rdp_console_get(self):
        self._test_console_get('get-rdp-console %s rdp-html5', 'rdp-html5')

    def _test_serial_console_get(self):
        self._test_console_get('get-serial-console %s', 'serial')

    def test_vnc_console_get(self):
        self._test_vnc_console_get()

    def test_spice_console_get(self):
        self._test_spice_console_get()

    def test_rdp_console_get(self):
        self._test_rdp_console_get()

    def test_serial_console_get(self):
        self._test_serial_console_get()

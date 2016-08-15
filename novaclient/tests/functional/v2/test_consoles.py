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

from novaclient.tests.functional.v2.legacy import test_consoles


class TestConsolesNovaClientV26(test_consoles.TestConsolesNovaClient):
    """Consoles functional tests for >=v2.6 api microversions."""

    COMPUTE_API_VERSION = "2.6"

    def test_vnc_console_get(self):
        self._test_vnc_console_get()

    def test_spice_console_get(self):
        self._test_spice_console_get()

    def test_rdp_console_get(self):
        self._test_rdp_console_get()

    def test_serial_console_get(self):
        self._test_serial_console_get()


class TestConsolesNovaClientV28(test_consoles.TestConsolesNovaClient):
    """Consoles functional tests for >=v2.8 api microversions."""

    COMPUTE_API_VERSION = "2.8"

    def test_webmks_console_get(self):
        self._test_console_get('get-mks-console %s ', 'webmks')

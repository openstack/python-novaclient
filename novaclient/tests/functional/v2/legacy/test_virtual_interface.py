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

from novaclient.tests.functional import base
from novaclient.v2 import shell


class TestVirtualInterfacesNovaClient(base.ClientTestBase):
    """Virtual Interfaces functional tests."""

    COMPUTE_API_VERSION = "2.1"

    def _create_server(self):
        name = self.name_generate(prefix='server')
        network = self.client.networks.list()[0]
        server = self.client.servers.create(
            name, self.image, self.flavor, nics=[{"net-id": network.id}])
        shell._poll_for_status(
            self.client.servers.get, server.id,
            'building', ['active'])
        self.addCleanup(server.delete)
        return server

    def test_virtual_interface_list(self):
        server = self._create_server()
        output = self.nova('virtual-interface-list %s' % server.id)
        self.assertTrue(len(output.split("\n")) > 5,
                        "Output table of `virtual-interface-list` for the test"
                        " server should not be empty.")
        return output

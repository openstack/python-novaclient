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

from novaclient.tests.functional.v2.legacy import test_virtual_interface


class TestVirtualInterfacesNovaClient(
        test_virtual_interface.TestVirtualInterfacesNovaClient):
    """Virtual Interfaces functional tests."""

    COMPUTE_API_VERSION = "2.latest"

    def test_virtual_interface_list(self):
        output = super(TestVirtualInterfacesNovaClient,
                       self).test_virtual_interface_list()
        network = self.client.networks.list()[0]
        self.assertEqual(network.id,
                         self._get_column_value_from_single_row_table(
                             output, "Network ID"))

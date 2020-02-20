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

from oslo_serialization import jsonutils

from novaclient.tests.functional.v2.legacy import test_extended_attributes


class TestExtAttrNovaClientV23(test_extended_attributes.TestExtAttrNovaClient):
    """Functional tests for os-extended-server-attributes, microversion 2.3"""

    COMPUTE_API_VERSION = "2.3"

    def test_extended_server_attributes(self):
        server, volume = self._create_server_and_attach_volume()
        table = self.nova('show %s' % server.id)
        # Check that attributes listed below exist in 'nova show' table and
        # they are exactly Property attributes (not an instance's name, e.g.)
        # The _get_value_from_the_table() will raise an exception
        # if attr is not a key of the table dict (first column)
        for attr in ['OS-EXT-SRV-ATTR:reservation_id',
                     'OS-EXT-SRV-ATTR:launch_index',
                     'OS-EXT-SRV-ATTR:ramdisk_id',
                     'OS-EXT-SRV-ATTR:kernel_id',
                     'OS-EXT-SRV-ATTR:hostname',
                     'OS-EXT-SRV-ATTR:root_device_name']:
            self._get_value_from_the_table(table, attr)
        # Check that attribute given below also exists in 'nova show' table
        # as a key (first column) of table dict
        volume_attr = self._get_value_from_the_table(
            table, 'os-extended-volumes:volumes_attached')
        # Check that 'delete_on_termination' exists as a key
        # of volume_attr dict
        self.assertIn('delete_on_termination', jsonutils.loads(volume_attr)[0])

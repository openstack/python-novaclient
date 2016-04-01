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

import json

from novaclient.tests.functional import base


class TestExtAttrNovaClient(base.ClientTestBase):
    """Functional tests for os-extended-server-attributes"""

    COMPUTE_API_VERSION = "2.1"

    def _create_server_and_attach_volume(self):
        server = self._create_server()
        volume = self.cinder.volumes.create(1)
        self.addCleanup(volume.delete)
        self.wait_for_volume_status(volume, 'available')
        self.nova('volume-attach', params="%s %s" % (server.name, volume.id))
        self.addCleanup(self._release_volume, server, volume)
        self.wait_for_volume_status(volume, 'in-use')
        return server, volume

    def _release_volume(self, server, volume):
        self.nova('volume-detach', params="%s %s" % (server.id, volume.id))
        self.wait_for_volume_status(volume, 'available')

    def test_extended_server_attributes(self):
        server, volume = self._create_server_and_attach_volume()
        table = self.nova('show %s' % server.id)
        # Check that attributes listed below exist in 'nova show' table and
        # they are exactly Property attributes (not an instance's name, e.g.)
        # The _get_value_from_the_table() will raise an exception
        # if attr is not a key (first column) of the table dict
        for attr in ['OS-EXT-SRV-ATTR:host',
                     'OS-EXT-SRV-ATTR:hypervisor_hostname',
                     'OS-EXT-SRV-ATTR:instance_name']:
            self._get_value_from_the_table(table, attr)
        # Check that attribute given below also exists in 'nova show' table
        # as a key (first column) of table dict
        volume_attr = self._get_value_from_the_table(
            table, 'os-extended-volumes:volumes_attached')
        # Check that 'id' exists as a key of volume_attr dict
        self.assertIn('id', json.loads(volume_attr)[0])

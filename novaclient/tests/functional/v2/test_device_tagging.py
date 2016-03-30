# Copyright (C) 2016, Red Hat, Inc.
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

import uuid

from novaclient.tests.functional import base


class TestDeviceTaggingCLI(base.ClientTestBase):

    COMPUTE_API_VERSION = "2.32"

    def test_boot_server_with_tagged_devices(self):
        server_info = self.nova('boot', params=(
            '%(name)s --flavor %(flavor)s --poll '
            '--nic net-id=%(net-uuid)s,tag=foo '
            '--block-device '
            'source=image,dest=volume,id=%(image)s,size=1,'
            'bootindex=0,tag=bar' % {'name': str(uuid.uuid4()),
                                     'flavor': self.flavor.id,
                                     'net-uuid': self.network.id,
                                     'image': self.image.id}))
        server_id = self._get_value_from_the_table(server_info, 'id')
        self.client.servers.delete(server_id)
        self.wait_for_resource_delete(server_id, self.client.servers)

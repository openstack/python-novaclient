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

from tempest.lib import exceptions

from novaclient.tests.functional import base


class TestBlockDeviceTaggingCLIError(base.ClientTestBase):
    """Negative test that asserts that creating a server with a tagged
    block device with a specific microversion will fail.
    """

    COMPUTE_API_VERSION = "2.31"

    def test_boot_server_with_tagged_block_devices_with_error(self):
        try:
            output = self.nova('boot', params=(
                '%(name)s --flavor %(flavor)s --poll '
                '--nic net-id=%(net-uuid)s '
                '--block-device '
                'source=image,dest=volume,id=%(image)s,size=1,bootindex=0,'
                'shutdown=remove,tag=bar' % {'name': self.name_generate(),
                                             'flavor': self.flavor.id,
                                             'net-uuid': self.network.id,
                                             'image': self.image.id}))
        except exceptions.CommandFailed as e:
            self.assertIn("ERROR (CommandError): "
                          "'tag' in block device mapping is not supported "
                          "in API version %s." % self.COMPUTE_API_VERSION,
                          str(e))
        else:
            server_id = self._get_value_from_the_table(output, 'id')
            self.client.servers.delete(server_id)
            self.wait_for_resource_delete(server_id, self.client.servers)
            self.fail("Booting a server with block device tag is not failed.")


class TestNICDeviceTaggingCLIError(base.ClientTestBase):
    """Negative test that asserts that creating a server with a tagged
    nic with a specific microversion will fail.
    """

    COMPUTE_API_VERSION = "2.31"

    def test_boot_server_with_tagged_nic_devices_with_error(self):
        try:
            output = self.nova('boot', params=(
                '%(name)s --flavor %(flavor)s --poll '
                '--nic net-id=%(net-uuid)s,tag=foo '
                '--block-device '
                'source=image,dest=volume,id=%(image)s,size=1,bootindex=0,'
                'shutdown=remove' % {'name': self.name_generate(),
                                     'flavor': self.flavor.id,
                                     'net-uuid': self.network.id,
                                     'image': self.image.id}))
        except exceptions.CommandFailed as e:
            self.assertIn('Invalid nic argument', str(e))
        else:
            server_id = self._get_value_from_the_table(output, 'id')
            self.client.servers.delete(server_id)
            self.wait_for_resource_delete(server_id, self.client.servers)
            self.fail("Booting a server with network interface tag "
                      "is not failed.")


class TestBlockDeviceTaggingCLI(base.ClientTestBase):
    """Tests that creating a server with a tagged block device will work
    with the 2.32 microversion, where the feature was originally added.
    """

    COMPUTE_API_VERSION = "2.32"

    def test_boot_server_with_tagged_block_devices(self):
        server_info = self.nova('boot', params=(
            '%(name)s --flavor %(flavor)s --poll '
            '--nic net-id=%(net-uuid)s '
            '--block-device '
            'source=image,dest=volume,id=%(image)s,size=1,bootindex=0,'
            'shutdown=remove,tag=bar' % {'name': self.name_generate(),
                                         'flavor': self.flavor.id,
                                         'net-uuid': self.network.id,
                                         'image': self.image.id}))
        server_id = self._get_value_from_the_table(server_info, 'id')
        self.client.servers.delete(server_id)
        self.wait_for_resource_delete(server_id, self.client.servers)


class TestNICDeviceTaggingCLI(base.ClientTestBase):
    """Tests that creating a server with a tagged nic will work
    with the 2.32 microversion, where the feature was originally added.
    """

    COMPUTE_API_VERSION = "2.32"

    def test_boot_server_with_tagged_nic_devices(self):
        server_info = self.nova('boot', params=(
            '%(name)s --flavor %(flavor)s --poll '
            '--nic net-id=%(net-uuid)s,tag=foo '
            '--block-device '
            'source=image,dest=volume,id=%(image)s,size=1,bootindex=0,'
            'shutdown=remove' % {'name': self.name_generate(),
                                 'flavor': self.flavor.id,
                                 'net-uuid': self.network.id,
                                 'image': self.image.id}))
        server_id = self._get_value_from_the_table(server_info, 'id')
        self.client.servers.delete(server_id)
        self.wait_for_resource_delete(server_id, self.client.servers)


class TestDeviceTaggingCLIV233(TestBlockDeviceTaggingCLIError,
                               TestNICDeviceTaggingCLI):
    """Tests that in microversion 2.33, creating a server with a tagged
    block device will fail, but creating a server with a tagged nic will
    succeed.
    """

    COMPUTE_API_VERSION = "2.33"


class TestDeviceTaggingCLIV236(TestBlockDeviceTaggingCLIError,
                               TestNICDeviceTaggingCLI):
    """Tests that in microversion 2.36, creating a server with a tagged
    block device will fail, but creating a server with a tagged nic will
    succeed. This is testing the boundary before 2.37 where nic tagging
    was broken.
    """

    COMPUTE_API_VERSION = "2.36"


class TestDeviceTaggingCLIV237(TestBlockDeviceTaggingCLIError,
                               TestNICDeviceTaggingCLIError):
    """Tests that in microversion 2.37, creating a server with either a
    tagged block device or tagged nic would fail.
    """

    COMPUTE_API_VERSION = "2.37"


class TestDeviceTaggingCLIV241(TestBlockDeviceTaggingCLIError,
                               TestNICDeviceTaggingCLIError):
    """Tests that in microversion 2.41, creating a server with either a
    tagged block device or tagged nic would fail. This is testing the
    boundary before 2.42 where block device tags and nic tags were fixed
    for server create requests.
    """

    COMPUTE_API_VERSION = "2.41"


class TestDeviceTaggingCLIV242(TestBlockDeviceTaggingCLI,
                               TestNICDeviceTaggingCLI):
    """Tests that in microversion 2.42 you could once again create a server
    with a tagged block device or a tagged nic.
    """

    COMPUTE_API_VERSION = "2.42"

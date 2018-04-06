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

import datetime

from oslo_utils import timeutils

from novaclient.tests.functional import base


class TestServersBootNovaClient(base.ClientTestBase):
    """Servers boot functional tests."""

    COMPUTE_API_VERSION = "2.1"

    def _boot_server_with_legacy_bdm(self, bdm_params=()):
        volume_size = 1
        volume_name = self.name_generate()
        volume = self.cinder.volumes.create(size=volume_size,
                                            name=volume_name,
                                            imageRef=self.image.id)
        self.wait_for_volume_status(volume, "available")

        if (len(bdm_params) >= 3 and bdm_params[2] == '1'):
            delete_volume = False
        else:
            delete_volume = True

        bdm_params = ':'.join(bdm_params)
        if bdm_params:
            bdm_params = ''.join((':', bdm_params))

        params = (
            "%(name)s --flavor %(flavor)s --poll "
            "--block-device-mapping vda=%(volume_id)s%(bdm_params)s" % {
                "name": self.name_generate(), "flavor":
                    self.flavor.id,
                "volume_id": volume.id,
                "bdm_params": bdm_params})
        # check to see if we have to pass in a network id
        if self.multiple_networks:
            params += ' --nic net-id=%s' % self.network.id
        server_info = self.nova("boot", params=params)
        server_id = self._get_value_from_the_table(server_info, "id")

        self.client.servers.delete(server_id)
        self.wait_for_resource_delete(server_id, self.client.servers)

        if delete_volume:
            self.cinder.volumes.delete(volume.id)
            self.wait_for_resource_delete(volume.id, self.cinder.volumes)

    def test_boot_server_with_legacy_bdm(self):
        # bdm v1 format
        # <id>:<type>:<size(GiB)>:<delete-on-terminate>
        # params = (type, size, delete-on-terminate)
        params = ('', '', '1')
        self._boot_server_with_legacy_bdm(bdm_params=params)

    def test_boot_server_with_legacy_bdm_volume_id_only(self):
        self._boot_server_with_legacy_bdm()

    def test_boot_server_with_net_name(self):
        server_info = self.nova("boot", params=(
            "%(name)s --flavor %(flavor)s --image %(image)s --poll "
            "--nic net-name=%(net-name)s" % {"name": self.name_generate(),
                                             "image": self.image.id,
                                             "flavor": self.flavor.id,
                                             "net-name": self.network.name}))
        server_id = self._get_value_from_the_table(server_info, "id")

        self.client.servers.delete(server_id)
        self.wait_for_resource_delete(server_id, self.client.servers)

    def test_boot_server_using_image_with(self):
        """Scenario test which does the following:

        1. Create a server.
        2. Create a snapshot image of the server with a special meta key.
        3. Create a second server using the --image-with option using the meta
           key stored in the snapshot image created in step 2.
        """
        # create the first server and wait for it to be active
        server_info = self.nova('boot', params=(
            '--flavor %(flavor)s --image %(image)s --poll '
            'image-with-server-1' % {'image': self.image.id,
                                     'flavor': self.flavor.id}))
        server_id = self._get_value_from_the_table(server_info, 'id')
        self.addCleanup(self._cleanup_server, server_id)

        # create a snapshot of the server with an image metadata key
        snapshot_info = self.nova('image-create', params=(
            '--metadata image_with_meta=%(meta_value)s '
            '--show --poll %(server_id)s image-with-snapshot' % {
                'meta_value': server_id,
                'server_id': server_id}))

        # get the snapshot image id out of the output table for the second
        # server create request
        snapshot_id = self._get_value_from_the_table(snapshot_info, 'id')
        self.addCleanup(self.glance.images.delete, snapshot_id)

        # verify the metadata was set on the snapshot image
        meta_value = self._get_value_from_the_table(
            snapshot_info, 'image_with_meta')
        self.assertEqual(server_id, meta_value)

        # create the second server using --image-with
        server_info = self.nova('boot', params=(
            '--flavor %(flavor)s --image-with image_with_meta=%(meta_value)s '
            '--poll image-with-server-2' % {'meta_value': server_id,
                                            'flavor': self.flavor.id}))
        server_id = self._get_value_from_the_table(server_info, 'id')
        self.addCleanup(self._cleanup_server, server_id)


class TestServersListNovaClient(base.ClientTestBase):
    """Servers list functional tests."""

    COMPUTE_API_VERSION = "2.1"

    def _create_servers(self, name, number):
        return [self._create_server(name) for i in range(number)]

    def test_list_with_limit(self):
        name = self.name_generate()
        self._create_servers(name, 2)
        output = self.nova("list", params="--limit 1 --name %s" % name)
        # Cut header and footer of the table
        servers = output.split("\n")[3:-2]
        self.assertEqual(1, len(servers), output)

    def test_list_with_changes_since(self):
        now = datetime.datetime.isoformat(timeutils.utcnow())
        name = self.name_generate()
        self._create_servers(name, 1)
        output = self.nova("list", params="--changes-since %s" % now)
        self.assertIn(name, output, output)
        now = datetime.datetime.isoformat(timeutils.utcnow())
        output = self.nova("list", params="--changes-since %s" % now)
        self.assertNotIn(name, output, output)

    def test_list_all_servers(self):
        name = self.name_generate()
        precreated_servers = self._create_servers(name, 3)
        # there are no possibility to exceed the limit on API side, so just
        # check that "-1" limit processes by novaclient side
        output = self.nova("list", params="--limit -1 --name %s" % name)
        # Cut header and footer of the table
        for server in precreated_servers:
            self.assertIn(server.id, output)

    def test_list_minimal(self):
        server = self._create_server()
        server_output = self.nova("list --minimal")
        # The only fields output are "ID" and "Name"
        output_uuid = self._get_column_value_from_single_row_table(
            server_output, 'ID')
        output_name = self._get_column_value_from_single_row_table(
            server_output, 'Name')
        self.assertEqual(output_uuid, server.id)
        self.assertEqual(output_name, server.name)

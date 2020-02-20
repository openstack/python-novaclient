# -*- coding: utf-8 -*-
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

import random
import string

from tempest.lib import decorators

from novaclient.tests.functional import base
from novaclient.tests.functional.v2.legacy import test_servers
from novaclient.v2 import shell


class TestServersBootNovaClient(test_servers.TestServersBootNovaClient):
    """Servers boot functional tests."""

    COMPUTE_API_VERSION = "2.latest"


class TestServersListNovaClient(test_servers.TestServersListNovaClient):
    """Servers list functional tests."""

    COMPUTE_API_VERSION = "2.latest"


class TestServerLockV29(base.ClientTestBase):

    COMPUTE_API_VERSION = "2.9"

    def _show_server_and_check_lock_attr(self, server, value):
        output = self.nova("show %s" % server.id)
        self.assertEqual(str(value),
                         self._get_value_from_the_table(output, "locked"))

    def test_attribute_presented(self):
        # prepare
        server = self._create_server()

        # testing
        self._show_server_and_check_lock_attr(server, False)

        self.nova("lock %s" % server.id)
        self._show_server_and_check_lock_attr(server, True)

        self.nova("unlock %s" % server.id)
        self._show_server_and_check_lock_attr(server, False)


class TestServersDescription(base.ClientTestBase):

    COMPUTE_API_VERSION = "2.19"

    def _boot_server_with_description(self):
        descr = "Some words about this test VM."
        server = self._create_server(description=descr)

        self.assertEqual(descr, server.description)

        return server, descr

    def test_create(self):
        # Add a description to the tests that create a server
        server, descr = self._boot_server_with_description()
        output = self.nova("show %s" % server.id)
        self.assertEqual(descr, self._get_value_from_the_table(output,
                                                               "description"))

    def test_list_servers_with_description(self):
        # Check that the description is returned as part of server details
        # for a server list
        server, descr = self._boot_server_with_description()
        output = self.nova("list --fields description")
        self.assertEqual(server.id,
                         self._get_column_value_from_single_row_table(
                             output, "ID"))
        self.assertEqual(descr,
                         self._get_column_value_from_single_row_table(
                             output, "Description"))

    @decorators.skip_because(bug="1694371")
    def test_rebuild(self):
        # Add a description to the tests that rebuild a server
        server, descr = self._boot_server_with_description()
        descr = "New description for rebuilt VM."
        self.nova("rebuild --description '%s' %s %s" %
                  (descr, server.id, self.image.name))
        shell._poll_for_status(
            self.client.servers.get, server.id,
            'rebuild', ['active'])
        output = self.nova("show %s" % server.id)
        self.assertEqual(descr, self._get_value_from_the_table(output,
                                                               "description"))

    def test_remove_description(self):
        # Remove description from server booted with it
        server, descr = self._boot_server_with_description()
        self.nova("update %s --description ''" % server.id)
        output = self.nova("show %s" % server.id)
        self.assertEqual("-", self._get_value_from_the_table(output,
                                                             "description"))

    def test_add_remove_description_on_existing_server(self):
        # Set and remove the description on an existing server
        server = self._create_server()
        descr = "Add a description for previously-booted VM."
        self.nova("update %s --description '%s'" % (server.id, descr))
        output = self.nova("show %s" % server.id)
        self.assertEqual(descr, self._get_value_from_the_table(output,
                                                               "description"))
        self.nova("update %s --description ''" % server.id)
        output = self.nova("show %s" % server.id)
        self.assertEqual("-", self._get_value_from_the_table(output,
                                                             "description"))

    def test_update_with_description_longer_than_255_symbols(self):
        # Negative case for description longer than 255 characters
        server = self._create_server()
        descr = ''.join(random.choice(string.ascii_letters)
                        for i in range(256))
        output = self.nova("update %s --description '%s'" % (server.id, descr),
                           fail_ok=True, merge_stderr=True)
        self.assertIn("ERROR (BadRequest): Invalid input for field/attribute"
                      " description. Value: %s. '%s' is too long (HTTP 400)"
                      % (descr, descr), output)


class TestServersTagsV226(base.ClientTestBase):

    COMPUTE_API_VERSION = "2.26"

    def _boot_server_with_tags(self, tags=["t1", "t2"]):
        uuid = self._create_server().id
        self.client.servers.set_tags(uuid, tags)
        return uuid

    def test_show(self):
        uuid = self._boot_server_with_tags()
        output = self.nova("show %s" % uuid)
        self.assertEqual('["t1", "t2"]', self._get_value_from_the_table(
            output, "tags"))

    def test_unicode_tag_correctly_displayed(self):
        """Regression test for bug #1669683.

        List and dict fields with unicode cannot be correctly
        displayed.

        Ensure that once we fix this it doesn't regress.
        """
        # create an instance with chinese tag
        uuid = self._boot_server_with_tags(tags=["中文标签"])
        output = self.nova("show %s" % uuid)
        self.assertEqual('["中文标签"]', self._get_value_from_the_table(
            output, "tags"))

    def test_list(self):
        uuid = self._boot_server_with_tags()
        output = self.nova("server-tag-list %s" % uuid)
        tags = self._get_list_of_values_from_single_column_table(
            output, "Tag")
        self.assertEqual(["t1", "t2"], tags)

    def test_add(self):
        uuid = self._boot_server_with_tags()
        self.nova("server-tag-add %s t3" % uuid)
        self.assertEqual(["t1", "t2", "t3"],
                         self.client.servers.tag_list(uuid))

    def test_add_many(self):
        uuid = self._boot_server_with_tags()
        self.nova("server-tag-add %s t3 t4" % uuid)
        self.assertEqual(["t1", "t2", "t3", "t4"],
                         self.client.servers.tag_list(uuid))

    def test_set(self):
        uuid = self._boot_server_with_tags()
        self.nova("server-tag-set %s t3 t4" % uuid)
        self.assertEqual(["t3", "t4"], self.client.servers.tag_list(uuid))

    def test_delete(self):
        uuid = self._boot_server_with_tags()
        self.nova("server-tag-delete %s t2" % uuid)
        self.assertEqual(["t1"], self.client.servers.tag_list(uuid))

    def test_delete_many(self):
        uuid = self._boot_server_with_tags()
        self.nova("server-tag-delete %s t1 t2" % uuid)
        self.assertEqual([], self.client.servers.tag_list(uuid))

    def test_delete_all(self):
        uuid = self._boot_server_with_tags()
        self.nova("server-tag-delete-all %s" % uuid)
        self.assertEqual([], self.client.servers.tag_list(uuid))


class TestServersAutoAllocateNetworkCLI(base.ClientTestBase):

    COMPUTE_API_VERSION = '2.37'

    def _find_network_in_table(self, table):
        # Example:
        # +-----------------+-----------------------------------+
        # |   Property      |               Value               |
        # +-----------------+-----------------------------------+
        # | private network |          192.168.154.128          |
        # +-----------------+-----------------------------------+
        for line in table.split('\n'):
            if '|' in line:
                l_property, l_value = line.split('|')[1:3]
                if ' network' in l_property.strip():
                    return ' '.join(l_property.strip().split()[:-1])

    def test_boot_server_with_auto_network(self):
        """Tests that the CLI defaults to 'auto' when --nic isn't specified.
        """
        # check to see if multiple networks are available because if so we
        # have to skip this test as auto will fail with a 409 conflict as it's
        # an ambiguous request and nova won't know which network to pick
        if self.multiple_networks:
            # we could potentially get around this by extending TenantTestBase
            self.skipTest('multiple networks available')
        server_info = self.nova('boot', params=(
            '%(name)s --flavor %(flavor)s --poll '
            '--image %(image)s ' % {'name': self.name_generate(),
                                    'flavor': self.flavor.id,
                                    'image': self.image.id}))
        server_id = self._get_value_from_the_table(server_info, 'id')
        self.addCleanup(self.wait_for_resource_delete,
                        server_id, self.client.servers)
        self.addCleanup(self.client.servers.delete, server_id)
        # get the server details to verify there is a network, we don't care
        # what the network name is, we just want to see an entry show up
        server_info = self.nova('show', params=server_id)
        network = self._find_network_in_table(server_info)
        self.assertIsNotNone(
            network, 'Auto-allocated network not found: %s' % server_info)

    def test_boot_server_with_no_network(self):
        """Tests that '--nic none' is honored.
        """
        server_info = self.nova('boot', params=(
            '%(name)s --flavor %(flavor)s --poll '
            '--image %(image)s --nic none' %
            {'name': self.name_generate(),
             'flavor': self.flavor.id,
             'image': self.image.id}))
        server_id = self._get_value_from_the_table(server_info, 'id')
        self.addCleanup(self.wait_for_resource_delete,
                        server_id, self.client.servers)
        self.addCleanup(self.client.servers.delete, server_id)
        # get the server details to verify there is not a network
        server_info = self.nova('show', params=server_id)
        network = self._find_network_in_table(server_info)
        self.assertIsNone(
            network, 'Unexpected network allocation: %s' % server_info)


class TestServersDetailsFlavorInfo(base.ClientTestBase):

    COMPUTE_API_VERSION = '2.47'

    def _validate_flavor_details(self, flavor_details, server_details):
        # This is a mapping between the keys used in the flavor GET response
        # and the keys used for the flavor information embedded in the server
        # details.
        flavor_key_mapping = {
            "OS-FLV-EXT-DATA:ephemeral": "flavor:ephemeral",
            "disk": "flavor:disk",
            "extra_specs": "flavor:extra_specs",
            "name": "flavor:original_name",
            "ram": "flavor:ram",
            "swap": "flavor:swap",
            "vcpus": "flavor:vcpus",
        }

        for key in flavor_key_mapping:
            flavor_val = self._get_value_from_the_table(
                flavor_details, key)
            server_flavor_val = self._get_value_from_the_table(
                server_details, flavor_key_mapping[key])
            if key == "swap" and flavor_val == "":
                # "flavor-show" displays zero swap as empty string.
                flavor_val = '0'
            self.assertEqual(flavor_val, server_flavor_val)

    def _setup_extra_specs(self, flavor_id):
        extra_spec_key = "dummykey"
        self.nova('flavor-key', params=('%(flavor)s set %(key)s=dummyval' %
                                        {'flavor': flavor_id,
                                         'key': extra_spec_key}))
        unset_params = ('%(flavor)s unset %(key)s' %
                        {'flavor': flavor_id, 'key': extra_spec_key})
        self.addCleanup(self.nova, 'flavor-key', params=unset_params)

    def test_show(self):
        self._setup_extra_specs(self.flavor.id)
        uuid = self._create_server().id
        server_output = self.nova("show %s" % uuid)
        flavor_output = self.nova("flavor-show %s" % self.flavor.id)
        self._validate_flavor_details(flavor_output, server_output)

    def test_show_minimal(self):
        uuid = self._create_server().id
        server_output = self.nova("show --minimal %s" % uuid)
        server_output_flavor = self._get_value_from_the_table(
            server_output, 'flavor')
        self.assertEqual(self.flavor.name, server_output_flavor)

    def test_list(self):
        self._setup_extra_specs(self.flavor.id)
        self._create_server()
        server_output = self.nova("list --fields flavor:disk")
        # namespaced fields get reformatted slightly as column names
        server_flavor_val = self._get_column_value_from_single_row_table(
            server_output, 'flavor: Disk')
        flavor_output = self.nova("flavor-show %s" % self.flavor.id)
        flavor_val = self._get_value_from_the_table(flavor_output, 'disk')
        self.assertEqual(flavor_val, server_flavor_val)


class TestInterfaceAttach(base.ClientTestBase):

    COMPUTE_API_VERSION = '2.latest'

    def test_interface_attach(self):
        server = self._create_server()
        output = self.nova("interface-attach --net-id %s %s" %
                           (self.network.id, server.id))

        for key in ('ip_address', 'mac_addr', 'port_id', 'port_state'):
            self._get_value_from_the_table(output, key)

        self.assertEqual(
            self.network.id,
            self._get_value_from_the_table(output, 'net_id'))


class TestServeRebuildV274(base.ClientTestBase):

    COMPUTE_API_VERSION = '2.74'
    REBUILD_FIELDS = ["OS-DCF:diskConfig", "accessIPv4", "accessIPv6",
                      "adminPass", "created", "description",
                      "flavor", "hostId", "id", "image", "key_name",
                      "locked", "locked_reason", "metadata", "name",
                      "progress", "server_groups", "status", "tags",
                      "tenant_id", "trusted_image_certificates", "updated",
                      "user_data", "user_id"]

    def test_rebuild(self):
        server = self._create_server()
        output = self.nova("rebuild %s %s" % (server.id, self.image.name))
        for field in self.REBUILD_FIELDS:
            self.assertIn(field, output)


class TestServeRebuildV275(TestServeRebuildV274):

    COMPUTE_API_VERSION = '2.75'
    REBUILD_FIELDS_V275 = ['OS-EXT-AZ:availability_zone', 'config_drive',
                           'OS-EXT-SRV-ATTR:host',
                           'OS-EXT-SRV-ATTR:hypervisor_hostname',
                           'OS-EXT-SRV-ATTR:instance_name',
                           'OS-EXT-SRV-ATTR:hostname',
                           'OS-EXT-SRV-ATTR:kernel_id',
                           'OS-EXT-SRV-ATTR:launch_index',
                           'OS-EXT-SRV-ATTR:ramdisk_id',
                           'OS-EXT-SRV-ATTR:reservation_id',
                           'OS-EXT-SRV-ATTR:root_device_name',
                           'host_status',
                           'OS-SRV-USG:launched_at',
                           'OS-SRV-USG:terminated_at',
                           'OS-EXT-STS:task_state', 'OS-EXT-STS:vm_state',
                           'OS-EXT-STS:power_state', 'security_groups',
                           'os-extended-volumes:volumes_attached']

    REBUILD_FIELDS = TestServeRebuildV274.REBUILD_FIELDS + REBUILD_FIELDS_V275

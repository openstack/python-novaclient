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
        descr = ''.join(random.choice(string.letters) for i in range(256))
        output = self.nova("update %s --description '%s'" % (server.id, descr),
                           fail_ok=True, merge_stderr=True)
        self.assertIn("\nERROR (BadRequest): Invalid input for field/attribute"
                      " description. Value: %s. u\'%s\' is too long (HTTP 400)"
                      % (descr, descr), output)

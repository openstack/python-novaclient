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
from novaclient.tests.functional.v2.legacy import test_servers


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
        server, descr = self._boot_server_with_description()

        output = self.nova("show %s" % server.id)
        self.assertEqual(descr, self._get_value_from_the_table(output,
                                                               "description"))

    def test_update(self):
        server, descr = self._boot_server_with_description()

        # remove description
        self.nova("update %s --description ''" % server.id)

        output = self.nova("show %s" % server.id)
        self.assertEqual("-", self._get_value_from_the_table(output,
                                                             "description"))

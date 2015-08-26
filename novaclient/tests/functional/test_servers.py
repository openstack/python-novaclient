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
from novaclient.v2 import shell


class TestServersListNovaClient(base.ClientTestBase):
    """Servers list functional tests.
    """

    def _create_servers(self, name, number):
        network = self.client.networks.list()[0]
        servers = []
        for i in range(number):
            servers.append(self.client.servers.create(
                name, self.image, self.flavor, nics=[{"net-id": network.id}]))
            shell._poll_for_status(
                self.client.servers.get, servers[-1].id,
                'building', ['active'])

            self.addCleanup(servers[-1].delete)
        return servers

    def test_list_with_limit(self):
        name = str(uuid.uuid4())
        self._create_servers(name, 2)
        output = self.nova("list", params="--limit 1 --name %s" % name)
        # Cut header and footer of the table
        servers = output.split("\n")[3:-2]
        self.assertEqual(1, len(servers), output)

    def test_list_all_servers(self):
        name = str(uuid.uuid4())
        precreated_servers = self._create_servers(name, 3)
        # there are no possibility to exceed the limit on API side, so just
        # check that "-1" limit processes by novaclient side
        output = self.nova("list", params="--limit -1 --name %s" % name)
        # Cut header and footer of the table
        for server in precreated_servers:
            self.assertIn(server.id, output)

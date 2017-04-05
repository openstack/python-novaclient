# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import time

from novaclient.tests.functional import base


class TestServersAPI(base.ClientTestBase):
    def test_server_ips(self):
        server_name = "test_server"
        initial_server = self.client.servers.create(
            server_name, self.image, self.flavor,
            nics=[{"net-id": self.network.id}])
        self.addCleanup(initial_server.delete)

        for x in range(60):
            server = self.client.servers.get(initial_server)
            if server.status == "ACTIVE":
                break
            else:
                time.sleep(1)
        else:
            self.fail("Server %s did not go ACTIVE after 60s" % server)

        ips = self.client.servers.ips(server)
        self.assertIn(self.network.name, ips)

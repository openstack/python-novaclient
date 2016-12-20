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

from novaclient.tests.functional.v2.legacy import test_usage


class TestUsageCLI_V240(test_usage.TestUsageCLI):

    COMPUTE_API_VERSION = '2.40'


class TestUsageClient_V240(test_usage.TestUsageClient):

    COMPUTE_API_VERSION = '2.40'

    def test_get(self):
        start, end = self._create_servers_in_time_window()
        tenant_id = self._get_project_id(self.cli_clients.tenant_name)
        usage = self.client.usage.get(
            tenant_id, start=start, end=end, limit=1)
        self.assertEqual(tenant_id, usage.tenant_id)
        self.assertEqual(1, len(usage.server_usages))

    def test_list(self):
        start, end = self._create_servers_in_time_window()
        usages = self.client.usage.list(
            start=start, end=end, detailed=True, limit=1)
        self.assertEqual(1, len(usages))
        self.assertEqual(1, len(usages[0].server_usages))

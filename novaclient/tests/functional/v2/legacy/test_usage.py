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

from novaclient.tests.functional import base


class TestUsageCLI(base.ClientTestBase):

    COMPUTE_API_VERSION = '2.1'

    def _get_num_servers_from_usage_output(self):
        output = self.nova('usage')
        servers = self._get_column_value_from_single_row_table(
            output, 'Servers')
        return int(servers)

    def _get_num_servers_by_tenant_from_usage_output(self):
        tenant_id = self._get_project_id(self.cli_clients.tenant_name)
        output = self.nova('usage --tenant=%s' % tenant_id)
        servers = self._get_column_value_from_single_row_table(
            output, 'Servers')
        return int(servers)

    def test_usage(self):
        before = self._get_num_servers_from_usage_output()
        self._create_server('some-server')
        after = self._get_num_servers_from_usage_output()
        self.assertGreater(after, before)

    def test_usage_tenant(self):
        before = self._get_num_servers_by_tenant_from_usage_output()
        self._create_server('some-server')
        after = self._get_num_servers_by_tenant_from_usage_output()
        self.assertGreater(after, before)


class TestUsageClient(base.ClientTestBase):

    COMPUTE_API_VERSION = '2.1'

    def _create_servers_in_time_window(self):
        start = datetime.datetime.now()
        self._create_server('some-server')
        self._create_server('another-server')
        end = datetime.datetime.now()
        return start, end

    def test_get(self):
        start, end = self._create_servers_in_time_window()
        tenant_id = self._get_project_id(self.cli_clients.tenant_name)
        usage = self.client.usage.get(tenant_id, start=start, end=end)
        self.assertEqual(tenant_id, usage.tenant_id)
        self.assertGreaterEqual(len(usage.server_usages), 2)

    def test_list(self):
        start, end = self._create_servers_in_time_window()
        tenant_id = self._get_project_id(self.cli_clients.tenant_name)
        usages = self.client.usage.list(start=start, end=end, detailed=True)
        tenant_ids = [usage.tenant_id for usage in usages]
        self.assertIn(tenant_id, tenant_ids)
        for usage in usages:
            if usage.tenant_id == tenant_id:
                self.assertGreaterEqual(len(usage.server_usages), 2)

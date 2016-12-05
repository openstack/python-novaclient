#    Copyright 2015 Huawei Technology corp.
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

from oslo_utils import uuidutils

from novaclient.tests.functional import base


class TestServerGroupClient(base.ClientTestBase):
    """Server groups v2.1 functional tests."""

    COMPUTE_API_VERSION = "2.1"

    def _create_sg(self, policy):
        sg_name = 'server_group-' + uuidutils.generate_uuid()
        output = self.nova('server-group-create %s %s' % (sg_name, policy))
        sg_id = self._get_column_value_from_single_row_table(output, "Id")
        return sg_id

    def test_create_server_group(self):
        sg_id = self._create_sg("affinity")
        self.addCleanup(self.nova, 'server-group-delete %s' % sg_id)
        sg = self.nova('server-group-get %s' % sg_id)
        result = self._get_column_value_from_single_row_table(sg, "Id")
        self.assertEqual(sg_id, result)

    def test_list_server_group(self):
        sg_id = self._create_sg("affinity")
        self.addCleanup(self.nova, 'server-group-delete %s' % sg_id)
        sg = self.nova('server-group-list')
        result = self._get_column_value_from_single_row_table(sg, "Id")
        self.assertEqual(sg_id, result)

    def test_delete_server_group(self):
        sg_id = self._create_sg("affinity")
        sg = self.nova('server-group-get %s' % sg_id)
        result = self._get_column_value_from_single_row_table(sg, "Id")
        self.assertIsNotNone(result)
        self.nova('server-group-delete %s' % sg_id)

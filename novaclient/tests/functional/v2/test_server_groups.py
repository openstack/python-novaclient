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

from novaclient.tests.functional.v2.legacy import test_server_groups


class TestServerGroupClientV213(test_server_groups.TestServerGroupClient):
    """Server groups v2.13 functional tests."""

    COMPUTE_API_VERSION = "2.13"
    expected_metadata = True
    expected_policy_rules = False

    def test_create_server_group(self):
        sg_id = self._create_sg("affinity")
        self.addCleanup(self.nova, 'server-group-delete %s' % sg_id)
        sg = self.nova('server-group-get %s' % sg_id)
        result = self._get_column_value_from_single_row_table(sg, "Id")
        self._get_column_value_from_single_row_table(
            sg, "User Id")
        self._get_column_value_from_single_row_table(
            sg, "Project Id")
        self.assertEqual(sg_id, result)
        self._get_column_value_from_single_row_table(sg, "Metadata")
        self.assertIn(
            'affinity',
            self._get_column_value_from_single_row_table(sg, 'Policies'))
        self.assertNotIn('Rules', sg)

    def test_list_server_groups(self):
        sg_id = self._create_sg("affinity")
        self.addCleanup(self.nova, 'server-group-delete %s' % sg_id)
        sg = self.nova("server-group-list")
        result = self._get_column_value_from_single_row_table(sg, "Id")
        self._get_column_value_from_single_row_table(
            sg, "User Id")
        self._get_column_value_from_single_row_table(
            sg, "Project Id")
        self.assertEqual(sg_id, result)
        if self.expected_metadata:
            self._get_column_value_from_single_row_table(sg, "Metadata")
        else:
            self.assertNotIn(sg, 'Metadata')
        if self.expected_policy_rules:
            self.assertEqual(
                'affinity',
                self._get_column_value_from_single_row_table(sg, "Policy"))
            self.assertEqual(
                '{}',
                self._get_column_value_from_single_row_table(sg, "Rules"))
        else:
            self.assertIn(
                'affinity',
                self._get_column_value_from_single_row_table(sg, 'Policies'))
            self.assertNotIn('Rules', sg)

    def test_get_server_group(self):
        sg_id = self._create_sg("affinity")
        self.addCleanup(self.nova, 'server-group-delete %s' % sg_id)
        sg = self.nova('server-group-get %s' % sg_id)
        result = self._get_column_value_from_single_row_table(sg, "Id")
        self._get_column_value_from_single_row_table(
            sg, "User Id")
        self._get_column_value_from_single_row_table(
            sg, "Project Id")
        self.assertEqual(sg_id, result)
        if self.expected_metadata:
            self._get_column_value_from_single_row_table(sg, "Metadata")
        else:
            self.assertNotIn(sg, 'Metadata')
        if self.expected_policy_rules:
            self.assertEqual(
                'affinity',
                self._get_column_value_from_single_row_table(sg, "Policy"))
            self.assertEqual(
                '{}',
                self._get_column_value_from_single_row_table(sg, "Rules"))
        else:
            self.assertIn(
                'affinity',
                self._get_column_value_from_single_row_table(sg, 'Policies'))
            self.assertNotIn('Rules', sg)


class TestServerGroupClientV264(TestServerGroupClientV213):
    """Server groups v2.64 functional tests."""

    COMPUTE_API_VERSION = "2.64"
    expected_metadata = False
    expected_policy_rules = True

    def test_create_server_group(self):
        output = self.nova('server-group-create complex-anti-affinity-group '
                           'anti-affinity --rule max_server_per_host=3')
        sg_id = self._get_column_value_from_single_row_table(output, "Id")
        self.addCleanup(self.nova, 'server-group-delete %s' % sg_id)
        sg = self.nova('server-group-get %s' % sg_id)
        result = self._get_column_value_from_single_row_table(sg, "Id")
        self.assertEqual(sg_id, result)
        self._get_column_value_from_single_row_table(
            sg, "User Id")
        self._get_column_value_from_single_row_table(
            sg, "Project Id")
        self.assertNotIn('Metadata', sg)
        self.assertEqual(
            'anti-affinity',
            self._get_column_value_from_single_row_table(sg, "Policy"))
        self.assertIn(
            'max_server_per_host',
            self._get_column_value_from_single_row_table(sg, "Rules"))

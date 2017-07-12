# Copyright 2017 Huawei Technologies Co.,LTD.
#
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

from tempest.lib import exceptions

from novaclient.tests.functional import base


class TestQuotaClassesNovaClient(base.ClientTestBase):
    """Nova quota classes functional tests for the v2.1 microversion."""

    COMPUTE_API_VERSION = '2.1'

    # The list of quota class resources we expect in the output table.
    _included_resources = ['instances', 'cores', 'ram',
                           'floating_ips', 'fixed_ips', 'metadata_items',
                           'injected_files', 'injected_file_content_bytes',
                           'injected_file_path_bytes', 'key_pairs',
                           'security_groups', 'security_group_rules']

    # The list of quota class resources we do not expect in the output table.
    _excluded_resources = ['server_groups', 'server_group_members']

    # Any resources that are not shown but can be updated. For example, before
    # microversion 2.50 you can update server_groups and server_groups_members
    # quota class values but they are not shown in the GET response.
    _extra_update_resources = _excluded_resources

    # The list of resources which are blocked from being updated.
    _blocked_update_resources = []

    def _get_quota_class_name(self):
        """Returns a fake quota class name specific to this test class."""
        return 'fake-class-%s' % self.COMPUTE_API_VERSION.replace('.', '-')

    def _verify_qouta_class_show_output(self, output, expected_values):
        # Assert that the expected key/value pairs are in the output table
        for quota_name in self._included_resources:
            # First make sure the resource is actually in expected quota.
            self.assertIn(quota_name, expected_values)
            expected_value = expected_values[quota_name]
            actual_value = self._get_value_from_the_table(output, quota_name)
            self.assertEqual(expected_value, actual_value)

        # Now make sure anything that we don't expect in the output table is
        # actually not showing up.
        for quota_name in self._excluded_resources:
            # ValueError is raised when the key isn't found in the table.
            self.assertRaises(ValueError,
                              self._get_value_from_the_table,
                              output, quota_name)

    def test_quota_class_show(self):
        """Tests showing quota class values for a fake non-existing quota
        class. The API will return the defaults if the quota class does not
        actually exist. We use a fake class to avoid any interaction with the
        real default quota class values.
        """
        default_quota_class_set = self.client.quota_classes.get('default')
        default_values = {
            quota_name: str(getattr(default_quota_class_set, quota_name))
            for quota_name in self._included_resources
        }
        output = self.nova('quota-class-show %s' %
                           self._get_quota_class_name())
        self._verify_qouta_class_show_output(output, default_values)

    def test_quota_class_update(self):
        """Tests updating a fake quota class. The way this works in the API
        is that if the quota class is not found, it is created. So in this
        test we can use a fake quota class with fake values and they will all
        get set. We don't use the default quota class because it is global
        and we don't want to interfere with other tests.
        """
        class_name = self._get_quota_class_name()
        params = [class_name]
        expected_values = {}
        for quota_name in (
                self._included_resources + self._extra_update_resources):
            params.append("--%s 99" % quota_name.replace("_", "-"))
            expected_values[quota_name] = '99'

        # Note that the quota-class-update CLI doesn't actually output any
        # information from the response.
        self.nova("quota-class-update", params=" ".join(params))
        # Assert the results using the quota-class-show output.
        output = self.nova('quota-class-show %s' % class_name)
        self._verify_qouta_class_show_output(output, expected_values)

        # Assert that attempting to update resources that are blocked will
        # result in a failure.
        for quota_name in self._blocked_update_resources:
            self.assertRaises(
                exceptions.CommandFailed,
                self.nova, "quota-class-update %s --%s 99" %
                           (class_name, quota_name.replace("_", "-")))


class TestQuotasNovaClient2_50(TestQuotaClassesNovaClient):
    """Nova quota classes functional tests for the v2.50 microversion."""

    COMPUTE_API_VERSION = '2.50'

    # The 2.50 microversion added the server_groups and server_group_members
    # to the response, and filtered out floating_ips, fixed_ips,
    # security_groups and security_group_members, similar to the 2.36
    # microversion in the os-qouta-sets API.
    _included_resources = ['instances', 'cores', 'ram', 'metadata_items',
                           'injected_files', 'injected_file_content_bytes',
                           'injected_file_path_bytes', 'key_pairs',
                           'server_groups', 'server_group_members']

    # The list of quota class resources we do not expect in the output table.
    _excluded_resources = ['floating_ips', 'fixed_ips',
                           'security_groups', 'security_group_rules']

    # In 2.50, server_groups and server_group_members can be both updated
    # in a PUT request and shown in a GET response.
    _extra_update_resources = []

    # In 2.50, you can't update the network-related resources.
    _blocked_update_resources = _excluded_resources

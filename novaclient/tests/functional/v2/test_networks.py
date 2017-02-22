# Copyright 2016 Red Hat, Inc.
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


class TestNetworkCommandsV2_36(base.ClientTestBase):
    """Deprecated network command functional tests."""

    # Proxy APIs were deprecated in 2.36 but the CLI should fallback to 2.35
    # and emit a warning.
    COMPUTE_API_VERSION = "2.36"

    def test_limits(self):
        """Tests that 2.36 won't return network-related resource limits and
        the CLI output won't show them.
        """
        output = self.nova('limits')
        # assert that SecurityGroups isn't in the table output
        self.assertRaises(ValueError, self._get_value_from_the_table,
                          output, 'SecurityGroups')

    def test_quota_show(self):
        """Tests that 2.36 won't return network-related resource quotas and
        the CLI output won't show them.
        """
        output = self.nova('quota-show')
        # assert that security_groups isn't in the table output
        self.assertRaises(ValueError, self._get_value_from_the_table,
                          output, 'security_groups')

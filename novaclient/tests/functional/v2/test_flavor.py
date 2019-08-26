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


class TestFlavorNovaClientV274(base.ClientTestBase):
    """Functional tests for flavors"""

    COMPUTE_API_VERSION = "2.74"
    # NOTE(gmann): Before microversion 2.75, default value of 'swap' field is
    # returned as empty string.
    SWAP_DEFAULT = ""

    def _create_flavor(self, swap=None):
        flv_name = self.name_generate()
        cmd = 'flavor-create %s auto 512 1 1'
        if swap:
            cmd = cmd + (' --swap %s' % swap)
        out = self.nova(cmd % flv_name)
        self.addCleanup(self.nova, 'flavor-delete %s' % flv_name)
        return out, flv_name

    def test_create_flavor_with_no_swap(self):
        out, _ = self._create_flavor()
        self.assertEqual(
            self.SWAP_DEFAULT,
            self._get_column_value_from_single_row_table(out, "Swap"))

    def test_update_flavor_with_no_swap(self):
        _, flv_name = self._create_flavor()
        out = self.nova('flavor-update %s new-description' % flv_name)
        self.assertEqual(
            self.SWAP_DEFAULT,
            self._get_column_value_from_single_row_table(out, "Swap"))

    def test_show_flavor_with_no_swap(self):
        _, flv_name = self._create_flavor()
        out = self.nova('flavor-show %s' % flv_name)
        self.assertEqual(self.SWAP_DEFAULT,
                         self._get_value_from_the_table(out, "swap"))

    def test_list_flavor_with_no_swap(self):
        self._create_flavor()
        out = self.nova('flavor-list')
        self.assertEqual(
            self.SWAP_DEFAULT,
            self._get_column_value_from_single_row_table(out, "Swap"))

    def test_create_flavor_with_swap(self):
        out, _ = self._create_flavor(swap=10)
        self.assertEqual(
            '10',
            self._get_column_value_from_single_row_table(out, "Swap"))


class TestFlavorNovaClientV275(TestFlavorNovaClientV274):
    """Functional tests for flavors"""

    COMPUTE_API_VERSION = "2.75"
    # NOTE(gmann): Since microversion 2.75, default value of 'swap' field is
    # returned as 0.
    SWAP_DEFAULT = '0'

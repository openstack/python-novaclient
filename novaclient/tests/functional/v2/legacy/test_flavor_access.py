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


class TestFlvAccessNovaClient(base.TenantTestBase):
    """Functional tests for flavors with public and non-public access"""

    COMPUTE_API_VERSION = "2.1"

    def test_public_flavor_list(self):
        # Check that flavors with public access are available for both admin
        # and non-admin tenants
        flavor_list1 = self.nova('flavor-list')
        flavor_list2 = self.another_nova('flavor-list')
        self.assertEqual(flavor_list1, flavor_list2)

    def test_non_public_flavor_list(self):
        # Check that non-public flavor appears in flavor list
        # only for admin tenant and only with --all attribute
        # and doesn't appear for non-admin tenant
        flv_name = self.name_generate(prefix='flv')
        self.nova('flavor-create --is-public false %s auto 512 1 1' % flv_name)
        self.addCleanup(self.nova, 'flavor-delete %s' % flv_name)
        flavor_list1 = self.nova('flavor-list')
        self.assertNotIn(flv_name, flavor_list1)
        flavor_list2 = self.nova('flavor-list --all')
        flavor_list3 = self.another_nova('flavor-list --all')
        self.assertIn(flv_name, flavor_list2)
        self.assertNotIn(flv_name, flavor_list3)

    def test_add_access_non_public_flavor(self):
        # Check that it's allowed to grant an access to non-public flavor for
        # the given tenant
        flv_name = self.name_generate(prefix='flv')
        self.nova('flavor-create --is-public false %s auto 512 1 1' % flv_name)
        self.addCleanup(self.nova, 'flavor-delete %s' % flv_name)
        self.nova('flavor-access-add', params="%s %s" %
                                              (flv_name, self.project_id))
        self.assertIn(self.project_id,
                      self.nova('flavor-access-list --flavor %s' % flv_name))

    def test_add_access_public_flavor(self):
        # For microversion < 2.7 the 'flavor-access-add' operation is executed
        # successfully for public flavor, but the next operation,
        # 'flavor-access-list --flavor %(name_of_public_flavor)' returns
        # a CommandError
        flv_name = self.name_generate(prefix='flv')
        self.nova('flavor-create %s auto 512 1 1' % flv_name)
        self.addCleanup(self.nova, 'flavor-delete %s' % flv_name)
        self.nova('flavor-access-add %s %s' % (flv_name, self.project_id))
        output = self.nova('flavor-access-list --flavor %s' % flv_name,
                           fail_ok=True, merge_stderr=True)
        self.assertIn("CommandError", output)

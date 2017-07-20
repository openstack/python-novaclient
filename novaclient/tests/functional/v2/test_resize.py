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

from novaclient.tests.functional import base


class TestServersResize(base.ClientTestBase):
    """Servers resize functional tests."""

    COMPUTE_API_VERSION = '2.1'

    def _create_server(self, name, flavor):
        """Boots a server with the given name and flavor and waits for it to
        be ACTIVE.
        """
        params = (
            "%(name)s --flavor %(flavor)s --image %(image)s --poll " % {
                "name": self.name_generate(name),
                "flavor": flavor,
                "image": self.image.id})
        # check to see if we have to pass in a network id
        if self.multiple_networks:
            params += ' --nic net-id=%s' % self.network.id
        server_info = self.nova("boot", params=params)
        server_id = self._get_value_from_the_table(server_info, "id")
        self.addCleanup(self._cleanup_server, server_id)
        return server_id

    def _pick_alternate_flavor(self):
        """Given the flavor picked in the base class setup, this finds the
        opposite flavor to use for a resize test. For example, if m1.nano is
        the flavor, then use m1.micro, but those are only available if Tempest
        is configured. If m1.tiny, then use m1.small.
        """
        flavor_name = self.flavor.name
        if flavor_name == 'm1.nano':
            # This is an upsize test.
            return 'm1.micro'
        if flavor_name == 'm1.micro':
            # This is a downsize test.
            return 'm1.nano'
        if flavor_name == 'm1.tiny':
            # This is an upsize test.
            return 'm1.small'
        if flavor_name == 'm1.small':
            # This is a downsize test.
            return 'm1.tiny'
        self.fail('Unable to find alternate for flavor: %s' % flavor_name)

    def _compare_quota_usage(self, old_usage, new_usage, expect_diff=True):
        """Compares the quota usage in the provided AbsoluteLimits."""
        # For a resize, instance usage shouldn't change.
        self.assertEqual(old_usage['totalInstancesUsed'],
                         new_usage['totalInstancesUsed'],
                         'totalInstancesUsed does not match')
        # For the resize we're doing, those flavors have the same vcpus so we
        # don't expect any quota change.
        self.assertEqual(old_usage['totalCoresUsed'],
                         new_usage['totalCoresUsed'],
                         'totalCoresUsed does not match')
        # RAM is the only thing that will change for these flavors in a resize.
        if expect_diff:
            self.assertNotEqual(old_usage['totalRAMUsed'],
                                new_usage['totalRAMUsed'],
                                'totalRAMUsed should have changed')
        else:
            self.assertEqual(old_usage['totalRAMUsed'],
                             new_usage['totalRAMUsed'],
                             'totalRAMUsed does not match')

    def test_resize_up_confirm(self):
        """Tests creating a server and resizes up and confirms the resize.
        Compares quota before, during and after the resize.
        """
        server_id = self._create_server('resize-up-confirm', self.flavor.name)
        # get the starting quota now that we've created a server
        starting_usage = self._get_absolute_limits()
        # now resize up
        alternate_flavor = self._pick_alternate_flavor()
        self.nova('resize',
                  params='%s %s --poll' % (server_id, alternate_flavor))
        resize_usage = self._get_absolute_limits()
        # compare the starting usage against the resize usage
        self._compare_quota_usage(starting_usage, resize_usage)
        # now confirm the resize
        self.nova('resize-confirm', params='%s' % server_id)
        # we have to wait for the server to be ACTIVE before we can check quota
        self._wait_for_state_change(server_id, 'active')
        # get the final quota usage which should be the same as the resize
        # usage before confirm
        confirm_usage = self._get_absolute_limits()
        self._compare_quota_usage(
            resize_usage, confirm_usage, expect_diff=False)

    def _create_resize_down_flavors(self):
        """Creates two flavors with different size ram but same size vcpus
        and disk.

        :returns: tuple of (larger_flavor_name, smaller_flavor_name)
        """
        self.nova('flavor-create', params='resize-larger-flavor auto 128 0 1')
        self.addCleanup(
            self.nova, 'flavor-delete', params='resize-larger-flavor')

        self.nova('flavor-create', params='resize-smaller-flavor auto 64 0 1')
        self.addCleanup(
            self.nova, 'flavor-delete', params='resize-smaller-flavor')

        return 'resize-larger-flavor', 'resize-smaller-flavor'

    def test_resize_down_revert(self):
        """Tests creating a server and resizes down and reverts the resize.
        Compares quota before, during and after the resize.
        """
        # devstack's m1.tiny and m1.small have different size disks so we
        # can't use those as you can't resize down the disk. So we have to
        # create our own flavors.
        larger_flavor, smaller_flavor = self._create_resize_down_flavors()
        # Now create the server with the larger flavor.
        server_id = self._create_server('resize-down-revert', larger_flavor)
        # get the starting quota now that we've created a server
        starting_usage = self._get_absolute_limits()
        # now resize down
        self.nova('resize',
                  params='%s %s --poll' % (server_id, smaller_flavor))
        resize_usage = self._get_absolute_limits()
        # compare the starting usage against the resize usage; with counting
        # quotas in the server there are no reservations, so the
        # usage changes after the resize happens before it's confirmed.
        self._compare_quota_usage(starting_usage, resize_usage)
        # now revert the resize
        self.nova('resize-revert', params='%s' % server_id)
        # we have to wait for the server to be ACTIVE before we can check quota
        self._wait_for_state_change(server_id, 'active')
        # get the final quota usage which will be different from the resize
        # usage since we've reverted back *up* to the original flavor; the API
        # code checks quota again if we revert up in size
        revert_usage = self._get_absolute_limits()
        self._compare_quota_usage(resize_usage, revert_usage)

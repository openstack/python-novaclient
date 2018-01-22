# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
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

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes


class QuotaClassSetsTest(utils.TestCase):
    def setUp(self):
        super(QuotaClassSetsTest, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.0"))

    def test_class_quotas_get(self):
        class_name = 'test'
        q = self.cs.quota_classes.get(class_name)
        self.assert_request_id(q, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-quota-class-sets/%s' % class_name)
        return q

    def test_update_quota(self):
        q = self.cs.quota_classes.get('test')
        self.assert_request_id(q, fakes.FAKE_REQUEST_ID_LIST)
        q.update(cores=2)
        self.cs.assert_called('PUT', '/os-quota-class-sets/test')
        return q

    def test_refresh_quota(self):
        q = self.cs.quota_classes.get('test')
        q2 = self.cs.quota_classes.get('test')
        self.assertEqual(q.cores, q2.cores)
        q2.cores = 0
        self.assertNotEqual(q.cores, q2.cores)
        q2.get()
        self.assertEqual(q.cores, q2.cores)


class QuotaClassSetsTest2_50(QuotaClassSetsTest):
    """Tests the quota classes API binding using the 2.50 microversion."""
    api_version = '2.50'
    invalid_resources = ['floating_ips', 'fixed_ips', 'networks',
                         'security_groups', 'security_group_rules']

    def setUp(self):
        super(QuotaClassSetsTest2_50, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion(self.api_version))

    def test_class_quotas_get(self):
        """Tests that network-related resources aren't in a 2.50 response
        and server group related resources are in the response.
        """
        q = super(QuotaClassSetsTest2_50, self).test_class_quotas_get()
        for invalid_resource in self.invalid_resources:
            self.assertFalse(hasattr(q, invalid_resource),
                             '%s should not be in %s' % (invalid_resource, q))
        # Also make sure server_groups and server_group_members are in the
        # response.
        for valid_resource in ('server_groups', 'server_group_members'):
            self.assertTrue(hasattr(q, valid_resource),
                            '%s should be in %s' % (invalid_resource, q))

    def test_update_quota(self):
        """Tests that network-related resources aren't in a 2.50 response
        and server group related resources are in the response.
        """
        q = super(QuotaClassSetsTest2_50, self).test_update_quota()
        for invalid_resource in self.invalid_resources:
            self.assertFalse(hasattr(q, invalid_resource),
                             '%s should not be in %s' % (invalid_resource, q))
        # Also make sure server_groups and server_group_members are in the
        # response.
        for valid_resource in ('server_groups', 'server_group_members'):
            self.assertTrue(hasattr(q, valid_resource),
                            '%s should be in %s' % (invalid_resource, q))

    def test_update_quota_invalid_resources(self):
        """Tests trying to update quota class values for invalid resources.

        This will fail with TypeError because the network-related resource
        kwargs aren't defined.
        """
        q = self.cs.quota_classes.get('test')
        self.assertRaises(TypeError, q.update, floating_ips=1)
        self.assertRaises(TypeError, q.update, fixed_ips=1)
        self.assertRaises(TypeError, q.update, security_groups=1)
        self.assertRaises(TypeError, q.update, security_group_rules=1)
        self.assertRaises(TypeError, q.update, networks=1)
        return q


class QuotaClassSetsTest2_57(QuotaClassSetsTest2_50):
    """Tests the quota classes API binding using the 2.57 microversion."""
    api_version = '2.57'

    def setUp(self):
        super(QuotaClassSetsTest2_57, self).setUp()
        self.invalid_resources.extend(['injected_files',
                                       'injected_file_content_bytes',
                                       'injected_file_path_bytes'])

    def test_update_quota_invalid_resources(self):
        """Tests trying to update quota class values for invalid resources.

        This will fail with TypeError because the file-related resource
        kwargs aren't defined.
        """
        q = super(
            QuotaClassSetsTest2_57, self).test_update_quota_invalid_resources()
        self.assertRaises(TypeError, q.update, injected_files=1)
        self.assertRaises(TypeError, q.update, injected_file_content_bytes=1)
        self.assertRaises(TypeError, q.update, injected_file_path_bytes=1)

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

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


class QuotaSetsTest(utils.TestCase):
    def setUp(self):
        super(QuotaSetsTest, self).setUp()
        self.cs = self._get_fake_client()

    def _get_fake_client(self):
        return fakes.FakeClient()

    def test_tenant_quotas_get(self):
        tenant_id = 'test'
        self.cs.quotas.get(tenant_id)
        self.cs.assert_called('GET', '/os-quota-sets/%s' % tenant_id)

    def test_user_quotas_get(self):
        tenant_id = 'test'
        user_id = 'fake_user'
        self.cs.quotas.get(tenant_id, user_id=user_id)
        url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        self.cs.assert_called('GET', url)

    def test_tenant_quotas_defaults(self):
        tenant_id = '97f4c221bff44578b0300df4ef119353'
        self.cs.quotas.defaults(tenant_id)
        self.cs.assert_called('GET', '/os-quota-sets/%s/defaults' % tenant_id)

    def test_update_quota(self):
        q = self.cs.quotas.get('97f4c221bff44578b0300df4ef119353')
        q.update(volumes=2)
        self.cs.assert_called('PUT',
                   '/os-quota-sets/97f4c221bff44578b0300df4ef119353')

    def test_update_user_quota(self):
        tenant_id = '97f4c221bff44578b0300df4ef119353'
        user_id = 'fake_user'
        q = self.cs.quotas.get(tenant_id)
        q.update(volumes=2, user_id=user_id)
        url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        self.cs.assert_called('PUT', url)

    def test_force_update_quota(self):
        q = self.cs.quotas.get('97f4c221bff44578b0300df4ef119353')
        q.update(cores=2, force=True)
        self.cs.assert_called(
            'PUT', '/os-quota-sets/97f4c221bff44578b0300df4ef119353',
            {'quota_set': {'force': True,
                           'cores': 2,
                           'tenant_id': '97f4c221bff44578b0300df4ef119353'}})

    def test_refresh_quota(self):
        q = self.cs.quotas.get('test')
        q2 = self.cs.quotas.get('test')
        self.assertEqual(q.volumes, q2.volumes)
        q2.volumes = 0
        self.assertNotEqual(q.volumes, q2.volumes)
        q2.get()
        self.assertEqual(q.volumes, q2.volumes)

    def test_quotas_delete(self):
        tenant_id = 'test'
        self.cs.quotas.delete(tenant_id)
        self.cs.assert_called('DELETE', '/os-quota-sets/%s' % tenant_id)

    def test_user_quotas_delete(self):
        tenant_id = 'test'
        user_id = 'fake_user'
        self.cs.quotas.delete(tenant_id, user_id=user_id)
        url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        self.cs.assert_called('DELETE', url)

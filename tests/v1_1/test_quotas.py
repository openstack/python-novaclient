# Copyright 2011 OpenStack LLC.
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

from novaclient import exceptions
from novaclient.v1_1 import quotas
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class QuoatsTest(utils.TestCase):
    def test_list_quotas(self):
        qs = cs.quotas.list()
        cs.assert_called('GET', '/os-quotas')
        [self.assertTrue(isinstance(q, quotas.QuotaSet)) for q in qs]

    def test_delete_quota(self):
        q = cs.quotas.list()[0]
        q.delete()
        cs.assert_called('DELETE', '/os-quotas/test')
        cs.quotas.delete('test')
        cs.assert_called('DELETE', '/os-quotas/test')
        cs.quotas.delete(q)
        cs.assert_called('DELETE', '/os-quotas/test')

    def test_update_quota(self):
        q = cs.quotas.list()[0]
        q.update(volumes=2)
        cs.assert_called('PUT', '/os-quotas/test')

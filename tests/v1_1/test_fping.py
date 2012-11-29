# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC.
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
from novaclient.v1_1 import fping
from tests import utils
from tests.v1_1 import fakes


cs = fakes.FakeClient()


class FpingTest(utils.TestCase):

    def test_list_fpings(self):
        fl = cs.fping.list()
        cs.assert_called('GET', '/os-fping')
        [self.assertTrue(isinstance(f, fping.Fping)) for f in fl]
        [self.assertEqual(f.project_id, "fake-project") for f in fl]
        [self.assertEqual(f.alive, True) for f in fl]

    def test_get_fping(self):
        f = cs.fping.get(1)
        cs.assert_called('GET', '/os-fping/1')
        self.assertTrue(isinstance(f, fping.Fping))
        self.assertEqual(f.project_id, "fake-project")
        self.assertEqual(f.alive, True)

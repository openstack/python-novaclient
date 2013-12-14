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
from novaclient.v1_1 import keypairs


cs = fakes.FakeClient()


class KeypairsTest(utils.TestCase):

    def test_get_keypair(self):
        kp = cs.keypairs.get('test')
        cs.assert_called('GET', '/os-keypairs/test')
        self.assertTrue(isinstance(kp, keypairs.Keypair))
        self.assertEqual(kp.name, 'test')

    def test_list_keypairs(self):
        kps = cs.keypairs.list()
        cs.assert_called('GET', '/os-keypairs')
        [self.assertTrue(isinstance(kp, keypairs.Keypair)) for kp in kps]

    def test_delete_keypair(self):
        kp = cs.keypairs.list()[0]
        kp.delete()
        cs.assert_called('DELETE', '/os-keypairs/test')
        cs.keypairs.delete('test')
        cs.assert_called('DELETE', '/os-keypairs/test')
        cs.keypairs.delete(kp)
        cs.assert_called('DELETE', '/os-keypairs/test')

    def test_create_keypair(self):
        kp = cs.keypairs.create("foo")
        cs.assert_called('POST', '/os-keypairs')
        self.assertTrue(isinstance(kp, keypairs.Keypair))

    def test_import_keypair(self):
        kp = cs.keypairs.create("foo", "fake-public-key")
        cs.assert_called('POST', '/os-keypairs')
        self.assertTrue(isinstance(kp, keypairs.Keypair))

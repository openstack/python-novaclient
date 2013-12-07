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

from novaclient.v1_1 import certs
from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class FlavorsTest(utils.TestCase):

    def test_create_cert(self):
        cert = cs.certs.create()
        cs.assert_called('POST', '/os-certificates')
        self.assertTrue(isinstance(cert, certs.Certificate))

    def test_get_root_cert(self):
        cert = cs.certs.get()
        cs.assert_called('GET', '/os-certificates/root')
        self.assertTrue(isinstance(cert, certs.Certificate))

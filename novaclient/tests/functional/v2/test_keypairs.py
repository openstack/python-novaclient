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

from novaclient.tests.functional.v2 import fake_crypto
from novaclient.tests.functional.v2.legacy import test_keypairs


class TestKeypairsNovaClientV22(test_keypairs.TestKeypairsNovaClient):
    """Keypairs functional tests for v2.2 nova-api microversion.
    """

    COMPUTE_API_VERSION = "2.2"

    def test_create_keypair(self):
        keypair = super(TestKeypairsNovaClientV22, self).test_create_keypair()
        self.assertIn('ssh', keypair)

    def test_create_keypair_x509(self):
        key_name = self._create_keypair(key_type='x509')
        keypair = self._show_keypair(key_name)
        self.assertIn(key_name, keypair)
        self.assertIn('x509', keypair)

    def test_import_keypair(self):
        pub_key, fingerprint = fake_crypto.get_ssh_pub_key_and_fingerprint()
        pub_key_file = self._create_public_key_file(pub_key)
        keypair = self._test_import_keypair(fingerprint, pub_key=pub_key_file)
        self.assertIn('ssh', keypair)

    def test_import_keypair_x509(self):
        certif, fingerprint = fake_crypto.get_x509_cert_and_fingerprint()
        pub_key_file = self._create_public_key_file(certif)
        keypair = self._test_import_keypair(fingerprint, key_type='x509',
                                            pub_key=pub_key_file)
        self.assertIn('x509', keypair)

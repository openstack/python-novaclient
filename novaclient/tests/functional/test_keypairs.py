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

import tempfile
import uuid

from tempest_lib import exceptions

from novaclient.tests.functional import base
from novaclient.tests.functional import fake_crypto


class TestKeypairsNovaClient(base.ClientTestBase):
    """Keypairs functional tests.
    """

    def _serialize_kwargs(self, kwargs):
        kwargs_pairs = ['--%(key)s %(val)s' % {'key': key.replace('_', '-'),
                                               'val': val}
                        for key, val in kwargs.items()]
        return " ".join(kwargs_pairs)

    def _create_keypair(self, **kwargs):
        key_name = self._raw_create_keypair(**kwargs)
        self.addCleanup(self.nova, 'keypair-delete %s' % key_name)
        return key_name

    def _raw_create_keypair(self, **kwargs):
        key_name = 'keypair-' + str(uuid.uuid4())
        kwargs_str = self._serialize_kwargs(kwargs)
        self.nova('keypair-add %s %s' % (kwargs_str, key_name))
        return key_name

    def _show_keypair(self, key_name):
        return self.nova('keypair-show %s' % key_name)

    def _list_keypairs(self):
        return self.nova('keypair-list')

    def _delete_keypair(self, key_name):
        self.nova('keypair-delete %s' % key_name)

    def _create_public_key_file(self, public_key):
        pubfile = tempfile.mkstemp()[1]
        with open(pubfile, 'w') as f:
            f.write(public_key)
        return pubfile

    def test_create_keypair(self):
        key_name = self._create_keypair()
        keypair = self._show_keypair(key_name)
        self.assertIn(key_name, keypair)

        return keypair

    def _test_import_keypair(self, fingerprint, **create_kwargs):
        key_name = self._create_keypair(**create_kwargs)
        keypair = self._show_keypair(key_name)
        self.assertIn(key_name, keypair)
        self.assertIn(fingerprint, keypair)

        return keypair

    def test_import_keypair(self):
        pub_key, fingerprint = fake_crypto.get_ssh_pub_key_and_fingerprint()
        pub_key_file = self._create_public_key_file(pub_key)
        self._test_import_keypair(fingerprint, pub_key=pub_key_file)

    def test_list_keypair(self):
        key_name = self._create_keypair()
        keypairs = self._list_keypairs()
        self.assertIn(key_name, keypairs)

    def test_delete_keypair(self):
        key_name = self._raw_create_keypair()
        keypair = self._show_keypair(key_name)
        self.assertIsNotNone(keypair)

        self._delete_keypair(key_name)

        # keypair-show should fail if no keypair with given name is found.
        self.assertRaises(exceptions.CommandFailed,
                          self._show_keypair, key_name)


class TestKeypairsNovaClientV22(TestKeypairsNovaClient):
    """Keypairs functional tests for v2.2 nova-api microversion.
    """

    def nova(self, *args, **kwargs):
        return self.cli_clients.nova(flags='--os-compute-api-version 2.2 ',
                                     *args, **kwargs)

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

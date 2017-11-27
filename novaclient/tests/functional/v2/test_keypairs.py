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
from novaclient.tests.functional.v2 import fake_crypto
from novaclient.tests.functional.v2.legacy import test_keypairs


class TestKeypairsNovaClientV22(test_keypairs.TestKeypairsNovaClient):
    """Keypairs functional tests for v2.2 nova-api microversion."""

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


class TestKeypairsNovaClientV210(base.TenantTestBase):
    """Keypairs functional tests for v2.10 nova-api microversion."""

    COMPUTE_API_VERSION = "2.10"

    def test_create_and_list_keypair(self):
        name = self.name_generate()
        self.nova("keypair-add %s --user %s" % (name, self.user_id))
        self.addCleanup(self.another_nova, "keypair-delete %s" % name)
        output = self.nova("keypair-list")
        self.assertRaises(ValueError, self._get_value_from_the_table,
                          output, name)
        output_1 = self.another_nova("keypair-list")
        output_2 = self.nova("keypair-list --user %s" % self.user_id)
        self.assertEqual(output_1, output_2)
        # it should be table with one key-pair
        self.assertEqual(name, self._get_column_value_from_single_row_table(
            output_1, "Name"))

        output_1 = self.another_nova("keypair-show %s " % name)
        output_2 = self.nova("keypair-show --user %s %s" % (self.user_id,
                                                            name))
        self.assertEqual(output_1, output_2)
        self.assertEqual(self.user_id,
                         self._get_value_from_the_table(output_1, "user_id"))

    def test_create_and_delete(self):
        name = self.name_generate()

        def cleanup():
            # We should check keypair existence and remove it from correct user
            # if keypair is presented
            o = self.another_nova("keypair-list")
            if name in o:
                self.another_nova("keypair-delete %s" % name)

        self.nova("keypair-add %s --user %s" % (name, self.user_id))
        self.addCleanup(cleanup)
        output = self.another_nova("keypair-list")
        self.assertEqual(name, self._get_column_value_from_single_row_table(
            output, "Name"))

        self.nova("keypair-delete %s --user %s " % (name, self.user_id))
        output = self.another_nova("keypair-list")
        self.assertRaises(
            ValueError,
            self._get_column_value_from_single_row_table, output, "Name")


class TestKeypairsNovaClientV235(base.TenantTestBase):
    """Keypairs functional tests for v2.35 nova-api microversion."""

    COMPUTE_API_VERSION = "2.35"

    def test_create_and_list_keypair_with_marker_and_limit(self):
        names = []
        for i in range(3):
            names.append(self.name_generate())
            self.nova("keypair-add %s --user %s" % (names[i], self.user_id))
            self.addCleanup(self.another_nova, "keypair-delete %s" % names[i])

        # sort keypairs before pagination
        names = sorted(names)

        # list only one keypair after the first
        output_1 = self.another_nova("keypair-list --limit 1 --marker %s" %
                                     names[0])
        output_2 = self.nova("keypair-list --limit 1 --marker %s --user %s" %
                             (names[0], self.user_id))
        self.assertEqual(output_1, output_2)
        # it should be table with only one second key-pair
        self.assertEqual(
            names[1], self._get_column_value_from_single_row_table(output_1,
                                                                   "Name"))

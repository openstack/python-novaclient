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
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import keypairs as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import keypairs


class KeypairsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.V1

    def setUp(self):
        super(KeypairsTest, self).setUp()
        self.keypair_type = self._get_keypair_type()
        self.keypair_prefix = self._get_keypair_prefix()

    def _get_keypair_type(self):
        return keypairs.Keypair

    def _get_keypair_prefix(self):
        return keypairs.KeypairManager.keypair_prefix

    def test_get_keypair(self):
        kp = self.cs.keypairs.get('test')
        self.assert_request_id(kp, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/%s/test' % self.keypair_prefix)
        self.assertIsInstance(kp, keypairs.Keypair)
        self.assertEqual('test', kp.name)

    def test_list_keypairs(self):
        kps = self.cs.keypairs.list()
        self.assert_request_id(kps, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/%s' % self.keypair_prefix)
        for kp in kps:
            self.assertIsInstance(kp, keypairs.Keypair)

    def test_delete_keypair(self):
        kp = self.cs.keypairs.list()[0]
        ret = kp.delete()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/%s/test' % self.keypair_prefix)
        ret = self.cs.keypairs.delete('test')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/%s/test' % self.keypair_prefix)
        ret = self.cs.keypairs.delete(kp)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/%s/test' % self.keypair_prefix)


class KeypairsV2TestCase(KeypairsTest):
    def setUp(self):
        super(KeypairsV2TestCase, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.0")

    def test_create_keypair(self):
        name = "foo"
        kp = self.cs.keypairs.create(name)
        self.assert_request_id(kp, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/%s' % self.keypair_prefix,
                           body={'keypair': {'name': name}})
        self.assertIsInstance(kp, keypairs.Keypair)

    def test_import_keypair(self):
        name = "foo"
        pub_key = "fake-public-key"
        kp = self.cs.keypairs.create(name, pub_key)
        self.assert_request_id(kp, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/%s' % self.keypair_prefix,
                           body={'keypair': {'name': name,
                                             'public_key': pub_key}})
        self.assertIsInstance(kp, keypairs.Keypair)


class KeypairsV22TestCase(KeypairsTest):
    def setUp(self):
        super(KeypairsV22TestCase, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.2")

    def test_create_keypair(self):
        name = "foo"
        key_type = "some_type"
        kp = self.cs.keypairs.create(name, key_type=key_type)
        self.assert_request_id(kp, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/%s' % self.keypair_prefix,
                           body={'keypair': {'name': name,
                                             'type': key_type}})
        self.assertIsInstance(kp, keypairs.Keypair)

    def test_import_keypair(self):
        name = "foo"
        pub_key = "fake-public-key"
        kp = self.cs.keypairs.create(name, pub_key)
        self.assert_request_id(kp, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/%s' % self.keypair_prefix,
                           body={'keypair': {'name': name,
                                             'public_key': pub_key,
                                             'type': 'ssh'}})
        self.assertIsInstance(kp, keypairs.Keypair)


class KeypairsV35TestCase(KeypairsTest):
    def setUp(self):
        super(KeypairsV35TestCase, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.35")

    def test_list_keypairs(self):
        kps = self.cs.keypairs.list(user_id='test_user', marker='test_kp',
                                    limit=3)
        self.assert_request_id(kps, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET',
                           '/%s?limit=3&marker=test_kp&user_id=test_user'
                           % self.keypair_prefix)
        for kp in kps:
            self.assertIsInstance(kp, keypairs.Keypair)


class KeypairsV92TestCase(KeypairsTest):
    def setUp(self):
        super(KeypairsV92TestCase, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.92")

    def test_create_keypair(self):
        name = "foo"
        key_type = "some_type"
        public_key = "fake-public-key"
        kp = self.cs.keypairs.create(name, public_key=public_key,
                                     key_type=key_type)
        self.assert_request_id(kp, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/%s' % self.keypair_prefix,
                           body={'keypair': {'name': name,
                                             'public_key': public_key,
                                             'type': key_type}})
        self.assertIsInstance(kp, keypairs.Keypair)

    def test_create_keypair_without_pubkey(self):
        name = "foo"
        key_type = "some_type"
        self.assertRaises(TypeError,
                          self.cs.keypairs.create, name, key_type=key_type)

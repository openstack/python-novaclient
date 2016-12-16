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

import warnings

import mock

from novaclient import api_versions
from novaclient import exceptions
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import images as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import images


class ImagesTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.V1

    @mock.patch.object(warnings, 'warn')
    def test_list_images(self, mock_warn):
        il = self.cs.images.list()
        self.assert_request_id(il, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/images/detail')
        for i in il:
            self.assertIsInstance(i, images.Image)
        self.assertEqual(2, len(il))
        self.assertEqual(1, mock_warn.call_count)

    def test_list_images_undetailed(self):
        il = self.cs.images.list(detailed=False)
        self.assert_request_id(il, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/images')
        for i in il:
            self.assertIsInstance(i, images.Image)

    def test_list_images_with_marker_limit(self):
        il = self.cs.images.list(marker=1234, limit=4)
        self.assert_request_id(il, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/images/detail?limit=4&marker=1234')

    @mock.patch.object(warnings, 'warn')
    def test_get_image_details(self, mock_warn):
        i = self.cs.images.get(1)
        self.assert_request_id(i, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/images/1')
        self.assertIsInstance(i, images.Image)
        self.assertEqual(1, i.id)
        self.assertEqual('CentOS 5.2', i.name)
        self.assertEqual(1, mock_warn.call_count)

    @mock.patch.object(warnings, 'warn')
    def test_delete_image(self, mock_warn):
        i = self.cs.images.delete(1)
        self.assert_request_id(i, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/images/1')
        self.assertEqual(1, mock_warn.call_count)

    @mock.patch.object(warnings, 'warn')
    def test_delete_meta(self, mock_warn):
        i = self.cs.images.delete_meta(1, {'test_key': 'test_value'})
        self.assert_request_id(i, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/images/1/metadata/test_key')
        self.assertEqual(1, mock_warn.call_count)

    @mock.patch.object(warnings, 'warn')
    def test_set_meta(self, mock_warn):
        i = self.cs.images.set_meta(1, {'test_key': 'test_value'})
        self.assert_request_id(i, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/images/1/metadata',
                           {"metadata": {'test_key': 'test_value'}})
        self.assertEqual(1, mock_warn.call_count)

    @mock.patch.object(warnings, 'warn')
    def test_find(self, mock_warn):
        i = self.cs.images.find(name="CentOS 5.2")
        self.assert_request_id(i, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(1, i.id)
        self.assert_called('GET', '/images/1')
        # This is two warnings because find calls findall which calls list
        # which is the first warning, which finds one results and then calls
        # get on that, which is the second warning.
        self.assertEqual(2, mock_warn.call_count)

        iml = self.cs.images.findall(status='SAVING')
        self.assert_request_id(iml, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(1, len(iml))
        self.assertEqual('My Server Backup', iml[0].name)

    def test_find_2_36(self):
        """Tests that using the find method fails after microversion 2.35.
        """
        self.cs.api_version = api_versions.APIVersion('2.36')
        self.assertRaises(exceptions.VersionNotFoundForAPIMethod,
                          self.cs.images.find, name="CentOS 5.2")

    def test_delete_meta_2_39(self):
        """Tests that 'delete_meta' method fails after microversion 2.39.
        """
        self.cs.api_version = api_versions.APIVersion('2.39')
        self.assertRaises(exceptions.VersionNotFoundForAPIMethod,
                          self.cs.images.delete_meta, 1,
                          {'test_key': 'test_value'})

    def test_set_meta_2_39(self):
        """Tests that 'set_meta' method fails after microversion 2.39.
        """
        self.cs.api_version = api_versions.APIVersion('2.39')
        self.assertRaises(exceptions.VersionNotFoundForAPIMethod,
                          self.cs.images.set_meta, 1,
                          {'test_key': 'test_value'})

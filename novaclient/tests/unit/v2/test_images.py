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

import mock

from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import images as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import images


class ImagesTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.V1

    @mock.patch('novaclient.base.Manager.alternate_service_type')
    def test_list_images(self, mock_alternate_service_type):
        il = self.cs.glance.list()
        self.assert_request_id(il, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/v2/images')
        for i in il:
            self.assertIsInstance(i, images.Image)
        self.assertEqual(2, len(il))
        mock_alternate_service_type.assert_called_once_with(
            'image', allowed_types=('image',))

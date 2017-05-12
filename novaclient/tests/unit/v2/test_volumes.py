# Copyright 2013 IBM Corp.
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

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import volumes


class VolumesTest(utils.TestCase):
    def setUp(self):
        super(VolumesTest, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.0"))

    def test_create_server_volume(self):
        v = self.cs.volumes.create_server_volume(
            server_id=1234,
            volume_id='15e59938-07d5-11e1-90e3-e3dffe0c5983',
            device='/dev/vdb'
        )
        self.assert_request_id(v, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('POST', '/servers/1234/os-volume_attachments')
        self.assertIsInstance(v, volumes.Volume)

    def test_update_server_volume(self):
        vol_id = '15e59938-07d5-11e1-90e3-e3dffe0c5983'
        v = self.cs.volumes.update_server_volume(
            server_id=1234,
            src_volid='Work',
            dest_volid=vol_id
        )
        self.assert_request_id(v, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('PUT',
                              '/servers/1234/os-volume_attachments/Work')
        self.assertIsInstance(v, volumes.Volume)

    def test_get_server_volume(self):
        v = self.cs.volumes.get_server_volume(1234, 'Work')
        self.assert_request_id(v, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET',
                              '/servers/1234/os-volume_attachments/Work')
        self.assertIsInstance(v, volumes.Volume)

    def test_list_server_volumes(self):
        vl = self.cs.volumes.get_server_volumes(1234)
        self.assert_request_id(vl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET',
                              '/servers/1234/os-volume_attachments')
        for v in vl:
            self.assertIsInstance(v, volumes.Volume)

    def test_delete_server_volume(self):
        ret = self.cs.volumes.delete_server_volume(1234, 'Work')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('DELETE',
                              '/servers/1234/os-volume_attachments/Work')

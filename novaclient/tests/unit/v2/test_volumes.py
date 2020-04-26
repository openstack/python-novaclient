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

from unittest import mock

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import volumes


class VolumesTest(utils.TestCase):
    api_version = "2.0"

    def setUp(self):
        super(VolumesTest, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion(self.api_version))

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

    def test_get_server_volume_with_exception(self):
        self.assertRaises(TypeError,
                          self.cs.volumes.get_server_volume,
                          "1234")

        self.assertRaises(TypeError,
                          self.cs.volumes.get_server_volume,
                          "1234",
                          volume_id="Work",
                          attachment_id="123")

    @mock.patch('warnings.warn')
    def test_get_server_volume_with_warn(self, mock_warn):
        self.cs.volumes.get_server_volume(1234,
                                          volume_id=None,
                                          attachment_id="Work")
        mock_warn.assert_called_once()

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


class VolumesV249Test(VolumesTest):
    api_version = "2.49"

    def test_create_server_volume_with_tag(self):
        v = self.cs.volumes.create_server_volume(
            server_id=1234,
            volume_id='15e59938-07d5-11e1-90e3-e3dffe0c5983',
            device='/dev/vdb',
            tag='test_tag'
        )
        self.assert_request_id(v, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called(
            'POST', '/servers/1234/os-volume_attachments',
            {'volumeAttachment': {
                'volumeId': '15e59938-07d5-11e1-90e3-e3dffe0c5983',
                'device': '/dev/vdb',
                'tag': 'test_tag'}})
        self.assertIsInstance(v, volumes.Volume)

    def test_delete_server_volume_with_exception(self):
        self.assertRaises(TypeError,
                          self.cs.volumes.delete_server_volume,
                          "1234")

        self.assertRaises(TypeError,
                          self.cs.volumes.delete_server_volume,
                          "1234",
                          volume_id="Work",
                          attachment_id="123")

    @mock.patch('warnings.warn')
    def test_delete_server_volume_with_warn(self, mock_warn):
        self.cs.volumes.delete_server_volume(1234,
                                             volume_id=None,
                                             attachment_id="Work")
        mock_warn.assert_called_once()


class VolumesV279Test(VolumesV249Test):
    api_version = "2.79"

    def test_create_server_volume_with_delete_on_termination(self):
        v = self.cs.volumes.create_server_volume(
            server_id=1234,
            volume_id='15e59938-07d5-11e1-90e3-e3dffe0c5983',
            device='/dev/vdb',
            tag='tag1',
            delete_on_termination=True
        )
        self.assert_request_id(v, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called(
            'POST', '/servers/1234/os-volume_attachments',
            {'volumeAttachment': {
                'volumeId': '15e59938-07d5-11e1-90e3-e3dffe0c5983',
                'device': '/dev/vdb',
                'tag': 'tag1',
                'delete_on_termination': True}})
        self.assertIsInstance(v, volumes.Volume)

    def test_create_server_volume_with_delete_on_termination_pre_v279(self):
        self.cs.api_version = api_versions.APIVersion('2.78')
        ex = self.assertRaises(
            TypeError, self.cs.volumes.create_server_volume, "1234",
            volume_id='15e59938-07d5-11e1-90e3-e3dffe0c5983',
            delete_on_termination=True)
        self.assertIn('delete_on_termination', str(ex))


class VolumesV285Test(VolumesV279Test):
    api_version = "2.85"

    def test_volume_update_server_volume(self):
        v = self.cs.volumes.update_server_volume(
            server_id=1234,
            src_volid='Work',
            dest_volid='Work',
            delete_on_termination=True
        )
        self.assert_request_id(v, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('PUT',
                              '/servers/1234/os-volume_attachments/Work')
        self.assertIsInstance(v, volumes.Volume)

    def test_volume_update_server_volume_pre_v285(self):
        self.cs.api_version = api_versions.APIVersion('2.84')
        ex = self.assertRaises(
            TypeError, self.cs.volumes.update_server_volume, "1234",
            'Work', 'Work', delete_on_termination=True)
        self.assertIn('delete_on_termination', str(ex))

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
import six

from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import cloudpipe as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import cloudpipe


class CloudpipeTest(utils.FixturedTestCase):

    data_fixture_class = data.Fixture

    scenarios = [('original', {'client_fixture_class': client.V1}),
                 ('session', {'client_fixture_class': client.SessionV1})]

    @mock.patch('warnings.warn')
    def test_list_cloudpipes(self, mock_warn):
        cp = self.cs.cloudpipe.list()
        self.assert_request_id(cp, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-cloudpipe')
        for c in cp:
            self.assertIsInstance(c, cloudpipe.Cloudpipe)
        mock_warn.assert_called_once_with(mock.ANY)

    @mock.patch('warnings.warn')
    def test_create(self, mock_warn):
        project = "test"
        cp = self.cs.cloudpipe.create(project)
        self.assert_request_id(cp, fakes.FAKE_REQUEST_ID_LIST)
        body = {'cloudpipe': {'project_id': project}}
        self.assert_called('POST', '/os-cloudpipe', body)
        self.assertIsInstance(cp, six.string_types)
        mock_warn.assert_called_once_with(mock.ANY)

    @mock.patch('warnings.warn')
    def test_update(self, mock_warn):
        cp = self.cs.cloudpipe.update("192.168.1.1", 2345)
        self.assert_request_id(cp, fakes.FAKE_REQUEST_ID_LIST)
        body = {'configure_project': {'vpn_ip': "192.168.1.1",
                                      'vpn_port': 2345}}
        self.assert_called('PUT', '/os-cloudpipe/configure-project', body)
        mock_warn.assert_called_once_with(mock.ANY)

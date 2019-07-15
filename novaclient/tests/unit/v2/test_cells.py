# Copyright 2013 Rackspace Hosting
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

import mock

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes

CELL_V1_DEPRECATION_WARNING = (
    'The cells v1 interface has been deprecated in Nova since 16.0.0 Pike '
    'Release. This API binding will be removed in the first major release '
    'after the Nova server 20.0.0 Train release.')


@mock.patch('warnings.warn')
class CellsExtensionTests(utils.TestCase):
    def setUp(self):
        super(CellsExtensionTests, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.1"))

    def test_get_cells(self, mock_warn):
        cell_name = 'child_cell'
        cell = self.cs.cells.get(cell_name)
        self.assert_request_id(cell, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-cells/%s' % cell_name)
        mock_warn.assert_called_once_with(CELL_V1_DEPRECATION_WARNING,
                                          DeprecationWarning)

    def test_get_capacities_for_a_given_cell(self, mock_warn):
        cell_name = 'child_cell'
        ca = self.cs.cells.capacities(cell_name)
        self.assert_request_id(ca, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-cells/%s/capacities' % cell_name)
        mock_warn.assert_called_once_with(CELL_V1_DEPRECATION_WARNING,
                                          DeprecationWarning)

    def test_get_capacities_for_all_cells(self, mock_warn):
        ca = self.cs.cells.capacities()
        self.assert_request_id(ca, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-cells/capacities')
        mock_warn.assert_called_once_with(CELL_V1_DEPRECATION_WARNING,
                                          DeprecationWarning)

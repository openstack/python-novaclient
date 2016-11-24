# Copyright 2013 Hewlett-Packard Development Company, L.P.
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


import warnings

import mock

from novaclient import api_versions
from novaclient import extension
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2.contrib import baremetal


@mock.patch.object(warnings, 'warn')
class BaremetalExtensionTest(utils.TestCase):
    def setUp(self):
        super(BaremetalExtensionTest, self).setUp()
        extensions = [
            extension.Extension(baremetal.__name__.split(".")[-1], baremetal),
        ]
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.0"),
                                   extensions=extensions)

    def test_list_nodes(self, mock_warn):
        nl = self.cs.baremetal.list()
        self.assert_request_id(nl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-baremetal-nodes')
        for n in nl:
            self.assertIsInstance(n, baremetal.BareMetalNode)
        self.assertEqual(1, mock_warn.call_count)

    def test_get_node(self, mock_warn):
        n = self.cs.baremetal.get(1)
        self.assert_request_id(n, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-baremetal-nodes/1')
        self.assertIsInstance(n, baremetal.BareMetalNode)
        self.assertEqual(1, mock_warn.call_count)

    def test_node_list_interfaces(self, mock_warn):
        il = self.cs.baremetal.list_interfaces(1)
        self.assert_request_id(il, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-baremetal-nodes/1')
        self.assertEqual(1, mock_warn.call_count)

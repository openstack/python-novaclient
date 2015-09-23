# Copyright 2015 IBM Corp.
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

from novaclient.tests.functional.v2.legacy import test_fixedips


class TestFixedIPsNovaClientV24(test_fixedips.TestFixedIPsNovaClient):
    """FixedIPs functional tests for v2.4 nova-api microversion."""

    COMPUTE_API_VERSION = '2.4'

    def test_fixedip_get(self):
        self._test_fixedip_get(expect_reserved=True)

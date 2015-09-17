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

from oslo_utils import strutils

from novaclient.tests.functional import base
from novaclient.v2 import shell


class TestFixedIPsNovaClient(base.ClientTestBase):
    """FixedIPs functional tests."""

    API_VERSION = '2.1'

    def nova(self, *args, **kwargs):
        flags = '--os-compute-api-version %s ' % self.API_VERSION
        return self.cli_clients.nova(flags=flags, *args, **kwargs)

    def _create_server(self):
        name = self.name_generate(prefix='server')
        server = self.client.servers.create(name, self.image, self.flavor)
        shell._poll_for_status(
            self.client.servers.get, server.id,
            'building', ['active'])
        self.addCleanup(server.delete)
        return server

    def _test_fixedip_get(self, expect_reserved=False):
        server = self._create_server()
        networks = server.networks
        self.assertIn('private', networks)
        fixed_ip = networks['private'][0]
        table = self.nova('fixed-ip-get %s' % fixed_ip)
        addr = self._get_column_value_from_single_row_table(table, 'address')
        self.assertEqual(fixed_ip, addr)
        if expect_reserved:
            reserved = self._get_column_value_from_single_row_table(table,
                                                                    'reserved')
            # By default the fixed IP should not be reserved.
            self.assertEqual(False, strutils.bool_from_string(reserved,
                                                              strict=True))
        else:
            self.assertRaises(ValueError,
                              self._get_column_value_from_single_row_table,
                              table, 'reserved')

    def test_fixedip_get(self):
        self._test_fixedip_get()


class TestFixedIPsNovaClientV24(TestFixedIPsNovaClient):
    """FixedIPs functional tests for v2.4 nova-api microversion."""

    API_VERSION = '2.4'

    def test_fixedip_get(self):
        self._test_fixedip_get(expect_reserved=True)

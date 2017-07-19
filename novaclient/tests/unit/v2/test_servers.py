# -*- coding: utf-8 -*-
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

import base64
import os
import tempfile

import mock
import six

from novaclient import api_versions
from novaclient import base
from novaclient import exceptions
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import floatingips
from novaclient.tests.unit.fixture_data import servers as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import servers


class _FloatingIPManager(base.Manager):
    resource_class = base.Resource

    @api_versions.deprecated_after('2.35')
    def list(self):
        """DEPRECATED: List floating IPs"""
        return self._list("/os-floating-ips", "floating_ips")

    @api_versions.deprecated_after('2.35')
    def get(self, floating_ip):
        """DEPRECATED: Retrieve a floating IP"""
        return self._get("/os-floating-ips/%s" % base.getid(floating_ip),
                         "floating_ip")


class ServersTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.V1
    api_version = None

    def setUp(self):
        super(ServersTest, self).setUp()
        self.useFixture(floatingips.FloatingFixture(self.requests_mock))
        if self.api_version:
            self.cs.api_version = api_versions.APIVersion(self.api_version)
        self.floating_ips = _FloatingIPManager(self.cs)

    def _get_server_create_default_nics(self):
        """Callback for default nics kwarg when creating a server.
        """
        return None

    def test_list_servers(self):
        sl = self.cs.servers.list()
        self.assert_request_id(sl, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers/detail')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_filter_servers_unicode(self):
        sl = self.cs.servers.list(search_opts={'name': u't€sting'})
        self.assert_request_id(sl, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers/detail?name=t%E2%82%ACsting')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_all_servers(self):
        # use marker just to identify this call in fixtures
        sl = self.cs.servers.list(limit=-1, marker=1234)
        self.assert_request_id(sl, fakes.FAKE_REQUEST_ID_LIST)

        self.assertEqual(2, len(sl))

        self.assertEqual(self.requests_mock.request_history[-2].method, 'GET')
        self.assertEqual(self.requests_mock.request_history[-2].path_url,
                         '/servers/detail?marker=1234')
        self.assert_called('GET', '/servers/detail?marker=5678')

        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_servers_undetailed(self):
        sl = self.cs.servers.list(detailed=False)
        self.assert_request_id(sl, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_servers_with_marker_limit(self):
        sl = self.cs.servers.list(marker=1234, limit=2)
        self.assert_request_id(sl, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers/detail?limit=2&marker=1234')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_servers_sort_single(self):
        sl = self.cs.servers.list(sort_keys=['display_name'],
                                  sort_dirs=['asc'])
        self.assert_request_id(sl, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called(
            'GET',
            '/servers/detail?sort_dir=asc&sort_key=display_name')
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_list_servers_sort_multiple(self):
        sl = self.cs.servers.list(sort_keys=['display_name', 'id'],
                                  sort_dirs=['asc', 'desc'])
        self.assert_request_id(sl, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called(
            'GET',
            ('/servers/detail?sort_dir=asc&sort_dir=desc&'
             'sort_key=display_name&sort_key=id'))
        for s in sl:
            self.assertIsInstance(s, servers.Server)

    def test_get_server_details(self):
        s = self.cs.servers.get(1234)
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers/1234')
        self.assertIsInstance(s, servers.Server)
        self.assertEqual(1234, s.id)
        self.assertEqual('BUILD', s.status)

    def test_get_server_promote_details(self):
        s1 = self.cs.servers.list(detailed=False)[0]
        s2 = self.cs.servers.list(detailed=True)[0]
        self.assertNotEqual(s1._info, s2._info)
        s1.get()
        self.assertEqual(s1._info, s2._info)

    def test_create_server(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata="hello moto",
            key_name="fakekey",
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': six.StringIO('data'),   # a stream
            },
            nics=self._get_server_create_default_nics()
        )
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_boot_from_volume_with_nics(self):
        old_boot = self.cs.servers._boot

        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                 'v4-fixed-ip': '10.0.0.7'}]
        bdm = {"volume_size": "1",
               "volume_id": "11111111-1111-1111-1111-111111111111",
               "delete_on_termination": "0",
               "device_name": "vda"}

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(boot_kwargs['block_device_mapping'], bdm)
            self.assertEqual(boot_kwargs['nics'], nics)
            return old_boot(url, key, *boot_args, **boot_kwargs)

        @mock.patch.object(self.cs.servers, '_boot', wrapped_boot)
        def test_create_server_from_volume():
            s = self.cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                block_device_mapping=bdm,
                nics=nics
            )
            self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
            self.assert_called('POST', '/os-volumes_boot')
            self.assertIsInstance(s, servers.Server)

        test_create_server_from_volume()

    def test_create_server_boot_from_volume_bdm_v2(self):
        old_boot = self.cs.servers._boot

        bdm = [{"volume_size": "1",
                "volume_id": "11111111-1111-1111-1111-111111111111",
                "delete_on_termination": "0",
                "device_name": "vda"}]

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(boot_kwargs['block_device_mapping_v2'], bdm)
            return old_boot(url, key, *boot_args, **boot_kwargs)

        with mock.patch.object(self.cs.servers, '_boot', wrapped_boot):
            s = self.cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                block_device_mapping_v2=bdm,
                nics=self._get_server_create_default_nics()
            )
            self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
            self.assert_called('POST', '/os-volumes_boot')
            self.assertIsInstance(s, servers.Server)

    def test_create_server_boot_with_nics_ipv6(self):
        old_boot = self.cs.servers._boot
        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                'v6-fixed-ip': '2001:db9:0:1::10'}]

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(boot_kwargs['nics'], nics)
            return old_boot(url, key, *boot_args, **boot_kwargs)

        with mock.patch.object(self.cs.servers, '_boot', wrapped_boot):
            s = self.cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                nics=nics
            )
            self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
            self.assert_called('POST', '/servers')
            self.assertIsInstance(s, servers.Server)

    def test_create_server_boot_with_address(self):
        old_boot = self.cs.servers._boot
        access_ip_v6 = '::1'
        access_ip_v4 = '10.10.10.10'

        def wrapped_boot(url, key, *boot_args, **boot_kwargs):
            self.assertEqual(boot_kwargs['access_ip_v6'], access_ip_v6)
            self.assertEqual(boot_kwargs['access_ip_v4'], access_ip_v4)
            return old_boot(url, key, *boot_args, **boot_kwargs)

        with mock.patch.object(self.cs.servers, '_boot', wrapped_boot):
            s = self.cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata="hello moto",
                key_name="fakekey",
                access_ip_v6=access_ip_v6,
                access_ip_v4=access_ip_v4,
                nics=self._get_server_create_default_nics()
            )
            self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
            self.assert_called('POST', '/servers')
            self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_file_object(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata=six.StringIO('hello moto'),
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': six.StringIO('data'),   # a stream
            },
            nics=self._get_server_create_default_nics(),
        )
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_unicode(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata=six.u('こんにちは'),
            key_name="fakekey",
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': six.StringIO('data'),   # a stream
            },
            nics=self._get_server_create_default_nics(),
        )
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_userdata_utf8(self):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata='こんにちは',
            key_name="fakekey",
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': six.StringIO('data'),   # a stream
            },
            nics=self._get_server_create_default_nics(),
        )
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_create_server_admin_pass(self):
        test_password = "test-pass"
        test_key = "fakekey"
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            admin_pass=test_password,
            key_name=test_key,
            nics=self._get_server_create_default_nics()
        )
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)
        body = self.requests_mock.last_request.json()
        self.assertEqual(test_password, body['server']['adminPass'])

    def test_create_server_userdata_bin(self):
        with tempfile.TemporaryFile(mode='wb+') as bin_file:
            original_data = os.urandom(1024)
            bin_file.write(original_data)
            bin_file.flush()
            bin_file.seek(0)
            s = self.cs.servers.create(
                name="My server",
                image=1,
                flavor=1,
                meta={'foo': 'bar'},
                userdata=bin_file,
                key_name="fakekey",
                files={
                    '/etc/passwd': 'some data',                 # a file
                    '/tmp/foo.txt': six.StringIO('data'),   # a stream
                },
                nics=self._get_server_create_default_nics(),
            )
            self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
            self.assert_called('POST', '/servers')
            self.assertIsInstance(s, servers.Server)
            # verify userdata matches original
            body = self.requests_mock.last_request.json()
            transferred_data = body['server']['user_data']
            transferred_data = base64.b64decode(transferred_data)
            self.assertEqual(original_data, transferred_data)

    def _create_disk_config(self, disk_config):
        s = self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            disk_config=disk_config,
            nics=self._get_server_create_default_nics(),
        )
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

        # verify disk config param was used in the request:
        server = self.requests_mock.last_request.json()['server']
        self.assertIn('OS-DCF:diskConfig', server)
        self.assertEqual(disk_config, server['OS-DCF:diskConfig'])

    def test_create_server_disk_config_auto(self):
        self._create_disk_config('AUTO')

    def test_create_server_disk_config_manual(self):
        self._create_disk_config('MANUAL')

    def test_update_server(self):
        s = self.cs.servers.get(1234)

        # Update via instance
        s.update(name='hi')
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/servers/1234')
        s.update(name='hi')
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/servers/1234')

        # Silly, but not an error
        s.update()

        # Update via manager
        self.cs.servers.update(s, name='hi')
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/servers/1234')

    def test_delete_server(self):
        s = self.cs.servers.get(1234)
        ret = s.delete()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/servers/1234')
        ret = self.cs.servers.delete(1234)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/servers/1234')
        ret = self.cs.servers.delete(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/servers/1234')

    def test_delete_server_meta(self):
        ret = self.cs.servers.delete_meta(1234, ['test_key'])
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/servers/1234/metadata/test_key')

    def test_set_server_meta(self):
        m = self.cs.servers.set_meta(1234, {'test_key': 'test_value'})
        self.assert_request_id(m, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/metadata',
                           {'metadata': {'test_key': 'test_value'}})

    def test_set_server_meta_item(self):
        m = self.cs.servers.set_meta_item(1234, 'test_key', 'test_value')
        self.assert_request_id(m, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/servers/1234/metadata/test_key',
                           {'meta': {'test_key': 'test_value'}})

    def test_find(self):
        server = self.cs.servers.find(name='sample-server')
        self.assert_request_id(server, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers/1234')
        self.assertEqual('sample-server', server.name)

        self.assertRaises(exceptions.NoUniqueMatch, self.cs.servers.find,
                          flavor={"id": 1, "name": "256 MB Server"})

        sl = self.cs.servers.findall(flavor={"id": 1, "name": "256 MB Server"})
        self.assert_request_id(sl, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual([1234, 5678, 9012], [s.id for s in sl])

    def test_reboot_server(self):
        s = self.cs.servers.get(1234)
        ret = s.reboot()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.reboot(s, reboot_type='HARD')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_rebuild_server(self):
        s = self.cs.servers.get(1234)
        ret = s.rebuild(image=1)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.rebuild(s, image=1)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = s.rebuild(image=1, password='5678')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.rebuild(s, image=1, password='5678')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def _rebuild_resize_disk_config(self, disk_config, operation="rebuild"):
        s = self.cs.servers.get(1234)

        if operation == "rebuild":
            ret = s.rebuild(image=1, disk_config=disk_config)
        elif operation == "resize":
            ret = s.resize(flavor=1, disk_config=disk_config)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

        # verify disk config param was used in the request:
        d = self.requests_mock.last_request.json()[operation]
        self.assertIn('OS-DCF:diskConfig', d)
        self.assertEqual(disk_config, d['OS-DCF:diskConfig'])

    def test_rebuild_server_disk_config_auto(self):
        self._rebuild_resize_disk_config('AUTO')

    def test_rebuild_server_disk_config_manual(self):
        self._rebuild_resize_disk_config('MANUAL')

    def test_rebuild_server_preserve_ephemeral(self):
        s = self.cs.servers.get(1234)
        ret = s.rebuild(image=1, preserve_ephemeral=True)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        d = self.requests_mock.last_request.json()['rebuild']
        self.assertIn('preserve_ephemeral', d)
        self.assertTrue(d['preserve_ephemeral'])

    def test_rebuild_server_name_meta_files(self):
        files = {'/etc/passwd': 'some data'}
        s = self.cs.servers.get(1234)
        ret = s.rebuild(image=1, name='new', meta={'foo': 'bar'}, files=files)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        d = self.requests_mock.last_request.json()['rebuild']
        self.assertEqual('new', d['name'])
        self.assertEqual({'foo': 'bar'}, d['metadata'])
        self.assertEqual('/etc/passwd',
                         d['personality'][0]['path'])

    def test_resize_server(self):
        s = self.cs.servers.get(1234)
        ret = s.resize(flavor=1)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.resize(s, flavor=1)
        self.assert_called('POST', '/servers/1234/action')

    def test_resize_server_disk_config_auto(self):
        self._rebuild_resize_disk_config('AUTO', 'resize')

    def test_resize_server_disk_config_manual(self):
        self._rebuild_resize_disk_config('MANUAL', 'resize')

    def test_confirm_resized_server(self):
        s = self.cs.servers.get(1234)
        ret = s.confirm_resize()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.confirm_resize(s)
        self.assert_called('POST', '/servers/1234/action')

    def test_revert_resized_server(self):
        s = self.cs.servers.get(1234)
        ret = s.revert_resize()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.revert_resize(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_migrate_server(self):
        s = self.cs.servers.get(1234)
        ret = s.migrate()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.migrate(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    @mock.patch('warnings.warn')
    def test_add_fixed_ip(self, mock_warn):
        s = self.cs.servers.get(1234)
        fip = s.add_fixed_ip(1)
        mock_warn.assert_called_once()
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        fip = self.cs.servers.add_fixed_ip(s, 1)
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    @mock.patch('warnings.warn')
    def test_remove_fixed_ip(self, mock_warn):
        s = self.cs.servers.get(1234)
        ret = s.remove_fixed_ip('10.0.0.1')
        mock_warn.assert_called_once()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.remove_fixed_ip(s, '10.0.0.1')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    @mock.patch('warnings.warn')
    def test_add_floating_ip(self, mock_warn):
        s = self.cs.servers.get(1234)
        fip = s.add_floating_ip('11.0.0.1')
        mock_warn.assert_called_once()
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        fip = self.cs.servers.add_floating_ip(s, '11.0.0.1')
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        f = self.floating_ips.list()[0]
        fip = self.cs.servers.add_floating_ip(s, f)
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        fip = s.add_floating_ip(f)
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_add_floating_ip_to_fixed(self):
        s = self.cs.servers.get(1234)
        fip = s.add_floating_ip('11.0.0.1', fixed_address='12.0.0.1')
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        fip = self.cs.servers.add_floating_ip(s, '11.0.0.1',
                                              fixed_address='12.0.0.1')
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        f = self.floating_ips.list()[0]
        fip = self.cs.servers.add_floating_ip(s, f)
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        fip = s.add_floating_ip(f)
        self.assert_request_id(fip, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    @mock.patch('warnings.warn')
    def test_remove_floating_ip(self, mock_warn):
        s = self.cs.servers.get(1234)
        ret = s.remove_floating_ip('11.0.0.1')
        mock_warn.assert_called_once()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.remove_floating_ip(s, '11.0.0.1')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        f = self.floating_ips.list()[0]
        ret = self.cs.servers.remove_floating_ip(s, f)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = s.remove_floating_ip(f)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_stop(self):
        s = self.cs.servers.get(1234)
        ret = s.stop()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.stop(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_force_delete(self):
        s = self.cs.servers.get(1234)
        ret = s.force_delete()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.force_delete(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_restore(self):
        s = self.cs.servers.get(1234)
        ret = s.restore()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.restore(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_start(self):
        s = self.cs.servers.get(1234)
        ret = s.start()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.start(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_rescue(self):
        s = self.cs.servers.get(1234)
        ret = s.rescue()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.rescue(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_rescue_password(self):
        s = self.cs.servers.get(1234)
        ret = s.rescue(password='asdf')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'rescue': {'adminPass': 'asdf'}})
        ret = self.cs.servers.rescue(s, password='asdf')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'rescue': {'adminPass': 'asdf'}})

    def test_rescue_image(self):
        s = self.cs.servers.get(1234)
        ret = s.rescue(image=1)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'rescue': {'rescue_image_ref': 1}})
        ret = self.cs.servers.rescue(s, image=1)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'rescue': {'rescue_image_ref': 1}})

    def test_unrescue(self):
        s = self.cs.servers.get(1234)
        ret = s.unrescue()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.unrescue(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_lock(self):
        s = self.cs.servers.get(1234)
        ret = s.lock()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.lock(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_unlock(self):
        s = self.cs.servers.get(1234)
        ret = s.unlock()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.unlock(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_backup(self):
        s = self.cs.servers.get(1234)
        sb = s.backup('back1', 'daily', 1)
        self.assert_request_id(sb, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        sb = self.cs.servers.backup(s, 'back1', 'daily', 2)
        self.assert_request_id(sb, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_get_console_output_without_length(self):
        success = 'foo'
        s = self.cs.servers.get(1234)
        co = s.get_console_output()
        self.assert_request_id(co, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(success, s.get_console_output())
        self.assert_called('POST', '/servers/1234/action')

        co = self.cs.servers.get_console_output(s)
        self.assert_request_id(co, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(success, self.cs.servers.get_console_output(s))
        self.assert_called('POST', '/servers/1234/action')

    def test_get_console_output_with_length(self):
        success = 'foo'

        s = self.cs.servers.get(1234)
        co = s.get_console_output(length=50)
        self.assert_request_id(co, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(success, s.get_console_output(length=50))
        self.assert_called('POST', '/servers/1234/action')

        co = self.cs.servers.get_console_output(s, length=50)
        self.assert_request_id(co, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(success,
                         self.cs.servers.get_console_output(s, length=50))
        self.assert_called('POST', '/servers/1234/action')

    # Testing password methods with the following password and key
    #
    # Clear password: FooBar123
    #
    # RSA Private Key: novaclient/tests/unit/idfake.pem
    #
    # Encrypted password
    # OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r
    # qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho
    # QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw
    # /y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N
    # tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk
    # Hi/fmZZNQQqj1Ijq0caOIw==

    def test_get_password(self):
        s = self.cs.servers.get(1234)
        password = s.get_password('novaclient/tests/unit/idfake.pem')
        self.assert_request_id(password, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(b'FooBar123', password)
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_get_password_without_key(self):
        s = self.cs.servers.get(1234)
        password = s.get_password()
        self.assert_request_id(password, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual(
            'OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r'
            'qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho'
            'QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw'
            '/y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N'
            'tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk'
            'Hi/fmZZNQQqj1Ijq0caOIw==', password)
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_clear_password(self):
        s = self.cs.servers.get(1234)
        ret = s.clear_password()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/servers/1234/os-server-password')

    def test_get_server_diagnostics(self):
        s = self.cs.servers.get(1234)
        diagnostics = s.diagnostics()
        self.assert_request_id(diagnostics, fakes.FAKE_REQUEST_ID_LIST)
        self.assertIsNotNone(diagnostics)
        self.assert_called('GET', '/servers/1234/diagnostics')

        diagnostics_from_manager = self.cs.servers.diagnostics(1234)
        self.assert_request_id(diagnostics_from_manager,
                               fakes.FAKE_REQUEST_ID_LIST)
        self.assertIsNotNone(diagnostics_from_manager)
        self.assert_called('GET', '/servers/1234/diagnostics')

        self.assertEqual(diagnostics[1], diagnostics_from_manager[1])

    def test_get_vnc_console(self):
        s = self.cs.servers.get(1234)
        vc = s.get_vnc_console('novnc')
        self.assert_request_id(vc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

        vc = self.cs.servers.get_vnc_console(s, 'novnc')
        self.assert_request_id(vc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_get_spice_console(self):
        s = self.cs.servers.get(1234)
        sc = s.get_spice_console('spice-html5')
        self.assert_request_id(sc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

        sc = self.cs.servers.get_spice_console(s, 'spice-html5')
        self.assert_request_id(sc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_get_serial_console(self):
        s = self.cs.servers.get(1234)
        sc = s.get_serial_console('serial')
        self.assert_request_id(sc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

        sc = self.cs.servers.get_serial_console(s, 'serial')
        self.assert_request_id(sc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_get_rdp_console(self):
        s = self.cs.servers.get(1234)
        rc = s.get_rdp_console('rdp-html5')
        self.assert_request_id(rc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

        rc = self.cs.servers.get_rdp_console(s, 'rdp-html5')
        self.assert_request_id(rc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_get_console_url(self):
        s = self.cs.servers.get(1234)
        rc = s.get_console_url('novnc')
        self.assert_request_id(rc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

        rc = self.cs.servers.get_console_url(s, 'novnc')
        self.assert_request_id(rc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

        # test the case with invalid console type
        self.assertRaises(exceptions.UnsupportedConsoleType,
                          s.get_console_url,
                          'invalid')

    def test_create_image(self):
        s = self.cs.servers.get(1234)
        im = s.create_image('123')
        self.assert_request_id(im, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        im = s.create_image('123', {})
        self.assert_request_id(im, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        im = self.cs.servers.create_image(s, '123')
        self.assert_request_id(im, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        im = self.cs.servers.create_image(s, '123', {})
        self.assert_request_id(im, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_live_migrate_server(self):
        s = self.cs.servers.get(1234)
        ret = s.live_migrate(host='hostname', block_migration=False,
                             disk_over_commit=False)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': False,
                                               'disk_over_commit': False}})
        ret = self.cs.servers.live_migrate(s, host='hostname',
                                           block_migration=False,
                                           disk_over_commit=False)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': False,
                                               'disk_over_commit': False}})

    def test_live_migrate_server_block_migration_none(self):
        s = self.cs.servers.get(1234)
        ret = s.live_migrate(host='hostname', block_migration=None,
                             disk_over_commit=None)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': False,
                                               'disk_over_commit': False}})

    def test_reset_state(self):
        s = self.cs.servers.get(1234)
        ret = s.reset_state('newstate')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.reset_state(s, 'newstate')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_reset_network(self):
        s = self.cs.servers.get(1234)
        ret = s.reset_network()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.reset_network(s)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_add_security_group(self):
        s = self.cs.servers.get(1234)
        sg = s.add_security_group('newsg')
        self.assert_request_id(sg, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        sg = self.cs.servers.add_security_group(s, 'newsg')
        self.assert_request_id(sg, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_remove_security_group(self):
        s = self.cs.servers.get(1234)
        ret = s.remove_security_group('oldsg')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.remove_security_group(s, 'oldsg')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_list_security_group(self):
        s = self.cs.servers.get(1234)
        sgs = s.list_security_group()
        self.assert_request_id(sgs, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers/1234/os-security-groups')

    def test_evacuate(self):
        s = self.cs.servers.get(1234)
        ret = s.evacuate('fake_target_host', 'True')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        ret = self.cs.servers.evacuate(s, 'fake_target_host',
                                          'False', 'NewAdminPassword')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_interface_list(self):
        s = self.cs.servers.get(1234)
        il = s.interface_list()
        self.assert_request_id(il, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers/1234/os-interface')

    def test_interface_list_result_string_representable(self):
        """Test for bugs.launchpad.net/python-novaclient/+bug/1280453."""
        # According to https://github.com/openstack/nova/blob/master/
        # nova/api/openstack/compute/contrib/attach_interfaces.py#L33,
        # the attach_interface extension get method will return a json
        # object partly like this:
        interface_list = [{
            'net_id': 'd7745cf5-63f9-4883-b0ae-983f061e4f23',
            'port_id': 'f35079da-36d5-4513-8ec1-0298d703f70e',
            'mac_addr': 'fa:16:3e:4c:37:c8',
            'port_state': 'ACTIVE',
            'fixed_ips': [
                {
                    'subnet_id': 'f1ad93ad-2967-46ba-b403-e8cbbe65f7fa',
                    'ip_address': '10.2.0.96'
                }]
        }]
        # If server is not string representable, it will raise an exception,
        # because attribute named 'name' cannot be found.
        # Parameter 'loaded' must be True or it will try to get attribute
        # 'id' then fails (lazy load detail), this is exactly same as
        # novaclient.base.Manager._list()
        s = servers.Server(servers.ServerManager, interface_list[0],
                           loaded=True)
        # Trigger the __repr__ magic method
        self.assertEqual('<Server: unknown-name>', '%r' % s)

    def test_interface_attach(self):
        s = self.cs.servers.get(1234)
        ret = s.interface_attach(None, None, None)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/os-interface')

    def test_interface_detach(self):
        s = self.cs.servers.get(1234)
        ret = s.interface_detach('port-id')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/servers/1234/os-interface/port-id')

    def test_create_server_with_description(self):
        self.assertRaises(exceptions.UnsupportedAttribute,
                          self.cs.servers.create,
                          name="My server",
                          description="descr",
                          image=1,
                          flavor=1,
                          meta={'foo': 'bar'},
                          userdata="hello moto",
                          key_name="fakekey"
                          )

    def test_create_server_with_nics_auto(self):
        """Negative test for specifying nics='auto' before 2.37
        """
        self.assertRaises(ValueError,
                          self.cs.servers.create,
                          name='test',
                          image='d9d8d53c-4b4a-4144-a5e5-b30d9f1fe46a',
                          flavor='1',
                          nics='auto')


class ServersV26Test(ServersTest):

    api_version = "2.6"

    def test_get_vnc_console(self):
        s = self.cs.servers.get(1234)
        vc = s.get_vnc_console('novnc')
        self.assert_request_id(vc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        vc = self.cs.servers.get_vnc_console(s, 'novnc')
        self.assert_request_id(vc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        # test the case with invalid console type
        self.assertRaises(exceptions.UnsupportedConsoleType,
                          s.get_vnc_console,
                          'invalid')

    def test_get_spice_console(self):
        s = self.cs.servers.get(1234)
        sc = s.get_spice_console('spice-html5')
        self.assert_request_id(sc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        sc = self.cs.servers.get_spice_console(s, 'spice-html5')
        self.assert_request_id(sc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        # test the case with invalid console type
        self.assertRaises(exceptions.UnsupportedConsoleType,
                          s.get_spice_console,
                          'invalid')

    def test_get_serial_console(self):
        s = self.cs.servers.get(1234)
        sc = s.get_serial_console('serial')
        self.assert_request_id(sc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        sc = self.cs.servers.get_serial_console(s, 'serial')
        self.assert_request_id(sc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        # test the case with invalid console type
        self.assertRaises(exceptions.UnsupportedConsoleType,
                          s.get_serial_console,
                          'invalid')

    def test_get_rdp_console(self):
        s = self.cs.servers.get(1234)
        rc = s.get_rdp_console('rdp-html5')
        self.assert_request_id(rc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        rc = self.cs.servers.get_rdp_console(s, 'rdp-html5')
        self.assert_request_id(rc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        # test the case with invalid console type
        self.assertRaises(exceptions.UnsupportedConsoleType,
                          s.get_rdp_console,
                          'invalid')

    def test_get_console_url(self):
        s = self.cs.servers.get(1234)
        vc = s.get_console_url('novnc')
        self.assert_request_id(vc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        vc = self.cs.servers.get_console_url(s, 'novnc')
        self.assert_request_id(vc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        # test the case with invalid console type
        self.assertRaises(exceptions.UnsupportedConsoleType,
                          s.get_console_url,
                          'invalid')
        # console type webmks is supported since api version 2.8
        self.assertRaises(exceptions.UnsupportedConsoleType,
                          s.get_console_url,
                          'webmks')


class ServersV28Test(ServersV26Test):

    api_version = "2.8"

    def test_get_mks_console(self):
        s = self.cs.servers.get(1234)
        mksc = s.get_mks_console()
        self.assert_request_id(mksc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        mksc = self.cs.servers.get_mks_console(s)
        self.assert_request_id(mksc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

    def test_get_console_url(self):
        s = self.cs.servers.get(1234)
        mksc = s.get_console_url('novnc')
        self.assert_request_id(mksc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        mksc = self.cs.servers.get_console_url(s, 'novnc')
        self.assert_request_id(mksc, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/remote-consoles')

        # test the case with invalid console type
        self.assertRaises(exceptions.UnsupportedConsoleType,
                          s.get_console_url,
                          'invalid')


class ServersV214Test(ServersV28Test):

    api_version = "2.14"

    def test_evacuate(self):
        s = self.cs.servers.get(1234)
        s.evacuate('fake_target_host')
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.evacuate(s, 'fake_target_host',
                                 password='NewAdminPassword')
        self.assert_called('POST', '/servers/1234/action')


class ServersV217Test(ServersV214Test):

    api_version = "2.17"

    def test_trigger_crash_dump(self):
        s = self.cs.servers.get(1234)
        s.trigger_crash_dump()
        self.assert_called('POST', '/servers/1234/action')
        self.cs.servers.trigger_crash_dump(s)
        self.assert_called('POST', '/servers/1234/action')


class ServersV219Test(ServersV217Test):

    api_version = "2.19"

    def test_create_server_with_description(self):
        self.cs.servers.create(
            name="My server",
            description="descr",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata="hello moto",
            key_name="fakekey",
            nics=self._get_server_create_default_nics()
        )
        self.assert_called('POST', '/servers')

    def test_update_server_with_description(self):
        s = self.cs.servers.get(1234)

        s.update(description='hi')
        s.update(name='hi', description='hi')
        self.assert_called('PUT', '/servers/1234')

    def test_rebuild_with_description(self):
        s = self.cs.servers.get(1234)

        ret = s.rebuild(image="1", description="descr")
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')


class ServersV225Test(ServersV219Test):

    api_version = "2.25"

    def test_live_migrate_server(self):
        s = self.cs.servers.get(1234)
        ret = s.live_migrate(host='hostname', block_migration='auto')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto'}})
        ret = self.cs.servers.live_migrate(s, host='hostname',
                                           block_migration='auto')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto'}})

    def test_live_migrate_server_block_migration_true(self):
        s = self.cs.servers.get(1234)
        ret = s.live_migrate(host='hostname', block_migration=True)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': True}})

        ret = self.cs.servers.live_migrate(s, host='hostname',
                                           block_migration=True)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': True}})

    def test_live_migrate_server_block_migration_none(self):
        s = self.cs.servers.get(1234)
        ret = s.live_migrate(host='hostname', block_migration=None)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto'}})

        ret = self.cs.servers.live_migrate(s, host='hostname',
                                           block_migration='auto')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto'}})


class ServersV226Test(ServersV225Test):

    api_version = "2.26"

    def test_tag_list(self):
        s = self.cs.servers.get(1234)
        ret = s.tag_list()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/servers/1234/tags')

    def test_tag_delete(self):
        s = self.cs.servers.get(1234)
        ret = s.delete_tag('tag')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/servers/1234/tags/tag')

    def test_tag_delete_all(self):
        s = self.cs.servers.get(1234)
        ret = s.delete_all_tags()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/servers/1234/tags')

    def test_tag_add(self):
        s = self.cs.servers.get(1234)
        ret = s.add_tag('tag')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/servers/1234/tags/tag')

    def test_tags_set(self):
        s = self.cs.servers.get(1234)
        ret = s.set_tags(['tag1', 'tag2'])
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/servers/1234/tags')


class ServersV229Test(ServersV226Test):

    api_version = "2.29"

    def test_evacuate(self):
        s = self.cs.servers.get(1234)
        s.evacuate('fake_target_host')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'fake_target_host'}})
        self.cs.servers.evacuate(s, 'fake_target_host', force=True)
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'fake_target_host',
                                         'force': True}})


class ServersV230Test(ServersV229Test):

    api_version = "2.30"

    def test_live_migrate_server(self):
        s = self.cs.servers.get(1234)
        ret = s.live_migrate(host='hostname', block_migration='auto')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto'}})
        ret = self.cs.servers.live_migrate(s, host='hostname',
                                           block_migration='auto',
                                           force=True)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto',
                                               'force': True}})


class ServersV232Test(ServersV226Test):

    api_version = "2.32"

    def test_create_server_boot_with_tagged_nics(self):
        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                 'tag': 'one'},
                {'net-id': '22222222-2222-2222-2222-222222222222',
                 'tag': 'two'}]
        self.cs.servers.create(name="Server with tagged nics",
                               image=1,
                               flavor=1,
                               nics=nics)
        self.assert_called('POST', '/servers')

    def test_create_server_boot_with_tagged_nics_pre232(self):
        self.cs.api_version = api_versions.APIVersion("2.31")
        nics = [{'net-id': '11111111-1111-1111-1111-111111111111',
                 'tag': 'one'},
                {'net-id': '22222222-2222-2222-2222-222222222222',
                 'tag': 'two'}]
        self.assertRaises(ValueError, self.cs.servers.create,
                          name="Server with tagged nics", image=1, flavor=1,
                          nics=nics)

    def test_create_server_boot_from_volume_tagged_bdm_v2(self):
        bdm = [{"volume_size": "1",
                "volume_id": "11111111-1111-1111-1111-111111111111",
                "delete_on_termination": "0",
                "device_name": "vda", "tag": "foo"}]
        s = self.cs.servers.create(name="My server", image=1, flavor=1,
                                   meta={'foo': 'bar'}, userdata="hello moto",
                                   key_name="fakekey",
                                   block_device_mapping_v2=bdm)
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-volumes_boot')

    def test_create_server_boot_from_volume_tagged_bdm_v2_pre232(self):
        self.cs.api_version = api_versions.APIVersion("2.31")
        bdm = [{"volume_size": "1",
                "volume_id": "11111111-1111-1111-1111-111111111111",
                "delete_on_termination": "0",
                "device_name": "vda", "tag": "foo"}]
        self.assertRaises(ValueError, self.cs.servers.create, name="My server",
                          image=1, flavor=1, meta={'foo': 'bar'},
                          userdata="hello moto", key_name="fakekey",
                          block_device_mapping_v2=bdm)


class ServersV2_37Test(ServersV226Test):

    api_version = "2.37"

    def _get_server_create_default_nics(self):
        return 'auto'

    def test_create_server_no_nics(self):
        """Tests that nics are required in microversion 2.37+
        """
        self.assertRaises(ValueError, self.cs.servers.create,
                          name='test',
                          image='d9d8d53c-4b4a-4144-a5e5-b30d9f1fe46a',
                          flavor='1')

    def test_create_server_with_nics_auto(self):
        s = self.cs.servers.create(
            name='test', image='d9d8d53c-4b4a-4144-a5e5-b30d9f1fe46a',
            flavor='1', nics=self._get_server_create_default_nics())
        self.assert_request_id(s, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers')
        self.assertIsInstance(s, servers.Server)

    def test_add_floating_ip(self):
        # self.floating_ips.list() is not available after 2.35
        pass

    def test_add_floating_ip_to_fixed(self):
        # self.floating_ips.list() is not available after 2.35
        pass

    def test_remove_floating_ip(self):
        # self.floating_ips.list() is not available after 2.35
        pass


class ServersCreateImageBackupV2_45Test(utils.FixturedTestCase):
    """Tests the 2.45 microversion for createImage and createBackup
    server actions.
    """

    client_fixture_class = client.V1
    data_fixture_class = data.V1
    api_version = '2.45'

    def setUp(self):
        super(ServersCreateImageBackupV2_45Test, self).setUp()
        self.cs.api_version = api_versions.APIVersion(self.api_version)

    def test_create_image(self):
        """Tests the createImage API with the 2.45 microversion which
        does not return the Location header, it returns a json dict in the
        response body with an image_id key.
        """
        s = self.cs.servers.get(1234)
        im = s.create_image('123')
        self.assertEqual('456', im)
        self.assert_request_id(im, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        im = s.create_image('123', {})
        self.assert_request_id(im, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        im = self.cs.servers.create_image(s, '123')
        self.assert_request_id(im, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        im = self.cs.servers.create_image(s, '123', {})
        self.assert_request_id(im, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')

    def test_backup(self):
        s = self.cs.servers.get(1234)
        # Test backup on the Server object.
        sb = s.backup('back1', 'daily', 1)
        self.assertIn('image_id', sb)
        self.assertEqual('456', sb['image_id'])
        self.assert_request_id(sb, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')
        # Test backup on the ServerManager.
        sb = self.cs.servers.backup(s, 'back1', 'daily', 2)
        self.assertEqual('456', sb['image_id'])
        self.assert_request_id(sb, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/servers/1234/action')


class ServersV249Test(ServersV2_37Test):

    api_version = "2.49"

    def test_interface_attach_with_tag(self):
        s = self.cs.servers.get(1234)
        ret = s.interface_attach('7f42712e-63fe-484c-a6df-30ae4867ff66',
                                 None, None, 'test_tag')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called(
            'POST', '/servers/1234/os-interface',
            {'interfaceAttachment':
                {'port_id': '7f42712e-63fe-484c-a6df-30ae4867ff66',
                 'tag': 'test_tag'}})

    def test_add_fixed_ip(self):
        # novaclient.v2.servers.Server.add_fixed_ip()
        # is not available after 2.44
        pass

    def test_remove_fixed_ip(self):
        # novaclient.v2.servers.Server.remove_fixed_ip()
        # is not available after 2.44
        pass


class ServersV252Test(ServersV249Test):

    api_version = "2.52"

    def test_create_server_with_tags(self):
        self.cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata="hello moto",
            key_name="fakekey",
            nics=self._get_server_create_default_nics(),
            tags=['tag1', 'tag2']
        )
        self.assert_called('POST', '/servers',
                           {'server': {
                               'flavorRef': '1',
                               'imageRef': '1',
                               'key_name': 'fakekey',
                               'max_count': 1,
                               'metadata': {'foo': 'bar'},
                               'min_count': 1,
                               'name': 'My server',
                               'networks': 'auto',
                               'tags': ['tag1', 'tag2'],
                               'user_data': 'aGVsbG8gbW90bw=='
                           }}
                           )

    def test_create_server_with_tags_pre_252_fails(self):
        self.cs.api_version = api_versions.APIVersion('2.51')
        self.assertRaises(exceptions.UnsupportedAttribute,
                          self.cs.servers.create,
                          name="My server",
                          image=1,
                          flavor=1,
                          meta={'foo': 'bar'},
                          userdata="hello moto",
                          key_name="fakekey",
                          nics=self._get_server_create_default_nics(),
                          tags=['tag1', 'tag2'])

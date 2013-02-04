# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack LLC.
# Copyright 2012 IBM Corp.
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

import datetime
import os
import mock
import sys
import tempfile

import fixtures

import novaclient.shell
import novaclient.client
from novaclient import exceptions
from novaclient.openstack.common import timeutils
from tests.v1_1 import fakes
from tests import utils


class ShellFixture(fixtures.Fixture):

    def setUp(self):
        super(ShellFixture, self).setUp()
        self.shell = novaclient.shell.OpenStackComputeShell()

    def tearDown(self):
        # For some method like test_image_meta_bad_action we are
        # testing a SystemExit to be thrown and object self.shell has
        # no time to get instantatiated which is OK in this case, so
        # we make sure the method is there before launching it.
        if hasattr(self.shell, 'cs'):
            self.shell.cs.clear_callstack()
        super(ShellFixture, self).tearDown()


class ShellTest(utils.TestCase):

    FAKE_ENV = {
        'NOVA_USERNAME': 'username',
        'NOVA_PASSWORD': 'password',
        'NOVA_PROJECT_ID': 'project_id',
        'OS_COMPUTE_API_VERSION': '1.1',
        'NOVA_URL': 'http://no.where',
    }

    def setUp(self):
        """Run before each test."""
        super(ShellTest, self).setUp()

        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))
        self.shell = self.useFixture(ShellFixture()).shell

        self.useFixture(fixtures.MonkeyPatch(
            'novaclient.client.get_client_class',
            lambda *_: fakes.FakeClient))
        self.addCleanup(timeutils.clear_time_override)

    def run_command(self, cmd):
        self.shell.main(cmd.split())

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test_agents_list_with_hypervisor(self):
        self.run_command('agent-list --hypervisor xen')
        self.assert_called('GET', '/os-agents?hypervisor=xen')

    def test_agents_create(self):
        self.run_command('agent-create win x86 7.0 '
                         '/xxx/xxx/xxx '
                         'add6bb58e139be103324d04d82d8f546 '
                         'kvm')
        self.assert_called(
            'POST', '/os-agents',
            {'agent': {
                     'hypervisor': 'kvm',
                     'os': 'win',
                     'architecture': 'x86',
                     'version': '7.0',
                     'url': '/xxx/xxx/xxx',
                     'md5hash': 'add6bb58e139be103324d04d82d8f546'}})

    def test_agents_delete(self):
        self.run_command('agent-delete 1')
        self.assert_called('DELETE', '/os-agents/1')

    def test_agents_modify(self):
        self.run_command('agent-modify 1 8.0 /yyy/yyyy/yyyy '
                         'add6bb58e139be103324d04d82d8f546')
        self.assert_called('PUT', '/os-agents/1',
                          {"para": {
                               "url": "/yyy/yyyy/yyyy",
                               "version": "8.0",
                               "md5hash": "add6bb58e139be103324d04d82d8f546"}})

    def test_boot(self):
        self.run_command('boot --flavor 1 --image 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                }},
        )

    def test_boot_image_with(self):
        self.run_command("boot --flavor 1"
                         " --image-with test_key=test_value some-server")
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                }},
        )

    def test_boot_no_image_no_bdms(self):
        cmd = 'boot --flavor 1 some-server'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_no_image_bdms(self):
        self.run_command(
            'boot --flavor 1 --block_device_mapping vda=blah:::0 some-server'
        )
        self.assert_called_anytime(
            'POST', '/os-volumes_boot',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping': [
                    {
                        'volume_size': '',
                        'volume_id': 'blah',
                        'delete_on_termination': '0',
                        'device_name':'vda'
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
                }},
        )

    def test_boot_metadata(self):
        self.run_command('boot --image 1 --flavor 1 --meta foo=bar=pants'
                         ' --meta spam=eggs some-server ')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'metadata': {'foo': 'bar=pants', 'spam': 'eggs'},
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_hints(self):
        self.run_command('boot --image 1 --flavor 1 --hint a=b=c some-server ')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 1,
                },
                'os:scheduler_hints': {'a': 'b=c'},
            },
        )

    def test_boot_nics(self):
        cmd = ('boot --image 1 --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=10.0.0.1 some-server')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 1,
                    'networks': [
                        {'uuid': 'a=c', 'fixed_ip': '10.0.0.1'},
                    ],
                },
            },
        )

    def test_boot_files(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        expected_file_data = open(testfile).read().encode('base64')

        cmd = 'boot some-server --flavor 1 --image 1 ' \
              '--file /tmp/foo=%s --file /tmp/bar=%s'
        self.run_command(cmd % (testfile, testfile))

        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                'personality': [
                   {'path': '/tmp/bar', 'contents': expected_file_data},
                   {'path': '/tmp/foo', 'contents': expected_file_data},
                ]},
            },
        )

    def test_boot_invalid_file(self):
        invalid_file = os.path.join(os.path.dirname(__file__),
                                    'asdfasdfasdfasdf')
        cmd = 'boot some-server --image 1 --file /foo=%s' % invalid_file
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_num_instances(self):
        self.run_command('boot --image 1 --flavor 1 --num-instances 3 server')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 3,
                }
            })

    def test_boot_invalid_num_instances(self):
        cmd = 'boot --image 1 --flavor 1 --num-instances 1  server'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_flavor_list(self):
        self.run_command('flavor-list')
        self.assert_called('GET', '/flavors/aa1/os-extra_specs')
        self.assert_called_anytime('GET', '/flavors/detail')

    def test_flavor_show(self):
        self.run_command('flavor-show 1')
        self.assert_called_anytime('GET', '/flavors/1')

    def test_flavor_show_with_alphanum_id(self):
        self.run_command('flavor-show aa1')
        self.assert_called_anytime('GET', '/flavors/aa1')

    def test_image_show(self):
        self.run_command('image-show 1')
        self.assert_called('GET', '/images/1')

    def test_image_meta_set(self):
        self.run_command('image-meta 1 set test_key=test_value')
        self.assert_called('POST', '/images/1/metadata',
            {'metadata': {'test_key': 'test_value'}})

    def test_image_meta_del(self):
        self.run_command('image-meta 1 delete test_key=test_value')
        self.assert_called('DELETE', '/images/1/metadata/test_key')

    def test_image_meta_bad_action(self):
        tmp = tempfile.TemporaryFile()

        # Suppress stdout and stderr
        (stdout, stderr) = (sys.stdout, sys.stderr)
        (sys.stdout, sys.stderr) = (tmp, tmp)

        self.assertRaises(SystemExit, self.run_command,
                          'image-meta 1 BAD_ACTION test_key=test_value')

        # Put stdout and stderr back
        sys.stdout, sys.stderr = (stdout, stderr)

    def test_image_list(self):
        self.run_command('image-list')
        self.assert_called('GET', '/images/detail')

    def test_create_image(self):
        self.run_command('image-create sample-server mysnapshot')
        self.assert_called(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot', 'metadata': {}}},
        )

    def test_image_delete(self):
        self.run_command('image-delete 1')
        self.assert_called('DELETE', '/images/1')

    def test_list(self):
        self.run_command('list')
        self.assert_called('GET', '/servers/detail')

    def test_reboot(self):
        self.run_command('reboot sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'reboot': {'type': 'SOFT'}})
        self.run_command('reboot sample-server --hard')
        self.assert_called('POST', '/servers/1234/action',
                           {'reboot': {'type': 'HARD'}})

    def test_rebuild(self):
        self.run_command('rebuild sample-server 1')
        # XXX need a way to test multiple calls
        #self.assert_called('POST', '/servers/1234/action',
        #                   {'rebuild': {'imageRef': 1}})
        self.assert_called('GET', '/images/2')

        self.run_command('rebuild sample-server 1 --rebuild-password asdf')
        # XXX need a way to test multiple calls
        #self.assert_called('POST', '/servers/1234/action',
        #                   {'rebuild': {'imageRef': 1, 'adminPass': 'asdf'}})
        self.assert_called('GET', '/images/2')

    def test_rename(self):
        self.run_command('rename sample-server newname')
        self.assert_called('PUT', '/servers/1234',
                           {'server': {'name': 'newname'}})

    def test_resize(self):
        self.run_command('resize sample-server 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'resize': {'flavorRef': 1}})

    def test_resize_confirm(self):
        self.run_command('resize-confirm sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'confirmResize': None})

    def test_resize_revert(self):
        self.run_command('resize-revert sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'revertResize': None})

    @mock.patch('getpass.getpass', mock.Mock(return_value='p'))
    def test_root_password(self):
        self.run_command('root-password sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'changePassword': {'adminPass': 'p'}})

    def test_scrub(self):
        self.run_command('scrub 4ffc664c198e435e9853f2538fbcd7a7')
        self.assert_called('GET', '/os-networks', pos=-4)
        self.assert_called('GET', '/os-security-groups?all_tenants=1',
                          pos=-3)
        self.assert_called('POST', '/os-networks/1/action',
                           {"disassociate": None}, pos=-2)
        self.assert_called('DELETE', '/os-security-groups/1')

    def test_show(self):
        self.run_command('show 1234')
        self.assert_called('GET', '/servers/1234', pos=-3)
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/images/2')

    def test_show_no_image(self):
        self.run_command('show 9012')
        self.assert_called('GET', '/servers/9012', pos=-2)
        self.assert_called('GET', '/flavors/1', pos=-1)

    def test_show_bad_id(self):
        self.assertRaises(exceptions.CommandError,
                          self.run_command, 'show xxx')

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/servers/1234')
        self.run_command('delete sample-server')
        self.assert_called('DELETE', '/servers/1234')

    def test_diagnostics(self):
        self.run_command('diagnostics 1234')
        self.assert_called('GET', '/servers/1234/diagnostics')
        self.run_command('diagnostics sample-server')
        self.assert_called('GET', '/servers/1234/diagnostics')

    def test_actions(self):
        self.run_command('actions 1234')
        self.assert_called('GET', '/servers/1234/actions')
        self.run_command('actions sample-server')
        self.assert_called('GET', '/servers/1234/actions')

    def test_set_meta_set(self):
        self.run_command('meta 1234 set key1=val1 key2=val2')
        self.assert_called('POST', '/servers/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_set_meta_delete_dict(self):
        self.run_command('meta 1234 delete key1=val1 key2=val2')
        self.assert_called('DELETE', '/servers/1234/metadata/key1')
        self.assert_called('DELETE', '/servers/1234/metadata/key2', pos=-2)

    def test_set_meta_delete_keys(self):
        self.run_command('meta 1234 delete key1 key2')
        self.assert_called('DELETE', '/servers/1234/metadata/key1')
        self.assert_called('DELETE', '/servers/1234/metadata/key2', pos=-2)

    def test_dns_create(self):
        self.run_command('dns-create 192.168.1.1 testname testdomain')
        self.assert_called('PUT',
                           '/os-floating-ip-dns/testdomain/entries/testname')

        self.run_command('dns-create 192.168.1.1 testname testdomain --type A')
        self.assert_called('PUT',
                           '/os-floating-ip-dns/testdomain/entries/testname')

    def test_dns_create_public_domain(self):
        self.run_command('dns-create-public-domain testdomain '
                         '--project test_project')
        self.assert_called('PUT', '/os-floating-ip-dns/testdomain')

    def test_dns_create_private_domain(self):
        self.run_command('dns-create-private-domain testdomain '
                         '--availability-zone av_zone')
        self.assert_called('PUT', '/os-floating-ip-dns/testdomain')

    def test_dns_delete(self):
        self.run_command('dns-delete testdomain testname')
        self.assert_called('DELETE',
                           '/os-floating-ip-dns/testdomain/entries/testname')

    def test_dns_delete_domain(self):
        self.run_command('dns-delete-domain testdomain')
        self.assert_called('DELETE', '/os-floating-ip-dns/testdomain')

    def test_dns_list(self):
        self.run_command('dns-list testdomain --ip 192.168.1.1')
        self.assert_called('GET',
                       '/os-floating-ip-dns/testdomain/entries?ip=192.168.1.1')

        self.run_command('dns-list testdomain --name testname')
        self.assert_called('GET',
                           '/os-floating-ip-dns/testdomain/entries/testname')

    def test_dns_domains(self):
        self.run_command('dns-domains')
        self.assert_called('GET', '/os-floating-ip-dns')

    def test_floating_ip_bulk_list(self):
        self.run_command('floating-ip-bulk-list')
        self.assert_called('GET', '/os-floating-ips-bulk')

    def test_floating_ip_bulk_create(self):
        self.run_command('floating-ip-bulk-create 10.0.0.1/24')
        self.assert_called('POST', '/os-floating-ips-bulk',
                           {'floating_ips_bulk_create':
                                {'ip_range': '10.0.0.1/24'}})

    def test_floating_ip_bulk_create_host_and_interface(self):
        self.run_command('floating-ip-bulk-create 10.0.0.1/24 --pool testPool \
                         --interface ethX')
        self.assert_called('POST', '/os-floating-ips-bulk',
                           {'floating_ips_bulk_create':
                                {'ip_range': '10.0.0.1/24',
                                 'pool': 'testPool', 'interface': 'ethX'}})

    def test_floating_ip_bulk_delete(self):
        self.run_command('floating-ip-bulk-delete 10.0.0.1/24')
        self.assert_called('PUT', '/os-floating-ips-bulk/delete',
                                {'ip_range': '10.0.0.1/24'})

    def test_usage_list(self):
        self.run_command('usage-list --start 2000-01-20 --end 2005-02-01')
        self.assert_called('GET',
                           '/os-simple-tenant-usage?' +
                           'start=2000-01-20T00:00:00&' +
                           'end=2005-02-01T00:00:00&' +
                           'detailed=1')

    def test_usage_list_no_args(self):
        timeutils.set_time_override(datetime.datetime(2005, 2, 1, 0, 0))
        self.run_command('usage-list')
        self.assert_called('GET',
                           '/os-simple-tenant-usage?' +
                           'start=2005-01-04T00:00:00&' +
                           'end=2005-02-02T00:00:00&' +
                           'detailed=1')

    def test_usage(self):
        self.run_command('usage --start 2000-01-20 --end 2005-02-01 '
                         '--tenant test')
        self.assert_called('GET',
                           '/os-simple-tenant-usage/test?' +
                           'start=2000-01-20T00:00:00&' +
                           'end=2005-02-01T00:00:00')

    def test_usage_no_tenant(self):
        self.run_command('usage --start 2000-01-20 --end 2005-02-01')
        self.assert_called('GET',
                           '/os-simple-tenant-usage/tenant_id?' +
                           'start=2000-01-20T00:00:00&' +
                           'end=2005-02-01T00:00:00')

    def test_flavor_delete(self):
        self.run_command("flavor-delete 2")
        self.assert_called('DELETE', '/flavors/2')

    def test_flavor_create(self):
        self.run_command("flavor-create flavorcreate "
                         "1234 512 10 1 --swap 1024 --ephemeral 10 "
                         "--is-public true")
        self.assert_called('POST', '/flavors', pos=-3)
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/flavors/1/os-extra_specs', pos=-1)

    def test_aggregate_list(self):
        self.run_command('aggregate-list')
        self.assert_called('GET', '/os-aggregates')

    def test_aggregate_create(self):
        self.run_command('aggregate-create test_name nova1')
        body = {"aggregate": {"name": "test_name",
                              "availability_zone": "nova1"}}
        self.assert_called('POST', '/os-aggregates', body)

    def test_aggregate_delete(self):
        self.run_command('aggregate-delete 1')
        self.assert_called('DELETE', '/os-aggregates/1')

    def test_aggregate_update(self):
        self.run_command('aggregate-update 1 new_name')
        body = {"aggregate": {"name": "new_name"}}
        self.assert_called('PUT', '/os-aggregates/1', body)

    def test_aggregate_update_with_availability_zone(self):
        self.run_command('aggregate-update 1 foo new_zone')
        body = {"aggregate": {"name": "foo", "availability_zone": "new_zone"}}
        self.assert_called('PUT', '/os-aggregates/1', body)

    def test_aggregate_set_metadata(self):
        self.run_command('aggregate-set-metadata 1 foo=bar delete_key')
        body = {"set_metadata": {"metadata": {"foo": "bar",
                                              "delete_key": None}}}
        self.assert_called('POST', '/os-aggregates/1/action', body)

    def test_aggregate_add_host(self):
        self.run_command('aggregate-add-host 1 host1')
        body = {"add_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body)

    def test_aggregate_remove_host(self):
        self.run_command('aggregate-remove-host 1 host1')
        body = {"remove_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body)

    def test_aggregate_details(self):
        self.run_command('aggregate-details 1')
        self.assert_called('GET', '/os-aggregates/1')

    def test_live_migration(self):
        self.run_command('live-migration sample-server hostname')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                            'block_migration': False,
                                            'disk_over_commit': False}})
        self.run_command('live-migration sample-server hostname \
                         --block-migrate')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                            'block_migration': True,
                                            'disk_over_commit': False}})
        self.run_command('live-migration sample-server hostname \
                         --block-migrate --disk-over-commit')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                            'block_migration': True,
                                            'disk_over_commit': True}})

    def test_reset_state(self):
        self.run_command('reset-state sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'error'}})
        self.run_command('reset-state sample-server --active')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'active'}})

    def test_services_list(self):
        self.run_command('service-list')
        self.assert_called('GET', '/os-services')

    def test_services_list_with_host(self):
        self.run_command('service-list --host host1')
        self.assert_called('GET', '/os-services?host=host1')

    def test_services_list_with_servicename(self):
        self.run_command('service-list --servicename nova-cert')
        self.assert_called('GET', '/os-services?binary=nova-cert')

    def test_services_list_with_host_servicename(self):
        self.run_command('service-list --host host1 --servicename nova-cert')
        self.assert_called('GET', '/os-services?host=host1&binary=nova-cert')

    def test_services_enable(self):
        self.run_command('service-enable host1 nova-cert')
        body = {'host': 'host1', 'binary': 'nova-cert'}
        self.assert_called('PUT', '/os-services/enable', body)

    def test_services_disable(self):
        self.run_command('service-disable host1 nova-cert')
        body = {'host': 'host1', 'binary': 'nova-cert'}
        self.assert_called('PUT', '/os-services/disable', body)

    def test_fixed_ips_get(self):
        self.run_command('fixed-ip-get 192.168.1.1')
        self.assert_called('GET', '/os-fixed-ips/192.168.1.1')

    def test_fixed_ips_reserve(self):
        self.run_command('fixed-ip-reserve 192.168.1.1')
        body = {'reserve': None}
        self.assert_called('POST', '/os-fixed-ips/192.168.1.1/action', body)

    def test_fixed_ips_unreserve(self):
        self.run_command('fixed-ip-unreserve 192.168.1.1')
        body = {'unreserve': None}
        self.assert_called('POST', '/os-fixed-ips/192.168.1.1/action', body)

    def test_host_list(self):
        self.run_command('host-list')
        self.assert_called('GET', '/os-hosts')

    def test_host_list_with_zone(self):
        self.run_command('host-list --zone nova')
        self.assert_called('GET', '/os-hosts?zone=nova')

    def test_host_update_status(self):
        self.run_command('host-update sample-host_1 --status enabled')
        body = {'host': {'status': 'enabled'}}
        self.assert_called('PUT', '/os-hosts/sample-host_1', body)

    def test_host_update_maintenance(self):
        self.run_command('host-update sample-host_2 --maintenance enable')
        body = {'host': {'maintenance_mode': 'enable'}}
        self.assert_called('PUT', '/os-hosts/sample-host_2', body)

    def test_host_update_multiple_settings(self):
        self.run_command('host-update sample-host_3 '
                         '--status disabled --maintenance enable')
        body = {'host': {'status': 'disabled', 'maintenance_mode': 'enable'}}
        self.assert_called('PUT', '/os-hosts/sample-host_3', body)

    def test_host_startup(self):
        self.run_command('host-action sample-host --action startup')
        self.assert_called(
            'POST', '/os-hosts/sample-host/action', {'startup': None})

    def test_host_shutdown(self):
        self.run_command('host-action sample-host --action shutdown')
        self.assert_called(
            'POST', '/os-hosts/sample-host/action', {'shutdown': None})

    def test_host_reboot(self):
        self.run_command('host-action sample-host --action reboot')
        self.assert_called(
            'POST', '/os-hosts/sample-host/action', {'reboot': None})

    def test_coverage_start(self):
        self.run_command('coverage-start')
        self.assert_called('POST', '/os-coverage/action')

    def test_coverage_start_with_combine(self):
        self.run_command('coverage-start --combine')
        body = {'start': {'combine': True}}
        self.assert_called('POST', '/os-coverage/action', body)

    def test_coverage_stop(self):
        self.run_command('coverage-stop')
        self.assert_called_anytime('POST', '/os-coverage/action')

    def test_coverage_report(self):
        self.run_command('coverage-report report')
        self.assert_called_anytime('POST', '/os-coverage/action')

    def test_coverage_report_with_html(self):
        self.run_command('coverage-report report --html')
        body = {'report': {'html': True, 'file': 'report'}}
        self.assert_called_anytime('POST', '/os-coverage/action', body)

    def test_coverage_report_with_xml(self):
        self.run_command('coverage-report report --xml')
        body = {'report': {'xml': True, 'file': 'report'}}
        self.assert_called_anytime('POST', '/os-coverage/action', body)

    def test_hypervisor_list(self):
        self.run_command('hypervisor-list')
        self.assert_called('GET', '/os-hypervisors')

    def test_hypervisor_list_matching(self):
        self.run_command('hypervisor-list --matching hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/search')

    def test_hypervisor_servers(self):
        self.run_command('hypervisor-servers hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers')

    def test_hypervisor_show(self):
        self.run_command('hypervisor-show 1234')
        self.assert_called('GET', '/os-hypervisors/1234')

    def test_hypervisor_uptime(self):
        self.run_command('hypervisor-uptime 1234')
        self.assert_called('GET', '/os-hypervisors/1234/uptime')

    def test_hypervisor_stats(self):
        self.run_command('hypervisor-stats')
        self.assert_called('GET', '/os-hypervisors/statistics')

    def test_quota_show(self):
        self.run_command('quota-show --tenant test')
        self.assert_called('GET', '/os-quota-sets/test')

    def test_quota_show_no_tenant(self):
        self.run_command('quota-show')
        self.assert_called('GET', '/os-quota-sets/tenant_id')

    def test_quota_defaults(self):
        self.run_command('quota-defaults --tenant test')
        self.assert_called('GET', '/os-quota-sets/test/defaults')

    def test_quota_defaults_no_nenant(self):
        self.run_command('quota-defaults')
        self.assert_called('GET', '/os-quota-sets/tenant_id/defaults')

    def test_quota_update(self):
        self.run_command(
                        'quota-update 97f4c221bff44578b0300df4ef119353 \
                         --instances=5')
        self.assert_called('PUT',
                        '/os-quota-sets/97f4c221bff44578b0300df4ef119353')

    def test_quota_update_error(self):
        self.assertRaises(exceptions.CommandError,
                          self.run_command,
                         'quota-update 7f4c221-bff4-4578-b030-0df4ef119353 \
                          --instances=5')

    def test_quota_class_show(self):
        self.run_command('quota-class-show test')
        self.assert_called('GET', '/os-quota-class-sets/test')

    def test_quota_class_update(self):
        self.run_command('quota-class-update 97f4c221bff44578b0300df4ef119353 \
                          --instances=5')
        self.assert_called('PUT',
                       '/os-quota-class-sets/97f4c221bff44578b0300df4ef119353')

    def test_network_list(self):
        self.run_command('network-list')
        self.assert_called('GET', '/os-networks')

    def test_network_show(self):
        self.run_command('network-show 1')
        self.assert_called('GET', '/os-networks/1')

    def test_cloudpipe_list(self):
        self.run_command('cloudpipe-list')
        self.assert_called('GET', '/os-cloudpipe')

    def test_cloudpipe_create(self):
        self.run_command('cloudpipe-create myproject')
        body = {'cloudpipe': {'project_id': "myproject"}}
        self.assert_called('POST', '/os-cloudpipe', body)

    def test_cloudpipe_configure(self):
        self.run_command('cloudpipe-configure 192.168.1.1 1234')
        body = {'configure_project': {'vpn_ip': "192.168.1.1",
                                      'vpn_port': '1234'}}
        self.assert_called('PUT', '/os-cloudpipe/configure-project', body)

    def test_network_associate_host(self):
        self.run_command('network-associate-host 1 testHost')
        body = {'associate_host': 'testHost'}
        self.assert_called('POST', '/os-networks/1/action', body)

    def test_network_associate_project(self):
        self.run_command('network-associate-project 1')
        body = {'id': "1"}
        self.assert_called('POST', '/os-networks/add', body)

    def test_network_disassociate_host(self):
        self.run_command('network-disassociate --host-only 1 2')
        body = {'disassociate_host': None}
        self.assert_called('POST', '/os-networks/2/action', body)

    def test_network_disassociate_project(self):
        self.run_command('network-disassociate --project-only 1 2')
        body = {'disassociate_project': None}
        self.assert_called('POST', '/os-networks/2/action', body)

    def test_network_create_v4(self):
        self.run_command('network-create --fixed-range-v4 10.0.1.0/24 \
                         --dns1 10.0.1.254 new_network')
        body = {'network': {'cidr': '10.0.1.0/24', 'label': 'new_network',
                            'dns1': '10.0.1.254'}}
        self.assert_called('POST', '/os-networks', body)

    def test_network_create_v6(self):
        self.run_command('network-create --fixed-range-v6 2001::/64 \
                          new_network')
        body = {'network': {'cidr_v6': '2001::/64', 'label': 'new_network'}}
        self.assert_called('POST', '/os-networks', body)

    def test_backup(self):
        self.run_command('backup sample-server back1 daily 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'createBackup': {'name': 'back1',
                                             'backup_type': 'daily',
                                             'rotation': '1'}})
        self.run_command('backup 1234 back1 daily 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'createBackup': {'name': 'back1',
                                             'backup_type': 'daily',
                                             'rotation': '1'}})

    def test_absolute_limits(self):
        self.run_command('absolute-limits')
        self.assert_called('GET', '/limits')

        self.run_command('absolute-limits --reserved')
        self.assert_called('GET', '/limits?reserved=1')

    def test_evacuate(self):
        self.run_command('evacuate sample-server new_host')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'onSharedStorage': False}})
        self.run_command('evacuate sample-server new_host '
                            '--password NewAdminPass')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'onSharedStorage': False,
                                         'adminPass': 'NewAdminPass'}})
        self.run_command('evacuate sample-server new_host')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'onSharedStorage': False}})
        self.run_command('evacuate sample-server new_host '
                            '--on-shared-storage')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'onSharedStorage': True}})

    def test_get_password(self):
        self.run_command('get-password sample-server /foo/id_rsa')
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_clear_password(self):
        self.run_command('clear-password sample-server')
        self.assert_called('DELETE', '/servers/1234/os-server-password')

    def test_availability_zone_list(self):
            self.run_command('availability-zone-list')
            self.assert_called('GET', '/os-availability-zone/detail')

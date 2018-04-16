# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
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

import argparse
import base64
import collections
import datetime
import os

import fixtures
import mock
from oslo_utils import timeutils
import six
from six.moves import builtins
import testtools

import novaclient
from novaclient import api_versions
from novaclient import base
import novaclient.client
from novaclient import exceptions
import novaclient.shell
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import servers
import novaclient.v2.shell

FAKE_UUID_1 = fakes.FAKE_IMAGE_UUID_1
FAKE_UUID_2 = fakes.FAKE_IMAGE_UUID_2


# Converting dictionary to object
TestAbsoluteLimits = collections.namedtuple("TestAbsoluteLimits",
                                            ["name", "value"])


class ShellFixture(fixtures.Fixture):
    def setUp(self):
        super(ShellFixture, self).setUp()
        self.shell = novaclient.shell.OpenStackComputeShell()

    def tearDown(self):
        # For some method like test_image_meta_bad_action we are
        # testing a SystemExit to be thrown and object self.shell has
        # no time to get instantiated which is OK in this case, so
        # we make sure the method is there before launching it.
        if hasattr(self.shell, 'cs'):
            self.shell.cs.clear_callstack()
        super(ShellFixture, self).tearDown()


class ShellTest(utils.TestCase):
    FAKE_ENV = {
        'NOVA_USERNAME': 'username',
        'NOVA_PASSWORD': 'password',
        'NOVA_PROJECT_ID': 'project_id',
        'OS_COMPUTE_API_VERSION': '2',
        'NOVA_URL': 'http://no.where',
        'OS_AUTH_URL': 'http://no.where/v2.0',
    }

    def setUp(self):
        """Run before each test."""
        super(ShellTest, self).setUp()

        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))
        self.shell = self.useFixture(ShellFixture()).shell
        self.useFixture(fixtures.MonkeyPatch(
            'novaclient.client.Client', fakes.FakeClient))

    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('sys.stderr', new_callable=six.StringIO)
    def run_command(self, cmd, mock_stderr, mock_stdout, api_version=None):
        version_options = []
        if api_version:
            version_options.extend(["--os-compute-api-version", api_version,
                                    "--service-type", "computev21"])
        if isinstance(cmd, list):
            self.shell.main(version_options + cmd)
        else:
            self.shell.main(version_options + cmd.split())
        return mock_stdout.getvalue(), mock_stderr.getvalue()

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def assert_not_called(self, method, url, body=None):
        return self.shell.cs.assert_not_called(method, url, body)

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
        self.run_command('boot --flavor 1 --image %s '
                         'some-server' % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
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
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_image_with_error_out_no_match(self):
        cmd = ("boot --flavor 1"
               " --image-with fake_key=fake_value some-server")
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_key(self):
        self.run_command('boot --flavor 1 --image %s --key-name 1 some-server'
                         % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'key_name': '1',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_user_data(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        with open(testfile) as testfile_fd:
            data = testfile_fd.read().encode('utf-8')
        expected_file_data = base64.b64encode(data).decode('utf-8')
        self.run_command(
            'boot --flavor 1 --image %s --user-data %s some-server' %
            (FAKE_UUID_1, testfile))
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
                'user_data': expected_file_data
            }},
        )

    def test_boot_avzone(self):
        self.run_command(
            'boot --flavor 1 --image %s --availability-zone avzone  '
            'some-server' % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'availability_zone': 'avzone',
                'min_count': 1,
                'max_count': 1
            }},
        )

    def test_boot_secgroup(self):
        self.run_command(
            'boot --flavor 1 --image %s --security-groups secgroup1,'
            'secgroup2  some-server' % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'security_groups': [{'name': 'secgroup1'},
                                    {'name': 'secgroup2'}],
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_config_drive(self):
        self.run_command(
            'boot --flavor 1 --image %s --config-drive 1 some-server' %
            FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
                'config_drive': True
            }},
        )

    def test_boot_access_ip(self):
        self.run_command(
            'boot --flavor 1 --image %s --access-ip-v4 10.10.10.10 '
            '--access-ip-v6 ::1 some-server' % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'accessIPv4': '10.10.10.10',
                'accessIPv6': '::1',
                'max_count': 1,
                'min_count': 1
            }},
        )

    def test_boot_config_drive_custom(self):
        self.run_command(
            'boot --flavor 1 --image %s --config-drive /dev/hda some-server' %
            FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
                'config_drive': '/dev/hda'
            }},
        )

    def test_boot_invalid_user_data(self):
        invalid_file = os.path.join(os.path.dirname(__file__),
                                    'no_such_file')
        cmd = ('boot some-server --flavor 1 --image %s'
               ' --user-data %s' % (FAKE_UUID_1, invalid_file))
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_no_image_no_bdms(self):
        cmd = 'boot --flavor 1 some-server'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_no_flavor(self):
        cmd = 'boot --image %s some-server' % FAKE_UUID_1
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_not_key_value_bdm(self):
        cmd = ('boot --flavor 1 --image %s --block-device %s,tag=foo '
               'test-server' % (FAKE_UUID_1, FAKE_UUID_2))
        self.assertRaises(argparse.ArgumentTypeError, self.run_command, cmd)

    def test_boot_not_key_value_ephemeral(self):
        cmd = ('boot --flavor 1 --image %s --ephemeral %s,tag=foo '
               'test-server' % (FAKE_UUID_1, FAKE_UUID_2))
        self.assertRaises(argparse.ArgumentTypeError, self.run_command, cmd)

    def test_boot_no_image_bdms(self):
        self.run_command(
            'boot --flavor 1 --block-device-mapping vda=blah:::0 some-server'
        )
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping': [
                    {
                        'volume_id': 'blah',
                        'delete_on_termination': '0',
                        'device_name': 'vda'
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_image_bdms_v2(self):
        self.run_command(
            'boot --flavor 1 --image %s --block-device id=fake-id,'
            'source=volume,dest=volume,device=vda,size=1,format=ext4,'
            'type=disk,shutdown=preserve some-server' % FAKE_UUID_1
        )
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': FAKE_UUID_1,
                        'source_type': 'image',
                        'destination_type': 'local',
                        'boot_index': 0,
                        'delete_on_termination': True,
                    },
                    {
                        'uuid': 'fake-id',
                        'source_type': 'volume',
                        'destination_type': 'volume',
                        'device_name': 'vda',
                        'volume_size': '1',
                        'guest_format': 'ext4',
                        'device_type': 'disk',
                        'delete_on_termination': False,
                    },
                ],
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_image_bdms_v2_wrong_source_type(self):
        self.assertRaises(
            exceptions.CommandError, self.run_command,
            'boot --flavor 1 --image %s --block-device id=fake-id,'
            'source=fake,device=vda,size=1,format=ext4,'
            'type=disk,shutdown=preserve some-server' % FAKE_UUID_1)

    def test_boot_image_bdms_v2_no_source_type_no_destination_type(self):
        self.run_command(
            'boot --flavor 1 --image %s --block-device id=fake-id,'
            'device=vda,size=1,format=ext4,'
            'type=disk,shutdown=preserve some-server' % FAKE_UUID_1
        )
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': FAKE_UUID_1,
                        'source_type': 'image',
                        'destination_type': 'local',
                        'boot_index': 0,
                        'delete_on_termination': True,
                    },
                    {
                        'uuid': 'fake-id',
                        'source_type': 'blank',
                        'destination_type': 'local',
                        'device_name': 'vda',
                        'volume_size': '1',
                        'guest_format': 'ext4',
                        'device_type': 'disk',
                        'delete_on_termination': False,
                    },
                ],
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_image_bdms_v2_no_destination_type(self):
        self.run_command(
            'boot --flavor 1 --image %s --block-device id=fake-id,'
            'source=volume,device=vda,size=1,format=ext4,'
            'type=disk,shutdown=preserve some-server' % FAKE_UUID_1
        )
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': FAKE_UUID_1,
                        'source_type': 'image',
                        'destination_type': 'local',
                        'boot_index': 0,
                        'delete_on_termination': True,
                    },
                    {
                        'uuid': 'fake-id',
                        'source_type': 'volume',
                        'destination_type': 'volume',
                        'device_name': 'vda',
                        'volume_size': '1',
                        'guest_format': 'ext4',
                        'device_type': 'disk',
                        'delete_on_termination': False,
                    },
                ],
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_image_bdms_v2_wrong_destination_type(self):
        self.assertRaises(
            exceptions.CommandError, self.run_command,
            'boot --flavor 1 --image %s --block-device id=fake-id,'
            'source=volume,dest=dest1,device=vda,size=1,format=ext4,'
            'type=disk,shutdown=preserve some-server' % FAKE_UUID_1)

    def test_boot_image_bdms_v2_with_tag(self):
        self.run_command(
            'boot --flavor 1 --image %s --block-device id=fake-id,'
            'source=volume,dest=volume,device=vda,size=1,format=ext4,'
            'type=disk,shutdown=preserve,tag=foo some-server' % FAKE_UUID_1,
            api_version='2.32'
        )
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': FAKE_UUID_1,
                        'source_type': 'image',
                        'destination_type': 'local',
                        'boot_index': 0,
                        'delete_on_termination': True,
                    },
                    {
                        'uuid': 'fake-id',
                        'source_type': 'volume',
                        'destination_type': 'volume',
                        'device_name': 'vda',
                        'volume_size': '1',
                        'guest_format': 'ext4',
                        'device_type': 'disk',
                        'delete_on_termination': False,
                        'tag': 'foo',
                    },
                ],
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_no_image_bdms_v2(self):
        self.run_command(
            'boot --flavor 1 --block-device id=fake-id,source=volume,'
            'dest=volume,bus=virtio,device=vda,size=1,format=ext4,bootindex=0,'
            'type=disk,shutdown=preserve some-server'
        )
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': 'fake-id',
                        'source_type': 'volume',
                        'destination_type': 'volume',
                        'disk_bus': 'virtio',
                        'device_name': 'vda',
                        'volume_size': '1',
                        'guest_format': 'ext4',
                        'boot_index': '0',
                        'device_type': 'disk',
                        'delete_on_termination': False,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

        cmd = 'boot --flavor 1 --boot-volume fake-id some-server'
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': 'fake-id',
                        'source_type': 'volume',
                        'destination_type': 'volume',
                        'boot_index': 0,
                        'delete_on_termination': False,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

        cmd = 'boot --flavor 1 --snapshot fake-id some-server'
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'uuid': 'fake-id',
                        'source_type': 'snapshot',
                        'destination_type': 'volume',
                        'boot_index': 0,
                        'delete_on_termination': False,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

        self.run_command('boot --flavor 1 --swap 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'source_type': 'blank',
                        'destination_type': 'local',
                        'boot_index': -1,
                        'guest_format': 'swap',
                        'volume_size': '1',
                        'delete_on_termination': True,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

        self.run_command(
            'boot --flavor 1 --ephemeral size=1,format=ext4 some-server'
        )
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'block_device_mapping_v2': [
                    {
                        'source_type': 'blank',
                        'destination_type': 'local',
                        'boot_index': -1,
                        'guest_format': 'ext4',
                        'volume_size': '1',
                        'delete_on_termination': True,
                    }
                ],
                'imageRef': '',
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_bdms_v2_invalid_shutdown_value(self):
        self.assertRaises(exceptions.CommandError, self.run_command,
                          ('boot --flavor 1 --image %s --block-device '
                           'id=fake-id,source=volume,dest=volume,device=vda,'
                           'size=1,format=ext4,type=disk,shutdown=foobar '
                           'some-server' % FAKE_UUID_1))

    def test_boot_metadata(self):
        self.run_command('boot --image %s --flavor 1 --meta foo=bar=pants'
                         ' --meta spam=eggs some-server ' % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'metadata': {'foo': 'bar=pants', 'spam': 'eggs'},
                'min_count': 1,
                'max_count': 1,
            }},
        )

    def test_boot_with_incorrect_metadata(self):
        cmd = ('boot --image %s --flavor 1 --meta foo '
               'some-server ' % FAKE_UUID_1)
        result = self.assertRaises(argparse.ArgumentTypeError,
                                   self.run_command, cmd)
        expected = "'['foo']' is not in the format of 'key=value'"
        self.assertEqual(expected, result.args[0])

    def test_boot_hints(self):
        self.run_command('boot --image %s --flavor 1 '
                         '--hint a=b0=c0 --hint a=b1=c1 some-server ' %
                         FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 1,
                },
                'os:scheduler_hints': {'a': ['b0=c0', 'b1=c1']},
            },
        )

    def test_boot_nic_auto_not_alone_after(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic auto,tag=foo some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nic_auto_not_alone_before(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic tag=foo,auto some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nic_none_not_alone_before(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic none,tag=foo some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nic_none_not_alone_after(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic tag=foo,none some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=10.0.0.1 some-server' %
               FAKE_UUID_1)
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 1,
                    'networks': [
                        {'uuid': 'a=c', 'fixed_ip': '10.0.0.1'},
                    ],
                },
            },
        )

    def test_boot_with_multiple_nics(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=net_a,v4-fixed-ip=10.0.0.1 '
               '--nic net-id=net_b some-server' %
               FAKE_UUID_1)
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 1,
                    'networks': [
                        {'uuid': 'net_a', 'fixed_ip': '10.0.0.1'},
                        {'uuid': 'net_b'}
                    ],
                },
            },
        )

    def test_boot_nics_with_tag(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=10.0.0.1,tag=foo some-server' %
               FAKE_UUID_1)
        self.run_command(cmd, api_version='2.32')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 1,
                    'networks': [
                        {'uuid': 'a=c', 'fixed_ip': '10.0.0.1', 'tag': 'foo'},
                    ],
                },
            },
        )

    def test_boot_invalid_nics_pre_v2_32(self):
        # This is a negative test to make sure we fail with the correct message
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=1,port-id=2 some-server' % FAKE_UUID_1)
        ex = self.assertRaises(exceptions.CommandError, self.run_command,
                               cmd, api_version='2.1')
        self.assertNotIn('tag=tag', six.text_type(ex))

    def test_boot_invalid_nics_v2_32(self):
        # This is a negative test to make sure we fail with the correct message
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=1,port-id=2 some-server' % FAKE_UUID_1)
        ex = self.assertRaises(exceptions.CommandError, self.run_command,
                               cmd, api_version='2.32')
        self.assertIn('tag=tag', six.text_type(ex))

    def test_boot_invalid_nics_v2_36_auto(self):
        """This is a negative test to make sure we fail with the correct
        message. --nic auto isn't allowed before 2.37.
        """
        cmd = ('boot --image %s --flavor 1 --nic auto test' % FAKE_UUID_1)
        ex = self.assertRaises(exceptions.CommandError, self.run_command,
                               cmd, api_version='2.36')
        self.assertNotIn('auto,none', six.text_type(ex))

    def test_boot_invalid_nics_v2_37(self):
        """This is a negative test to make sure we fail with the correct
        message.
        """
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=1 --nic auto some-server' % FAKE_UUID_1)
        ex = self.assertRaises(exceptions.CommandError, self.run_command,
                               cmd, api_version='2.37')
        self.assertIn('auto,none', six.text_type(ex))

    def test_boot_nics_auto_allocate_default(self):
        """Tests that if microversion>=2.37 is specified and no --nics are
        specified that a single --nic with net-id=auto is used.
        """
        cmd = 'boot --image %s --flavor 1 some-server' % FAKE_UUID_1
        self.run_command(cmd, api_version='2.37')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 1,
                    'networks': 'auto',
                },
            },
        )

    def test_boot_nics_auto_allocate_none(self):
        """Tests specifying '--nic none' with microversion 2.37
        """
        cmd = 'boot --image %s --flavor 1 --nic none some-server' % FAKE_UUID_1
        self.run_command(cmd, api_version='2.37')
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 1,
                    'networks': 'none',
                },
            },
        )

    def test_boot_nics_ipv6(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=a=c,v6-fixed-ip=2001:db9:0:1::10 some-server' %
               FAKE_UUID_1)
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 1,
                    'networks': [
                        {'uuid': 'a=c', 'fixed_ip': '2001:db9:0:1::10'},
                    ],
                },
            },
        )

    def test_boot_nics_both_ipv4_and_ipv6(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=10.0.0.1,'
               'v6-fixed-ip=2001:db9:0:1::10 some-server' % FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_no_value(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id some-server' % FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_random_key(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=10.0.0.1,foo=bar some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_no_netid_or_portid(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic v4-fixed-ip=10.0.0.1 some-server' % FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_netid_and_portid(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic port-id=some=port,net-id=some=net some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_invalid_ipv4(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=a=c,v4-fixed-ip=2001:db9:0:1::10 some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_invalid_ipv6(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=a=c,v6-fixed-ip=10.0.0.1 some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_net_id_twice(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-id=net-id1,net-id=net-id2 some-server' % FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_nics_net_name_neutron(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-name=private some-server' % FAKE_UUID_1)
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 1,
                    'networks': [
                        {'uuid': 'e43a56c7-11d4-45c9-8681-ddc8171b5850'},
                    ],
                },
            },
        )

    def test_boot_nics_net_name_neutron_dup(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-name=duplicate some-server' % FAKE_UUID_1)
        # this should raise a multiple matches error
        msg = ("Multiple network matches found for 'duplicate', "
               "use an ID to be more specific.")
        with testtools.ExpectedException(exceptions.CommandError, msg):
            self.run_command(cmd)

    def test_boot_nics_net_name_neutron_blank(self):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-name=blank some-server' % FAKE_UUID_1)
        # this should raise a multiple matches error
        msg = 'No Network matching blank\..*'
        with testtools.ExpectedException(exceptions.CommandError, msg):
            self.run_command(cmd)

    # TODO(sdague): the following tests should really avoid mocking
    # out other tests, and they should check the string in the
    # CommandError, because it's not really enough to distinguish
    # between various errors.
    @mock.patch('novaclient.v2.shell._find_network_id', return_value='net-id')
    def test_boot_nics_net_name_and_net_id(self, mock_find_network_id):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-name=some-net,net-id=some-id some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    @mock.patch('novaclient.v2.shell._find_network_id', return_value='net-id')
    def test_boot_nics_net_name_and_port_id(self, mock_find_network_id):
        cmd = ('boot --image %s --flavor 1 '
               '--nic net-name=some-net,port-id=some-id some-server' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_files(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        with open(testfile) as testfile_fd:
            data = testfile_fd.read()
        expected = base64.b64encode(data.encode('utf-8')).decode('utf-8')

        cmd = ('boot some-server --flavor 1 --image %s'
               ' --file /tmp/foo=%s --file /tmp/bar=%s')
        self.run_command(cmd % (FAKE_UUID_1, testfile, testfile))

        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
                'personality': [
                    {'path': '/tmp/bar', 'contents': expected},
                    {'path': '/tmp/foo', 'contents': expected},
                ]
            }},
        )

    def test_boot_invalid_files(self):
        invalid_file = os.path.join(os.path.dirname(__file__),
                                    'asdfasdfasdfasdf')
        cmd = ('boot some-server --flavor 1 --image %s'
               ' --file /foo=%s' % (FAKE_UUID_1, invalid_file))
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_files_2_57(self):
        """Tests that trying to run the boot command with the --file option
        after microversion 2.56 fails.
        """
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        cmd = ('boot some-server --flavor 1 --image %s'
               ' --file /tmp/foo=%s')
        self.assertRaises(SystemExit, self.run_command,
                          cmd % (FAKE_UUID_1, testfile), api_version='2.57')

    def test_boot_max_min_count(self):
        self.run_command('boot --image %s --flavor 1 --min-count 1'
                         ' --max-count 3 server' % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 3,
                }
            })

    def test_boot_invalid_min_count(self):
        cmd = 'boot --image %s --flavor 1 --min-count 0  server' % FAKE_UUID_1
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_boot_min_max_count(self):
        self.run_command('boot --image %s --flavor 1 --max-count 3 server' %
                         FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 3,
                }
            })
        self.run_command('boot --image %s --flavor 1 --min-count 3 server' %
                         FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 3,
                    'max_count': 3,
                }
            })
        self.run_command('boot --image %s --flavor 1 '
                         '--min-count 3 --max-count 3 server' % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 3,
                    'max_count': 3,
                }
            })
        self.run_command('boot --image %s --flavor 1 '
                         '--min-count 3 --max-count 5 server' % FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '1',
                    'name': 'server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 3,
                    'max_count': 5,
                }
            })
        cmd = ('boot --image %s --flavor 1 --min-count 3 --max-count 1 serv' %
               FAKE_UUID_1)
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    @mock.patch('novaclient.v2.shell._poll_for_status')
    def test_boot_with_poll(self, poll_method):
        self.run_command('boot --flavor 1 --image %s some-server --poll' %
                         FAKE_UUID_1)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
            }},
        )
        self.assertEqual(1, poll_method.call_count)
        poll_method.assert_has_calls(
            [mock.call(self.shell.cs.servers.get, '1234', 'building',
                       ['active'])])

    def test_boot_with_poll_to_check_VM_state_error(self):
        self.assertRaises(exceptions.ResourceInErrorState, self.run_command,
                          'boot --flavor 1 --image %s some-bad-server --poll' %
                          FAKE_UUID_1)

    def test_boot_named_flavor(self):
        self.run_command(["boot", "--image", FAKE_UUID_1,
                          "--flavor", "512 MB Server",
                          "--max-count", "3", "server"])
        self.assert_called('GET', '/v2/images/' + FAKE_UUID_1, pos=0)
        self.assert_called('GET', '/flavors/512 MB Server', pos=1)
        self.assert_called('GET', '/flavors?is_public=None', pos=2)
        self.assert_called('GET', '/flavors/2', pos=3)
        self.assert_called(
            'POST', '/servers',
            {
                'server': {
                    'flavorRef': '2',
                    'name': 'server',
                    'imageRef': FAKE_UUID_1,
                    'min_count': 1,
                    'max_count': 3,
                }
            }, pos=4)

    def test_boot_invalid_ephemeral_data_format(self):
        cmd = ('boot --flavor 1 --image %s --ephemeral 1 some-server' %
               FAKE_UUID_1)
        self.assertRaises(argparse.ArgumentTypeError, self.run_command, cmd)

    def test_boot_with_tags(self):
        self.run_command('boot --flavor 1 --image %s --nic auto '
                         'some-server --tags tag1,tag2' % FAKE_UUID_1,
                         api_version='2.52')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
                'networks': 'auto',
                'tags': ['tag1', 'tag2']
            }},
        )

    def test_boot_without_tags_v252(self):
        self.run_command('boot --flavor 1 --image %s --nic auto '
                         'some-server' % FAKE_UUID_1,
                         api_version='2.52')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': FAKE_UUID_1,
                'min_count': 1,
                'max_count': 1,
                'networks': 'auto',
            }},
        )

    def test_boot_with_tags_pre_v2_52(self):
        cmd = ('boot --flavor 1 --image %s some-server '
               '--tags tag1,tag2' % FAKE_UUID_1)
        self.assertRaises(SystemExit, self.run_command,
                          cmd, api_version='2.51')

    def test_flavor_list(self):
        out, _ = self.run_command('flavor-list')
        self.assert_called_anytime('GET', '/flavors/detail')
        self.assertNotIn('Description', out)

    def test_flavor_list_with_description(self):
        """Tests that the description column is added for version >= 2.55."""
        out, _ = self.run_command('flavor-list', api_version='2.55')
        self.assert_called_anytime('GET', '/flavors/detail')
        self.assertIn('Description', out)

    def test_flavor_list_with_extra_specs(self):
        self.run_command('flavor-list --extra-specs')
        self.assert_called('GET', '/flavors/aa1/os-extra_specs')
        self.assert_called_anytime('GET', '/flavors/detail')

    def test_flavor_list_with_extra_specs_2_61_or_later(self):
        """Tests that the 'os-extra_specs' API is not called
        when the '--extra-specs' option is specified since microversion 2.61.
        """
        out, _ = self.run_command('flavor-list --extra-specs',
                                  api_version='2.61')
        self.assert_not_called('GET', '/flavors/aa1/os-extra_specs')
        self.assert_called_anytime('GET', '/flavors/detail')
        self.assertIn('extra_specs', out)

    def test_flavor_list_with_all(self):
        self.run_command('flavor-list --all')
        self.assert_called('GET', '/flavors/detail?is_public=None')

    def test_flavor_list_with_limit_and_marker(self):
        self.run_command('flavor-list --marker 1 --limit 2')
        self.assert_called('GET', '/flavors/detail?limit=2&marker=1')

    def test_flavor_list_with_min_disk(self):
        self.run_command('flavor-list --min-disk 20')
        self.assert_called('GET', '/flavors/detail?minDisk=20')

    def test_flavor_list_with_min_ram(self):
        self.run_command('flavor-list --min-ram 512')
        self.assert_called('GET', '/flavors/detail?minRam=512')

    def test_flavor_list_with_sort_key_dir(self):
        self.run_command('flavor-list --sort-key id --sort-dir asc')
        self.assert_called('GET', '/flavors/detail?sort_dir=asc&sort_key=id')

    def test_flavor_show(self):
        out, _ = self.run_command('flavor-show 1')
        self.assert_called_anytime('GET', '/flavors/1')
        self.assertNotIn('description', out)

    def test_flavor_show_with_description(self):
        """Tests that the description is shown in version >= 2.55."""
        out, _ = self.run_command('flavor-show 1', api_version='2.55')
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/flavors/1/os-extra_specs', pos=-1)
        self.assertIn('description', out)

    def test_flavor_show_2_61_or_later(self):
        """Tests that the 'os-extra_specs' is not called in version >= 2.61."""
        out, _ = self.run_command('flavor-show 1', api_version='2.61')
        self.assert_not_called('GET', '/flavors/1/os-extra_specs')
        self.assert_called_anytime('GET', '/flavors/1')
        self.assertIn('extra_specs', out)

    def test_flavor_show_with_alphanum_id(self):
        self.run_command('flavor-show aa1')
        self.assert_called_anytime('GET', '/flavors/aa1')

    def test_flavor_show_by_name(self):
        self.run_command(['flavor-show', '128 MB Server'])
        self.assert_called('GET', '/flavors/128 MB Server', pos=0)
        self.assert_called('GET', '/flavors?is_public=None', pos=1)
        self.assert_called('GET', '/flavors/aa1', pos=2)
        self.assert_called('GET', '/flavors/aa1/os-extra_specs', pos=3)

    def test_flavor_show_by_name_priv(self):
        self.run_command(['flavor-show', '512 MB Server'])
        self.assert_called('GET', '/flavors/512 MB Server', pos=0)
        self.assert_called('GET', '/flavors?is_public=None', pos=1)
        self.assert_called('GET', '/flavors/2', pos=2)
        self.assert_called('GET', '/flavors/2/os-extra_specs', pos=3)

    def test_flavor_key_set(self):
        self.run_command('flavor-key 1 set k1=v1')
        self.assert_called('POST', '/flavors/1/os-extra_specs',
                           {'extra_specs': {'k1': 'v1'}})

    def test_flavor_key_unset(self):
        self.run_command('flavor-key 1 unset k1')
        self.assert_called('DELETE', '/flavors/1/os-extra_specs/k1')

    def test_flavor_access_list_flavor(self):
        self.run_command('flavor-access-list --flavor 2')
        self.assert_called('GET', '/flavors/2/os-flavor-access')

    def test_flavor_access_list_no_filter(self):
        cmd = 'flavor-access-list'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_flavor_access_list_public(self):
        cmd = 'flavor-access-list --flavor 1'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_flavor_access_add_by_id(self):
        self.run_command('flavor-access-add 2 proj2')
        self.assert_called('POST', '/flavors/2/action',
                           {'addTenantAccess': {'tenant': 'proj2'}})

    def test_flavor_access_add_by_name(self):
        self.run_command(['flavor-access-add', '512 MB Server', 'proj2'])
        self.assert_called('POST', '/flavors/2/action',
                           {'addTenantAccess': {'tenant': 'proj2'}})

    def test_flavor_access_remove_by_id(self):
        self.run_command('flavor-access-remove 2 proj2')
        self.assert_called('POST', '/flavors/2/action',
                           {'removeTenantAccess': {'tenant': 'proj2'}})

    def test_flavor_access_remove_by_name(self):
        self.run_command(['flavor-access-remove', '512 MB Server', 'proj2'])
        self.assert_called('POST', '/flavors/2/action',
                           {'removeTenantAccess': {'tenant': 'proj2'}})

    def test_create_image(self):
        self.run_command('image-create sample-server mysnapshot')
        self.assert_called(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot', 'metadata': {}}},
        )

    def test_create_image_2_45(self):
        """Tests the image-create command with microversion 2.45 which
        does not change the output of the command, just how the response
        from the server is processed.
        """
        self.run_command('image-create sample-server mysnapshot',
                         api_version='2.45')
        self.assert_called(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot', 'metadata': {}}},
        )

    def test_create_image_with_incorrect_metadata(self):
        cmd = 'image-create sample-server mysnapshot --metadata foo'
        result = self.assertRaises(argparse.ArgumentTypeError,
                                   self.run_command, cmd)
        expected = "'['foo']' is not in the format of 'key=value'"
        self.assertEqual(expected, result.args[0])

    def test_create_image_with_metadata(self):
        self.run_command(
            'image-create sample-server mysnapshot --metadata mykey=123')
        self.assert_called(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot',
                             'metadata': {'mykey': '123'}}},
        )

    def test_create_image_show(self):
        output, _err = self.run_command(
            'image-create sample-server mysnapshot --show')
        self.assert_called_anytime(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot', 'metadata': {}}},
        )
        self.assertIn('My Server Backup', output)
        self.assertIn('SAVING', output)

    @mock.patch('novaclient.v2.shell._poll_for_status')
    def test_create_image_with_poll(self, poll_method):
        self.run_command(
            'image-create sample-server mysnapshot --poll')
        self.assert_called_anytime(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot', 'metadata': {}}},
        )
        self.assertEqual(1, poll_method.call_count)
        poll_method.assert_has_calls(
            [mock.call(self.shell.cs.glance.find_image,
                       fakes.FAKE_IMAGE_UUID_SNAPSHOT, 'snapshotting',
                       ['active'])])

    def test_create_image_with_poll_to_check_image_state_deleted(self):
        self.assertRaises(
            exceptions.InstanceInDeletedState, self.run_command,
            'image-create sample-server mysnapshot_deleted --poll')

    def test_list(self):
        self.run_command('list')
        self.assert_called('GET', '/servers/detail', pos=0)
        self.assert_called('GET', '/servers/detail?marker=9014')

    def test_list_minimal(self):
        self.run_command('list --minimal')
        self.assert_called('GET', '/servers', pos=0)
        self.assert_called('GET', '/servers?marker=9014')

    def test_list_deleted(self):
        self.run_command('list --deleted')
        self.assert_called(
            'GET',
            '/servers/detail?deleted=True',
            pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?deleted=True&marker=9014')

    def test_list_with_images(self):
        self.run_command('list --image %s' % FAKE_UUID_1)
        self.assert_called(
            'GET',
            '/servers/detail?image=%s' % FAKE_UUID_1,
            pos=1)
        self.assert_called(
            'GET',
            '/servers/detail?image=%s&marker=9014' % FAKE_UUID_1)

    def test_list_with_flavors(self):
        self.run_command('list --flavor 1')
        self.assert_called('GET', '/servers/detail?flavor=1', pos=1)
        self.assert_called('GET', '/servers/detail?flavor=1&marker=9014')

    def test_list_by_tenant(self):
        self.run_command('list --tenant fake_tenant')
        self.assert_called(
            'GET',
            '/servers/detail?all_tenants=1&tenant_id=fake_tenant', pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?all_tenants=1&marker=9014&tenant_id=fake_tenant')

    def test_list_by_user(self):
        self.run_command('list --user fake_user')
        self.assert_called(
            'GET',
            '/servers/detail?all_tenants=1&user_id=fake_user', pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?all_tenants=1&marker=9014&user_id=fake_user')

    def test_list_with_single_sort_key_no_dir(self):
        self.run_command('list --sort 1')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=desc&sort_key=1'), pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?marker=9014&sort_dir=desc&sort_key=1')

    def test_list_with_single_sort_key_and_dir(self):
        self.run_command('list --sort 1:asc')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=asc&sort_key=1'), pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?marker=9014&sort_dir=asc&sort_key=1')

    def test_list_with_sort_keys_no_dir(self):
        self.run_command('list --sort 1,2')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=desc&sort_dir=desc&'
                    'sort_key=1&sort_key=2'), pos=0)
        self.assert_called(
            'GET', ('/servers/detail?marker=9014&sort_dir=desc&sort_dir=desc&'
                    'sort_key=1&sort_key=2'))

    def test_list_with_sort_keys_and_dirs(self):
        self.run_command('list --sort 1:asc,2:desc')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=asc&sort_dir=desc&'
                    'sort_key=1&sort_key=2'), pos=0)
        self.assert_called(
            'GET', ('/servers/detail?marker=9014&sort_dir=asc&sort_dir=desc&'
                    'sort_key=1&sort_key=2'))

    def test_list_with_sort_keys_and_some_dirs(self):
        self.run_command('list --sort 1,2:asc')
        self.assert_called(
            'GET', ('/servers/detail?sort_dir=desc&sort_dir=asc&'
                    'sort_key=1&sort_key=2'), pos=0)
        self.assert_called(
            'GET', ('/servers/detail?marker=9014&sort_dir=desc&'
                    'sort_dir=asc&sort_key=1&sort_key=2'))

    def test_list_with_invalid_sort_dir_one(self):
        cmd = 'list --sort 1:foo'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_list_with_invalid_sort_dir_two(self):
        cmd = 'list --sort 1:asc,2:foo'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_list_sortby_index_with_sort(self):
        # sortby_index is None if there is sort information
        for cmd in ['list --sort key',
                    'list --sort key:desc',
                    'list --sort key1,key2:asc']:
            with mock.patch('novaclient.utils.print_list') as mock_print_list:
                self.run_command(cmd)
                mock_print_list.assert_called_once_with(
                    mock.ANY, mock.ANY, mock.ANY, sortby_index=None)

    def test_list_sortby_index_without_sort(self):
        # sortby_index is 1 without sort information
        for cmd in ['list', 'list --minimal', 'list --deleted']:
            with mock.patch('novaclient.utils.print_list') as mock_print_list:
                self.run_command(cmd)
                mock_print_list.assert_called_once_with(
                    mock.ANY, mock.ANY, mock.ANY, sortby_index=1)

    def test_list_fields(self):
        output, _err = self.run_command(
            'list --fields '
            'host,security_groups,OS-EXT-MOD:some_thing')
        self.assert_called('GET', '/servers/detail', pos=0)
        self.assert_called('GET', '/servers/detail?marker=9014')
        self.assertIn('computenode1', output)
        self.assertIn('securitygroup1', output)
        self.assertIn('OS-EXT-MOD: Some Thing', output)
        self.assertIn('mod_some_thing_value', output)
        # Testing the 'networks' field that is explicitly added to the
        # existing fields list.
        output, _err = self.run_command('list --fields networks')
        self.assertIn('Networks', output)
        self.assertIn('10.11.12.13', output)
        self.assertIn('5.6.7.8', output)

    @mock.patch(
        'novaclient.tests.unit.v2.fakes.FakeSessionClient.get_servers_detail')
    def test_list_fields_no_instances(self, mock_get_servers_detail):
        mock_get_servers_detail.return_value = (200, {}, {"servers": []})
        stdout, _stderr = self.run_command('list --fields metadata,networks')
        # Because there are no instances, you just get the default columns
        # rather than the ones you actually asked for (Metadata, Networks).
        defaults = 'ID | Name | Status | Task State | Power State | Networks'
        self.assertIn(defaults, stdout)

    def test_list_invalid_fields(self):
        self.assertRaises(exceptions.CommandError,
                          self.run_command,
                          'list --fields host,security_groups,'
                          'OS-EXT-MOD:some_thing,invalid')
        self.assertRaises(exceptions.CommandError,
                          self.run_command,
                          'list --fields __dict__')
        self.assertRaises(exceptions.CommandError,
                          self.run_command,
                          'list --fields update')
        self.assertRaises(exceptions.CommandError,
                          self.run_command,
                          'list --fields __init__')
        self.assertRaises(exceptions.CommandError,
                          self.run_command,
                          'list --fields __module__,updated')

    def test_list_with_marker(self):
        self.run_command('list --marker some-uuid')
        self.assert_called('GET', '/servers/detail?marker=some-uuid', pos=0)
        self.assert_called('GET', '/servers/detail?marker=9014')

    def test_list_with_limit(self):
        self.run_command('list --limit 3')
        self.assert_called('GET', '/servers/detail?limit=3')

    def test_list_with_changes_since(self):
        self.run_command('list --changes-since 2016-02-29T06:23:22')
        self.assert_called(
            'GET',
            '/servers/detail?changes-since=2016-02-29T06%3A23%3A22',
            pos=0)
        self.assert_called(
            'GET',
            ('/servers/detail?changes-since=2016-02-29T06%3A23%3A22&'
             'marker=9014'))

    def test_list_with_changes_since_invalid_value(self):
        self.assertRaises(exceptions.CommandError,
                          self.run_command, 'list --changes-since 0123456789')

    def test_list_fields_redundant(self):
        output, _err = self.run_command('list --fields id,status,status')
        header = output.splitlines()[1]
        self.assertEqual(1, header.count('ID'))
        self.assertEqual(0, header.count('Id'))
        self.assertEqual(1, header.count('Status'))

    def test_meta_parsing(self):
        meta = ['key1=meta1', 'key2=meta2']
        ref = {'key1': 'meta1', 'key2': 'meta2'}
        parsed_meta = novaclient.v2.shell._meta_parsing(meta)
        self.assertEqual(ref, parsed_meta)

    def test_reboot(self):
        self.run_command('reboot sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'reboot': {'type': 'SOFT'}})
        self.run_command('reboot sample-server --hard')
        self.assert_called('POST', '/servers/1234/action',
                           {'reboot': {'type': 'HARD'}})

    def test_reboot_many(self):
        self.run_command('reboot sample-server sample-server2')
        self.assert_called('POST', '/servers/1234/action',
                           {'reboot': {'type': 'SOFT'}}, pos=-2)
        self.assert_called('POST', '/servers/5678/action',
                           {'reboot': {'type': 'SOFT'}}, pos=-1)

    def test_rebuild(self):
        output, _err = self.run_command('rebuild sample-server %s'
                                        % FAKE_UUID_1)
        self.assert_called('GET', '/servers?name=sample-server', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=sample-server',
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_1, pos=3)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': FAKE_UUID_1}}, pos=4)
        self.assert_called('GET', '/flavors/1', pos=5)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=6)
        self.assertIn('adminPass', output)

    def test_rebuild_password(self):
        output, _err = self.run_command('rebuild sample-server %s'
                                        ' --rebuild-password asdf'
                                        % FAKE_UUID_1)
        self.assert_called('GET', '/servers?name=sample-server', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=sample-server',
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_1, pos=3)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': FAKE_UUID_1,
                            'adminPass': 'asdf'}}, pos=4)
        self.assert_called('GET', '/flavors/1', pos=5)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=6)
        self.assertIn('adminPass', output)

    def test_rebuild_preserve_ephemeral(self):
        self.run_command('rebuild sample-server %s --preserve-ephemeral'
                         % FAKE_UUID_1)
        self.assert_called('GET', '/servers?name=sample-server', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=sample-server',
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_1, pos=3)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': FAKE_UUID_1,
                                        'preserve_ephemeral': True}}, pos=4)
        self.assert_called('GET', '/flavors/1', pos=5)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=6)

    def test_rebuild_name_meta(self):
        self.run_command('rebuild sample-server %s --name asdf --meta '
                         'foo=bar' % FAKE_UUID_1)
        self.assert_called('GET', '/servers?name=sample-server', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=sample-server',
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_1, pos=3)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': FAKE_UUID_1,
                                        'name': 'asdf',
                                        'metadata': {'foo': 'bar'}}}, pos=4)
        self.assert_called('GET', '/flavors/1', pos=5)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=6)

    def test_rebuild_reset_keypair(self):
        self.run_command('rebuild sample-server %s --key-name test_keypair' %
                         FAKE_UUID_1, api_version='2.54')
        self.assert_called('GET', '/servers?name=sample-server', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=sample-server',
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_1, pos=3)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': FAKE_UUID_1,
                                        'key_name': 'test_keypair',
                                        'description': None}}, pos=4)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=5)

    def test_rebuild_unset_keypair(self):
        self.run_command('rebuild sample-server %s --key-unset' %
                         FAKE_UUID_1, api_version='2.54')
        self.assert_called('GET', '/servers?name=sample-server', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=sample-server',
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_1, pos=3)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': FAKE_UUID_1,
                                        'key_name': None,
                                        'description': None}}, pos=4)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=5)

    def test_rebuild_unset_keypair_with_key_name(self):
        ex = self.assertRaises(
            exceptions.CommandError, self.run_command,
            'rebuild sample-server %s --key-unset --key-name test_keypair' %
            FAKE_UUID_1, api_version='2.54')
        self.assertIn("Cannot specify '--key-unset' with '--key-name'.",
                      six.text_type(ex))

    def test_rebuild_with_incorrect_metadata(self):
        cmd = 'rebuild sample-server %s --name asdf --meta foo' % FAKE_UUID_1
        result = self.assertRaises(argparse.ArgumentTypeError,
                                   self.run_command, cmd)
        expected = "'['foo']' is not in the format of 'key=value'"
        self.assertEqual(expected, result.args[0])

    def test_rebuild_user_data_2_56(self):
        """Tests that trying to run the rebuild command with the --user-data*
        options before microversion 2.57 fails.
        """
        cmd = 'rebuild sample-server %s --user-data test' % FAKE_UUID_1
        self.assertRaises(SystemExit, self.run_command, cmd,
                          api_version='2.56')
        cmd = 'rebuild sample-server %s --user-data-unset' % FAKE_UUID_1
        self.assertRaises(SystemExit, self.run_command, cmd,
                          api_version='2.56')

    def test_rebuild_files_2_57(self):
        """Tests that trying to run the rebuild command with the --file option
        after microversion 2.56 fails.
        """
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        cmd = 'rebuild sample-server %s --file /tmp/foo=%s'
        self.assertRaises(SystemExit, self.run_command,
                          cmd % (FAKE_UUID_1, testfile), api_version='2.57')

    def test_rebuild_change_user_data(self):
        self.run_command('rebuild sample-server %s --user-data test' %
                         FAKE_UUID_1, api_version='2.57')
        user_data = servers.ServerManager.transform_userdata('test')
        self.assert_called('GET', '/servers?name=sample-server', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=sample-server',
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_1, pos=3)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': FAKE_UUID_1,
                                        'user_data': user_data,
                                        'description': None}}, pos=4)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=5)

    def test_rebuild_unset_user_data(self):
        self.run_command('rebuild sample-server %s --user-data-unset' %
                         FAKE_UUID_1, api_version='2.57')
        self.assert_called('GET', '/servers?name=sample-server', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=sample-server',
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_1, pos=3)
        self.assert_called('POST', '/servers/1234/action',
                           {'rebuild': {'imageRef': FAKE_UUID_1,
                                        'user_data': None,
                                        'description': None}}, pos=4)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=5)

    def test_rebuild_user_data_and_unset_user_data(self):
        """Tests that trying to set --user-data and --unset-user-data in the
        same rebuild call fails.
        """
        cmd = ('rebuild sample-server %s --user-data x --user-data-unset' %
               FAKE_UUID_1)
        ex = self.assertRaises(exceptions.CommandError, self.run_command, cmd,
                               api_version='2.57')
        self.assertIn("Cannot specify '--user-data-unset' with "
                      "'--user-data'.", six.text_type(ex))

    def test_start(self):
        self.run_command('start sample-server')
        self.assert_called('POST', '/servers/1234/action', {'os-start': None})

    def test_start_with_all_tenants(self):
        self.run_command('start sample-server --all-tenants')
        self.assert_called('GET',
                           '/servers?all_tenants=1&name=sample-server', pos=0)
        self.assert_called('GET',
                           ('/servers?all_tenants=1&marker=9014&'
                            'name=sample-server'),
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('POST', '/servers/1234/action', {'os-start': None})

    def test_stop(self):
        self.run_command('stop sample-server')
        self.assert_called('POST', '/servers/1234/action', {'os-stop': None})

    def test_stop_with_all_tenants(self):
        self.run_command('stop sample-server --all-tenants')
        self.assert_called('GET',
                           '/servers?all_tenants=1&name=sample-server', pos=0)
        self.assert_called('GET',
                           ('/servers?all_tenants=1&marker=9014&'
                            'name=sample-server'),
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('POST', '/servers/1234/action', {'os-stop': None})

    def test_pause(self):
        self.run_command('pause sample-server')
        self.assert_called('POST', '/servers/1234/action', {'pause': None})

    def test_unpause(self):
        self.run_command('unpause sample-server')
        self.assert_called('POST', '/servers/1234/action', {'unpause': None})

    def test_lock(self):
        self.run_command('lock sample-server')
        self.assert_called('POST', '/servers/1234/action', {'lock': None})

    def test_unlock(self):
        self.run_command('unlock sample-server')
        self.assert_called('POST', '/servers/1234/action', {'unlock': None})

    def test_suspend(self):
        self.run_command('suspend sample-server')
        self.assert_called('POST', '/servers/1234/action', {'suspend': None})

    def test_resume(self):
        self.run_command('resume sample-server')
        self.assert_called('POST', '/servers/1234/action', {'resume': None})

    def test_rescue(self):
        self.run_command('rescue sample-server')
        self.assert_called('POST', '/servers/1234/action', {'rescue': None})

    def test_rescue_password(self):
        self.run_command('rescue sample-server --password asdf')
        self.assert_called('POST', '/servers/1234/action',
                           {'rescue': {'adminPass': 'asdf'}})

    def test_rescue_image(self):
        self.run_command('rescue sample-server --image %s' % FAKE_UUID_1)
        self.assert_called('POST', '/servers/1234/action',
                           {'rescue': {'rescue_image_ref': FAKE_UUID_1}})

    def test_unrescue(self):
        self.run_command('unrescue sample-server')
        self.assert_called('POST', '/servers/1234/action', {'unrescue': None})

    def test_shelve(self):
        self.run_command('shelve sample-server')
        self.assert_called('POST', '/servers/1234/action', {'shelve': None})

    def test_shelve_offload(self):
        self.run_command('shelve-offload sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'shelveOffload': None})

    def test_unshelve(self):
        self.run_command('unshelve sample-server')
        self.assert_called('POST', '/servers/1234/action', {'unshelve': None})

    def test_migrate(self):
        self.run_command('migrate sample-server')
        self.assert_called('POST', '/servers/1234/action', {'migrate': None})

    def test_migrate_pre_v256(self):
        self.assertRaises(SystemExit,
                          self.run_command,
                          'migrate --host target-host sample-server',
                          api_version='2.55')

    def test_migrate_v256(self):
        self.run_command('migrate sample-server',
                         api_version='2.56')
        self.assert_called('POST', '/servers/1234/action',
                           {'migrate': {}})

        self.run_command('migrate --host target-host sample-server',
                         api_version='2.56')
        self.assert_called('POST', '/servers/1234/action',
                           {'migrate': {'host': 'target-host'}})

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
    def test_set_password(self):
        self.run_command('set-password sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'changePassword': {'adminPass': 'p'}})

    def test_show(self):
        self.run_command('show 1234')
        self.assert_called('GET', '/servers?name=1234', pos=0)
        self.assert_called('GET', '/servers?marker=9014&name=1234', pos=1)
        self.assert_called('GET', '/servers?name=1234', pos=2)
        self.assert_called('GET', '/servers?marker=9014&name=1234', pos=3)
        self.assert_called('GET', '/servers/1234', pos=4)
        self.assert_called('GET', '/flavors/1', pos=5)
        self.assert_called('GET', '/v2/images/%s' % FAKE_UUID_2, pos=6)

    def test_show_no_image(self):
        self.run_command('show 9012')
        self.assert_called('GET', '/servers/9012', pos=-2)
        self.assert_called('GET', '/flavors/1', pos=-1)

    def test_show_bad_id(self):
        self.assertRaises(exceptions.CommandError,
                          self.run_command, 'show xxx')

    def test_show_unavailable_image_and_flavor(self):
        output, _ = self.run_command('show 9013')
        self.assert_called('GET', '/servers/9013', pos=-6)
        self.assert_called('GET',
                           '/flavors/80645cf4-6ad3-410a-bbc8-6f3e1e291f51',
                           pos=-5)
        self.assert_called('GET',
                           '/v2/images/3e861307-73a6-4d1f-8d68-f68b03223032',
                           pos=-1)
        self.assertIn('Image not found', output)
        self.assertIn('Flavor not found', output)

    def test_show_with_name_help(self):
        output, _ = self.run_command('show help')
        self.assert_called('GET', '/servers/9014', pos=-6)

    @mock.patch('novaclient.v2.shell.utils.print_dict')
    def test_print_server(self, mock_print_dict):
        self.run_command('show 5678')
        args, kwargs = mock_print_dict.call_args
        parsed_server = args[0]
        self.assertEqual('securitygroup1, securitygroup2',
                         parsed_server['security_groups'])

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/servers/1234')
        self.run_command('delete sample-server')
        self.assert_called('DELETE', '/servers/1234')

    def test_force_delete(self):
        self.run_command('force-delete 1234')
        self.assert_called('POST', '/servers/1234/action',
                           {'forceDelete': None})
        self.run_command('force-delete sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'forceDelete': None})

    def test_restore(self):
        self.run_command('restore 1234')
        self.assert_called('POST', '/servers/1234/action', {'restore': None})
        self.run_command('restore sample-server')
        self.assert_called('POST', '/servers/1234/action', {'restore': None})

    def test_restore_withname(self):
        self.run_command('restore sample-server')
        self.assert_called('GET',
                           '/servers?deleted=True&name=sample-server', pos=0)
        self.assert_called('GET',
                           ('/servers?deleted=True&marker=9014&'
                            'name=sample-server'),
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('POST', '/servers/1234/action', {'restore': None},
                           pos=3)

    def test_delete_two_with_two_existent(self):
        self.run_command('delete 1234 5678')
        self.assert_called('DELETE', '/servers/1234', pos=-7)
        self.assert_called('DELETE', '/servers/5678', pos=-1)
        self.run_command('delete sample-server sample-server2')
        self.assert_called('GET',
                           '/servers?name=sample-server', pos=-8)
        self.assert_called('GET',
                           '/servers?marker=9014&name=sample-server',
                           pos=-7)
        self.assert_called('GET', '/servers/1234', pos=-6)
        self.assert_called('DELETE', '/servers/1234', pos=-5)
        self.assert_called('GET',
                           '/servers?name=sample-server2',
                           pos=-4)
        self.assert_called('GET',
                           '/servers?marker=9014&name=sample-server2',
                           pos=-3)
        self.assert_called('GET', '/servers/5678', pos=-2)
        self.assert_called('DELETE', '/servers/5678', pos=-1)

    def test_delete_two_with_two_existent_all_tenants(self):
        self.run_command('delete sample-server sample-server2 --all-tenants')
        self.assert_called('GET',
                           '/servers?all_tenants=1&name=sample-server', pos=0)
        self.assert_called('GET',
                           ('/servers?all_tenants=1&marker=9014&'
                            'name=sample-server'),
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('DELETE', '/servers/1234', pos=3)
        self.assert_called('GET',
                           '/servers?all_tenants=1&name=sample-server2',
                           pos=4)
        self.assert_called('GET',
                           ('/servers?all_tenants=1&marker=9014&'
                            'name=sample-server2'),
                           pos=5)
        self.assert_called('GET', '/servers/5678', pos=6)
        self.assert_called('DELETE', '/servers/5678', pos=7)

    def test_delete_two_with_one_nonexistent(self):
        cmd = 'delete 1234 123456789'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        self.assert_called_anytime('DELETE', '/servers/1234')
        cmd = 'delete sample-server nonexistentserver'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        self.assert_called_anytime('DELETE', '/servers/1234')

    def test_delete_one_with_one_nonexistent(self):
        cmd = 'delete 123456789'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        cmd = 'delete nonexistent-server1'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_delete_two_with_two_nonexistent(self):
        cmd = 'delete 123456789 987654321'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)
        cmd = 'delete nonexistent-server1 nonexistent-server2'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_diagnostics(self):
        self.run_command('diagnostics 1234')
        self.assert_called('GET', '/servers/1234/diagnostics')
        self.run_command('diagnostics sample-server')
        self.assert_called('GET', '/servers/1234/diagnostics')

    def test_refresh_network(self):
        self.run_command('refresh-network 1234')
        self.assert_called('POST', '/os-server-external-events',
                           {'events': [{'name': 'network-changed',
                                        'server_uuid': '1234'}]})

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

    def test_set_host_meta(self):
        self.run_command('host-meta hyper set key1=val1 key2=val2')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=1)
        self.assert_called('POST', '/servers/uuid2/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=2)
        self.assert_called('POST', '/servers/uuid3/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=3)
        self.assert_called('POST', '/servers/uuid4/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=4)

    def test_set_host_meta_strict(self):
        self.run_command('host-meta hyper1 --strict set key1=val1 key2=val2')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=1)
        self.assert_called('POST', '/servers/uuid2/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}},
                           pos=2)

    def test_set_host_meta_no_match(self):
        cmd = 'host-meta hyper --strict set key1=val1 key2=val2'
        self.assertRaises(exceptions.NotFound, self.run_command, cmd)

    def test_set_host_meta_with_no_servers(self):
        self.run_command('host-meta hyper_no_servers set key1=val1 key2=val2')
        self.assert_called('GET', '/os-hypervisors/hyper_no_servers/servers')

    def test_set_host_meta_with_no_servers_strict(self):
        cmd = 'host-meta hyper_no_servers --strict set key1=val1 key2=val2'
        self.assertRaises(exceptions.NotFound, self.run_command, cmd)

    def test_delete_host_meta(self):
        self.run_command('host-meta hyper delete key1')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('DELETE', '/servers/uuid1/metadata/key1', pos=1)
        self.assert_called('DELETE', '/servers/uuid2/metadata/key1', pos=2)

    def test_delete_host_meta_strict(self):
        self.run_command('host-meta hyper1 --strict delete key1')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        self.assert_called('DELETE', '/servers/uuid1/metadata/key1', pos=1)
        self.assert_called('DELETE', '/servers/uuid2/metadata/key1', pos=2)

    def test_usage_list(self):
        cmd = 'usage-list --start 2000-01-20 --end 2005-02-01'
        stdout, _stderr = self.run_command(cmd)
        self.assert_called('GET',
                           '/os-simple-tenant-usage?' +
                           'start=2000-01-20T00:00:00&' +
                           'end=2005-02-01T00:00:00&' +
                           'detailed=1')
        # Servers, RAM MB-Hours, CPU Hours, Disk GiB-Hours
        self.assertIn('1       | 25451.76     | 49.71     | 0.00', stdout)

    def test_usage_list_stitch_together_next_results(self):
        cmd = 'usage-list --start 2000-01-20 --end 2005-02-01'
        stdout, _stderr = self.run_command(cmd, api_version='2.40')
        self.assert_called('GET',
                           '/os-simple-tenant-usage?'
                           'start=2000-01-20T00:00:00&'
                           'end=2005-02-01T00:00:00&'
                           'detailed=1', pos=0)
        markers = [
            'f079e394-1111-457b-b350-bb5ecc685cdd',
            'f079e394-2222-457b-b350-bb5ecc685cdd',
        ]
        for pos, marker in enumerate(markers):
            self.assert_called('GET',
                               '/os-simple-tenant-usage?'
                               'start=2000-01-20T00:00:00&'
                               'end=2005-02-01T00:00:00&'
                               'marker=%s&detailed=1' % (marker), pos=pos + 1)
        # Servers, RAM MB-Hours, CPU Hours, Disk GiB-Hours
        self.assertIn('2       | 50903.53     | 99.42     | 0.00', stdout)

    def test_usage_list_no_args(self):
        timeutils.set_time_override(datetime.datetime(2005, 2, 1, 0, 0))
        self.addCleanup(timeutils.clear_time_override)
        self.run_command('usage-list')
        self.assert_called('GET',
                           '/os-simple-tenant-usage?' +
                           'start=2005-01-04T00:00:00&' +
                           'end=2005-02-02T00:00:00&' +
                           'detailed=1')

    def test_usage(self):
        cmd = 'usage --start 2000-01-20 --end 2005-02-01 --tenant test'
        stdout, _stderr = self.run_command(cmd)
        self.assert_called('GET',
                           '/os-simple-tenant-usage/test?' +
                           'start=2000-01-20T00:00:00&' +
                           'end=2005-02-01T00:00:00')
        # Servers, RAM MB-Hours, CPU Hours, Disk GiB-Hours
        self.assertIn('1       | 25451.76     | 49.71     | 0.00', stdout)

    def test_usage_stitch_together_next_results(self):
        cmd = 'usage --start 2000-01-20 --end 2005-02-01'
        stdout, _stderr = self.run_command(cmd, api_version='2.40')
        self.assert_called('GET',
                           '/os-simple-tenant-usage/tenant_id?'
                           'start=2000-01-20T00:00:00&'
                           'end=2005-02-01T00:00:00', pos=0)
        markers = [
            'f079e394-1111-457b-b350-bb5ecc685cdd',
            'f079e394-2222-457b-b350-bb5ecc685cdd',
        ]
        for pos, marker in enumerate(markers):
            self.assert_called('GET',
                               '/os-simple-tenant-usage/tenant_id?'
                               'start=2000-01-20T00:00:00&'
                               'end=2005-02-01T00:00:00&'
                               'marker=%s' % (marker), pos=pos + 1)
        # Servers, RAM MB-Hours, CPU Hours, Disk GiB-Hours
        self.assertIn('2       | 50903.53     | 99.42     | 0.00', stdout)

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
        self.assert_called('POST', '/flavors', pos=-2)
        self.assert_called('GET', '/flavors/1', pos=-1)

    def test_flavor_create_with_description(self):
        """Tests creating a flavor with a description."""
        self.run_command("flavor-create description "
                         "1234 512 10 1 --description foo", api_version='2.55')
        expected_post_body = {
            "flavor": {
                "name": "description",
                "ram": 512,
                "vcpus": 1,
                "disk": 10,
                "id": "1234",
                "swap": 0,
                "OS-FLV-EXT-DATA:ephemeral": 0,
                "rxtx_factor": 1.0,
                "os-flavor-access:is_public": True,
                "description": "foo"
            }
        }
        self.assert_called('POST', '/flavors', expected_post_body, pos=-2)

    def test_flavor_update(self):
        """Tests creating a flavor with a description."""
        out, _ = self.run_command(
            "flavor-update with-description new-description",
            api_version='2.55')
        expected_put_body = {
            "flavor": {
                "description": "new-description"
            }
        }
        self.assert_called('GET', '/flavors/with-description', pos=-2)
        self.assert_called('PUT', '/flavors/with-description',
                           expected_put_body, pos=-1)
        self.assertIn('new-description', out)

    def test_aggregate_list(self):
        out, err = self.run_command('aggregate-list')
        self.assert_called('GET', '/os-aggregates')
        self.assertNotIn('UUID', out)

    def test_aggregate_list_v2_41(self):
        out, err = self.run_command('aggregate-list', api_version='2.41')
        self.assert_called('GET', '/os-aggregates')
        self.assertIn('UUID', out)
        self.assertIn('80785864-087b-45a5-a433-b20eac9b58aa', out)
        self.assertIn('30827713-5957-4b68-8fd3-ccaddb568c24', out)
        self.assertIn('9a651b22-ce3f-4a87-acd7-98446ef591c4', out)

    def test_aggregate_create(self):
        out, err = self.run_command('aggregate-create test_name nova1')
        body = {"aggregate": {"name": "test_name",
                              "availability_zone": "nova1"}}
        self.assert_called('POST', '/os-aggregates', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)
        self.assertNotIn('UUID', out)

    def test_aggregate_create_v2_41(self):
        out, err = self.run_command('aggregate-create test_name nova1',
                                    api_version='2.41')
        body = {"aggregate": {"name": "test_name",
                              "availability_zone": "nova1"}}
        self.assert_called('POST', '/os-aggregates', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)
        self.assertIn('UUID', out)
        self.assertIn('80785864-087b-45a5-a433-b20eac9b58aa', out)

    def test_aggregate_delete_by_id(self):
        self.run_command('aggregate-delete 1')
        self.assert_called('DELETE', '/os-aggregates/1')

    def test_aggregate_delete_by_name(self):
        self.run_command('aggregate-delete test')
        self.assert_called('DELETE', '/os-aggregates/1')

    def test_aggregate_update_by_id(self):
        out, err = self.run_command('aggregate-update 1 --name new_name')
        body = {"aggregate": {"name": "new_name"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)
        self.assertNotIn('UUID', out)

    def test_aggregate_update_by_id_v2_41(self):
        out, err = self.run_command('aggregate-update 1 --name new_name',
                                    api_version='2.41')
        body = {"aggregate": {"name": "new_name"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)
        self.assertIn('UUID', out)
        self.assertIn('80785864-087b-45a5-a433-b20eac9b58aa', out)

    def test_aggregate_update_by_name(self):
        self.run_command('aggregate-update test --name new_name ')
        body = {"aggregate": {"name": "new_name"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_update_with_availability_zone_by_id(self):
        self.run_command('aggregate-update 1 --name foo '
                         '--availability-zone new_zone')
        body = {"aggregate": {"name": "foo", "availability_zone": "new_zone"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_update_with_availability_zone_by_name(self):
        self.run_command('aggregate-update test --name foo '
                         '--availability-zone new_zone')
        body = {"aggregate": {"name": "foo", "availability_zone": "new_zone"}}
        self.assert_called('PUT', '/os-aggregates/1', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_update_without_availability_zone_and_name(self):
        ex = self.assertRaises(exceptions.CommandError, self.run_command,
                               'aggregate-update test')
        self.assertIn("Either '--name <name>' or '--availability-zone "
                      "<availability-zone>' must be specified.",
                      six.text_type(ex))

    def test_aggregate_set_metadata_add_by_id(self):
        out, err = self.run_command('aggregate-set-metadata 3 foo=bar')
        body = {"set_metadata": {"metadata": {"foo": "bar"}}}
        self.assert_called('POST', '/os-aggregates/3/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/3', pos=-1)
        self.assertNotIn('UUID', out)

    def test_aggregate_set_metadata_add_by_id_v2_41(self):
        out, err = self.run_command('aggregate-set-metadata 3 foo=bar',
                                    api_version='2.41')
        body = {"set_metadata": {"metadata": {"foo": "bar"}}}
        self.assert_called('POST', '/os-aggregates/3/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/3', pos=-1)
        self.assertIn('UUID', out)
        self.assertIn('9a651b22-ce3f-4a87-acd7-98446ef591c4', out)

    def test_aggregate_set_metadata_add_duplicate_by_id(self):
        cmd = 'aggregate-set-metadata 3 test=dup'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_aggregate_set_metadata_delete_by_id(self):
        self.run_command('aggregate-set-metadata 3 none_key')
        body = {"set_metadata": {"metadata": {"none_key": None}}}
        self.assert_called('POST', '/os-aggregates/3/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/3', pos=-1)

    def test_aggregate_set_metadata_delete_missing_by_id(self):
        cmd = 'aggregate-set-metadata 3 delete_key2'
        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

    def test_aggregate_set_metadata_by_name(self):
        self.run_command('aggregate-set-metadata test foo=bar')
        body = {"set_metadata": {"metadata": {"foo": "bar"}}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_add_host_by_id(self):
        out, err = self.run_command('aggregate-add-host 1 host1')
        body = {"add_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)
        self.assertNotIn('UUID', out)

    def test_aggregate_add_host_by_id_v2_41(self):
        out, err = self.run_command('aggregate-add-host 1 host1',
                                    api_version='2.41')
        body = {"add_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)
        self.assertIn('UUID', out)
        self.assertIn('80785864-087b-45a5-a433-b20eac9b58aa', out)

    def test_aggregate_add_host_by_name(self):
        self.run_command('aggregate-add-host test host1')
        body = {"add_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_remove_host_by_id(self):
        out, err = self.run_command('aggregate-remove-host 1 host1')
        body = {"remove_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)
        self.assertNotIn('UUID', out)

    def test_aggregate_remove_host_by_id_v2_41(self):
        out, err = self.run_command('aggregate-remove-host 1 host1',
                                    api_version='2.41')
        body = {"remove_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)
        self.assertIn('UUID', out)
        self.assertIn('80785864-087b-45a5-a433-b20eac9b58aa', out)

    def test_aggregate_remove_host_by_name(self):
        self.run_command('aggregate-remove-host test host1')
        body = {"remove_host": {"host": "host1"}}
        self.assert_called('POST', '/os-aggregates/1/action', body, pos=-2)
        self.assert_called('GET', '/os-aggregates/1', pos=-1)

    def test_aggregate_show_by_id(self):
        out, err = self.run_command('aggregate-show 1')
        self.assert_called('GET', '/os-aggregates/1')
        self.assertNotIn('UUID', out)

    def test_aggregate_show_by_id_v2_41(self):
        out, err = self.run_command('aggregate-show 1', api_version='2.41')
        self.assert_called('GET', '/os-aggregates/1')
        self.assertIn('UUID', out)
        self.assertIn('80785864-087b-45a5-a433-b20eac9b58aa', out)

    def test_aggregate_show_by_name(self):
        self.run_command('aggregate-show test')
        self.assert_called('GET', '/os-aggregates')

    def test_live_migration(self):
        self.run_command('live-migration sample-server hostname')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': False,
                                               'disk_over_commit': False}})
        self.run_command('live-migration sample-server hostname'
                         ' --block-migrate')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': True,
                                               'disk_over_commit': False}})
        self.run_command('live-migration sample-server hostname'
                         ' --block-migrate --disk-over-commit')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': True,
                                               'disk_over_commit': True}})

    def test_live_migration_v225(self):
        self.run_command('live-migration sample-server hostname',
                         api_version='2.25')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto'}})
        self.run_command('live-migration sample-server hostname'
                         ' --block-migrate', api_version='2.25')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': True}})
        self.run_command('live-migration sample-server', api_version='2.25')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': None,
                                               'block_migration': 'auto'}})

    def test_live_migration_v2_30(self):
        self.run_command('live-migration sample-server hostname',
                         api_version='2.30')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto'}})
        self.run_command('live-migration --force sample-server hostname',
                         api_version='2.30')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-migrateLive': {'host': 'hostname',
                                               'block_migration': 'auto',
                                               'force': True}})

    def test_live_migration_force_complete(self):
        self.run_command('live-migration-force-complete sample-server 1',
                         api_version='2.22')
        self.assert_called('POST', '/servers/1234/migrations/1/action',
                           {'force_complete': None})

    def test_list_migrations(self):
        self.run_command('server-migration-list sample-server',
                         api_version='2.23')
        self.assert_called('GET', '/servers/1234/migrations')

    def test_get_migration(self):
        self.run_command('server-migration-show sample-server 1',
                         api_version='2.23')
        self.assert_called('GET', '/servers/1234/migrations/1')

    def test_live_migration_abort(self):
        self.run_command('live-migration-abort sample-server 1',
                         api_version='2.24')
        self.assert_called('DELETE', '/servers/1234/migrations/1')

    def test_host_evacuate_live_with_no_target_host(self):
        self.run_command('host-evacuate-live hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': False,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_with_no_target_host_strict(self):
        self.run_command('host-evacuate-live hyper1 --strict')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': False,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)

    def test_host_evacuate_live_no_match(self):
        cmd = 'host-evacuate-live hyper --strict'
        self.assertRaises(exceptions.NotFound, self.run_command, cmd)

    def test_host_evacuate_live_2_25(self):
        self.run_command('host-evacuate-live hyper', api_version='2.25')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None, 'block_migration': 'auto'}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_2_25_strict(self):
        self.run_command('host-evacuate-live hyper1 --strict',
                         api_version='2.25')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        body = {'os-migrateLive': {'host': None, 'block_migration': 'auto'}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)

    def test_host_evacuate_live_with_target_host(self):
        self.run_command('host-evacuate-live hyper '
                         '--target-host hostname')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': 'hostname',
                                   'block_migration': False,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_with_target_host_strict(self):
        self.run_command('host-evacuate-live hyper1 '
                         '--target-host hostname --strict')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        body = {'os-migrateLive': {'host': 'hostname',
                                   'block_migration': False,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)

    def test_host_evacuate_live_2_30(self):
        self.run_command('host-evacuate-live --force hyper '
                         '--target-host hostname',
                         api_version='2.30')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': 'hostname',
                                   'block_migration': 'auto',
                                   'force': True}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_2_30_strict(self):
        self.run_command('host-evacuate-live --force hyper1 '
                         '--target-host hostname --strict',
                         api_version='2.30')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        body = {'os-migrateLive': {'host': 'hostname',
                                   'block_migration': 'auto',
                                   'force': True}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)

    def test_host_evacuate_live_with_block_migration(self):
        self.run_command('host-evacuate-live --block-migrate hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': True,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_with_block_migration_strict(self):
        self.run_command('host-evacuate-live --block-migrate hyper2 --strict')
        self.assert_called('GET', '/os-hypervisors/hyper2/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': True,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid3/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=2)

    def test_host_evacuate_live_with_block_migration_2_25(self):
        self.run_command('host-evacuate-live --block-migrate hyper',
                         api_version='2.25')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None, 'block_migration': True}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_with_block_migration_2_25_strict(self):
        self.run_command('host-evacuate-live --block-migrate hyper2 --strict',
                         api_version='2.25')
        self.assert_called('GET', '/os-hypervisors/hyper2/servers', pos=0)
        body = {'os-migrateLive': {'host': None, 'block_migration': True}}
        self.assert_called('POST', '/servers/uuid3/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=2)

    def test_host_evacuate_live_with_disk_over_commit(self):
        self.run_command('host-evacuate-live --disk-over-commit hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': False,
                                   'disk_over_commit': True}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid2/action', body, pos=2)
        self.assert_called('POST', '/servers/uuid3/action', body, pos=3)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=4)

    def test_host_evacuate_live_with_disk_over_commit_strict(self):
        self.run_command('host-evacuate-live --disk-over-commit hyper2 '
                         '--strict')
        self.assert_called('GET', '/os-hypervisors/hyper2/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': False,
                                   'disk_over_commit': True}}
        self.assert_called('POST', '/servers/uuid3/action', body, pos=1)
        self.assert_called('POST', '/servers/uuid4/action', body, pos=2)

    def test_host_evacuate_live_with_disk_over_commit_2_25(self):
        self.assertRaises(SystemExit, self.run_command,
                          'host-evacuate-live --disk-over-commit hyper',
                          api_version='2.25')

    def test_host_evacuate_live_with_disk_over_commit_2_25_strict(self):
        self.assertRaises(SystemExit, self.run_command,
                          'host-evacuate-live --disk-over-commit hyper2 '
                          '--strict', api_version='2.25')

    def test_host_evacuate_list_with_max_servers(self):
        self.run_command('host-evacuate-live --max-servers 1 hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': False,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)

    def test_host_evacuate_list_with_max_servers_strict(self):
        self.run_command('host-evacuate-live --max-servers 1 hyper1 --strict')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        body = {'os-migrateLive': {'host': None,
                                   'block_migration': False,
                                   'disk_over_commit': False}}
        self.assert_called('POST', '/servers/uuid1/action', body, pos=1)

    def test_reset_state(self):
        self.run_command('reset-state sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'error'}})
        self.run_command('reset-state sample-server --active')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'active'}})

    def test_reset_state_with_all_tenants(self):
        self.run_command('reset-state sample-server --all-tenants')
        self.assert_called('GET',
                           '/servers?all_tenants=1&name=sample-server', pos=0)
        self.assert_called('GET',
                           ('/servers?all_tenants=1&marker=9014&'
                            'name=sample-server'),
                           pos=1)
        self.assert_called('GET', '/servers/1234', pos=2)
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'error'}})

    def test_reset_state_multiple(self):
        self.run_command('reset-state sample-server sample-server2')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'error'}}, pos=-5)
        self.assert_called('POST', '/servers/5678/action',
                           {'os-resetState': {'state': 'error'}}, pos=-1)

    def test_reset_state_active_multiple(self):
        self.run_command('reset-state --active sample-server sample-server2')
        self.assert_called('POST', '/servers/1234/action',
                           {'os-resetState': {'state': 'active'}}, pos=-5)
        self.assert_called('POST', '/servers/5678/action',
                           {'os-resetState': {'state': 'active'}}, pos=-1)

    def test_reset_network(self):
        self.run_command('reset-network sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'resetNetwork': None})

    def test_services_list(self):
        self.run_command('service-list')
        self.assert_called('GET', '/os-services')

    def test_services_list_v2_53(self):
        """Tests nova service-list at the 2.53 microversion."""
        self.run_command('service-list', api_version='2.53')
        self.assert_called('GET', '/os-services')

    def test_services_list_with_host(self):
        self.run_command('service-list --host host1')
        self.assert_called('GET', '/os-services?host=host1')

    def test_services_list_with_binary(self):
        self.run_command('service-list --binary nova-cert')
        self.assert_called('GET', '/os-services?binary=nova-cert')

    def test_services_list_with_host_binary(self):
        self.run_command('service-list --host host1 --binary nova-cert')
        self.assert_called('GET', '/os-services?host=host1&binary=nova-cert')

    def test_services_enable(self):
        self.run_command('service-enable host1')
        body = {'host': 'host1', 'binary': 'nova-compute'}
        self.assert_called('PUT', '/os-services/enable', body)

    def test_services_enable_v2_53(self):
        """Tests nova service-enable at the 2.53 microversion."""
        self.run_command('service-enable %s' % fakes.FAKE_SERVICE_UUID_1,
                         api_version='2.53')
        body = {'status': 'enabled'}
        self.assert_called(
            'PUT', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1, body)

    def test_services_disable(self):
        self.run_command('service-disable host1')
        body = {'host': 'host1', 'binary': 'nova-compute'}
        self.assert_called('PUT', '/os-services/disable', body)

    def test_services_disable_v2_53(self):
        """Tests nova service-disable at the 2.53 microversion."""
        self.run_command('service-disable %s' % fakes.FAKE_SERVICE_UUID_1,
                         api_version='2.53')
        body = {'status': 'disabled'}
        self.assert_called(
            'PUT', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1, body)

    def test_services_disable_with_reason(self):
        self.run_command('service-disable host1 --reason no_reason')
        body = {'host': 'host1', 'binary': 'nova-compute',
                'disabled_reason': 'no_reason'}
        self.assert_called('PUT', '/os-services/disable-log-reason', body)

    def test_services_disable_with_reason_v2_53(self):
        """Tests nova service-disable --reason at microversion 2.53."""
        self.run_command('service-disable %s --reason no_reason' %
                         fakes.FAKE_SERVICE_UUID_1, api_version='2.53')
        body = {'status': 'disabled', 'disabled_reason': 'no_reason'}
        self.assert_called(
            'PUT', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1, body)

    def test_service_force_down_v2_53(self):
        """Tests nova service-force-down at the 2.53 microversion."""
        self.run_command('service-force-down %s' %
                         fakes.FAKE_SERVICE_UUID_1, api_version='2.53')
        body = {'forced_down': True}
        self.assert_called(
            'PUT', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1, body)

    def test_services_delete(self):
        self.run_command('service-delete 1')
        self.assert_called('DELETE', '/os-services/1')

    def test_services_delete_v2_53(self):
        """Tests nova service-delete at the 2.53 microversion."""
        self.run_command('service-delete %s' % fakes.FAKE_SERVICE_UUID_1)
        self.assert_called(
            'DELETE', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1)

    def test_host_evacuate_v2_14(self):
        self.run_command('host-evacuate hyper --target target_hyper',
                         api_version='2.14')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper'}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper'}}, pos=2)
        self.assert_called('POST', '/servers/uuid3/action',
                           {'evacuate': {'host': 'target_hyper'}}, pos=3)
        self.assert_called('POST', '/servers/uuid4/action',
                           {'evacuate': {'host': 'target_hyper'}}, pos=4)

    def test_host_evacuate_v2_14_strict(self):
        self.run_command('host-evacuate hyper1 --target target_hyper --strict',
                         api_version='2.14')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper'}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper'}}, pos=2)

    def test_host_evacuate(self):
        self.run_command('host-evacuate hyper --target target_hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=2)
        self.assert_called('POST', '/servers/uuid3/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=3)
        self.assert_called('POST', '/servers/uuid4/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=4)

    def test_host_evacuate_strict(self):
        self.run_command('host-evacuate hyper1 --target target_hyper --strict')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': False}}, pos=2)

    def test_host_evacuate_no_match(self):
        cmd = 'host-evacuate hyper --target target_hyper --strict'
        self.assertRaises(exceptions.NotFound, self.run_command, cmd)

    def test_host_evacuate_v2_29(self):
        self.run_command('host-evacuate hyper --target target_hyper --force',
                         api_version='2.29')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper', 'force': True}
                            }, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper', 'force': True}
                            }, pos=2)
        self.assert_called('POST', '/servers/uuid3/action',
                           {'evacuate': {'host': 'target_hyper', 'force': True}
                            }, pos=3)
        self.assert_called('POST', '/servers/uuid4/action',
                           {'evacuate': {'host': 'target_hyper', 'force': True}
                            }, pos=4)

    def test_host_evacuate_v2_29_strict(self):
        self.run_command('host-evacuate hyper1 --target target_hyper'
                         ' --force --strict', api_version='2.29')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper', 'force': True}
                            }, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper', 'force': True}
                            }, pos=2)

    def test_host_evacuate_with_shared_storage(self):
        self.run_command(
            'host-evacuate --on-shared-storage hyper --target target_hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=2)
        self.assert_called('POST', '/servers/uuid3/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=3)
        self.assert_called('POST', '/servers/uuid4/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=4)

    def test_host_evacuate_with_shared_storage_strict(self):
        self.run_command('host-evacuate --on-shared-storage hyper1'
                         ' --target target_hyper --strict')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'host': 'target_hyper',
                                         'onSharedStorage': True}}, pos=2)

    def test_host_evacuate_with_no_target_host(self):
        self.run_command('host-evacuate --on-shared-storage hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=2)
        self.assert_called('POST', '/servers/uuid3/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=3)
        self.assert_called('POST', '/servers/uuid4/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=4)

    def test_host_evacuate_with_no_target_host_strict(self):
        self.run_command('host-evacuate --on-shared-storage hyper1 --strict')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        self.assert_called('POST', '/servers/uuid1/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=1)
        self.assert_called('POST', '/servers/uuid2/action',
                           {'evacuate': {'onSharedStorage': True}}, pos=2)

    def test_host_servers_migrate(self):
        self.run_command('host-servers-migrate hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers', pos=0)
        self.assert_called('POST',
                           '/servers/uuid1/action', {'migrate': None}, pos=1)
        self.assert_called('POST',
                           '/servers/uuid2/action', {'migrate': None}, pos=2)
        self.assert_called('POST',
                           '/servers/uuid3/action', {'migrate': None}, pos=3)
        self.assert_called('POST',
                           '/servers/uuid4/action', {'migrate': None}, pos=4)

    def test_host_servers_migrate_strict(self):
        self.run_command('host-servers-migrate hyper1 --strict')
        self.assert_called('GET', '/os-hypervisors/hyper1/servers', pos=0)
        self.assert_called('POST',
                           '/servers/uuid1/action', {'migrate': None}, pos=1)
        self.assert_called('POST',
                           '/servers/uuid2/action', {'migrate': None}, pos=2)

    def test_host_servers_migrate_no_match(self):
        cmd = 'host-servers-migrate hyper --strict'
        self.assertRaises(exceptions.NotFound, self.run_command, cmd)

    def test_hypervisor_list(self):
        self.run_command('hypervisor-list')
        self.assert_called('GET', '/os-hypervisors')

    def test_hypervisor_list_matching(self):
        self.run_command('hypervisor-list --matching hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/search')

    def test_hypervisor_list_limit_marker(self):
        self.run_command('hypervisor-list --limit 10 --marker hyper1',
                         api_version='2.33')
        self.assert_called('GET', '/os-hypervisors?limit=10&marker=hyper1')

    def test_hypervisor_servers(self):
        self.run_command('hypervisor-servers hyper')
        self.assert_called('GET', '/os-hypervisors/hyper/servers')

    def test_hypervisor_show_by_id(self):
        self.run_command('hypervisor-show 1234')
        self.assert_called('GET', '/os-hypervisors/1234')

    def test_hypervisor_list_show_by_cell_id(self):
        self.run_command('hypervisor-show region!child@1')
        self.assert_called('GET', '/os-hypervisors/region!child@1')

    def test_hypervisor_show_by_name(self):
        self.run_command('hypervisor-show hyper1')
        self.assert_called('GET', '/os-hypervisors/hyper1')

    def test_hypervisor_uptime_by_id(self):
        self.run_command('hypervisor-uptime 1234')
        self.assert_called('GET', '/os-hypervisors/1234/uptime')

    def test_hypervisor_uptime_by_cell_id(self):
        self.run_command('hypervisor-uptime region!child@1')
        self.assert_called('GET', '/os-hypervisors/region!child@1/uptime')

    def test_hypervisor_uptime_by_name(self):
        self.run_command('hypervisor-uptime hyper1')
        self.assert_called('GET', '/os-hypervisors/1234/uptime')

    def test_hypervisor_stats(self):
        self.run_command('hypervisor-stats')
        self.assert_called('GET', '/os-hypervisors/statistics')

    def test_quota_show(self):
        self.run_command(
            'quota-show --tenant '
            '97f4c221bff44578b0300df4ef119353')
        self.assert_called(
            'GET',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353')

    def test_quota_show_detail(self):
        self.run_command(
            'quota-show --tenant '
            '97f4c221bff44578b0300df4ef119353 --detail')
        self.assert_called(
            'GET',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353/detail')

    def test_user_quota_show(self):
        self.run_command(
            'quota-show --tenant '
            '97f4c221bff44578b0300df4ef119353 --user u1')
        self.assert_called(
            'GET',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353?user_id=u1')

    def test_user_quota_show_detail(self):
        self.run_command(
            'quota-show --tenant '
            '97f4c221bff44578b0300df4ef119353 --user u1 --detail')
        self.assert_called(
            'GET',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353/detail'
            '?user_id=u1')

    def test_quota_show_no_tenant(self):
        self.run_command('quota-show')
        self.assert_called('GET', '/os-quota-sets/tenant_id')

    def test_quota_defaults(self):
        self.run_command(
            'quota-defaults --tenant '
            '97f4c221bff44578b0300df4ef119353')
        self.assert_called(
            'GET',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353/defaults')

    def test_quota_defaults_no_tenant(self):
        self.run_command('quota-defaults')
        self.assert_called('GET', '/os-quota-sets/tenant_id/defaults')

    def test_quota_update(self):
        self.run_command(
            'quota-update 97f4c221bff44578b0300df4ef119353'
            ' --instances=5')
        self.assert_called(
            'PUT',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353',
            {'quota_set': {'instances': 5}})

    def test_user_quota_update(self):
        self.run_command(
            'quota-update 97f4c221bff44578b0300df4ef119353'
            ' --user=u1'
            ' --instances=5')
        self.assert_called(
            'PUT',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353?user_id=u1',
            {'quota_set': {'instances': 5}})

    def test_quota_force_update(self):
        self.run_command(
            'quota-update 97f4c221bff44578b0300df4ef119353'
            ' --instances=5 --force')
        self.assert_called(
            'PUT', '/os-quota-sets/97f4c221bff44578b0300df4ef119353',
            {'quota_set': {'force': True,
                           'instances': 5}})

    def test_quota_update_fixed_ip(self):
        self.run_command(
            'quota-update 97f4c221bff44578b0300df4ef119353'
            ' --fixed-ips=5')
        self.assert_called(
            'PUT', '/os-quota-sets/97f4c221bff44578b0300df4ef119353',
            {'quota_set': {'fixed_ips': 5}})

    def test_quota_update_injected_file_2_57(self):
        """Tests that trying to update injected_file* quota with microversion
        2.57 fails.
        """
        for quota in ('--injected-files', '--injected-file-content-bytes',
                      '--injected-file-path-bytes'):
            cmd = ('quota-update 97f4c221bff44578b0300df4ef119353 %s=5' %
                   quota)
            self.assertRaises(SystemExit, self.run_command, cmd,
                              api_version='2.57')

    def test_quota_delete(self):
        self.run_command('quota-delete --tenant '
                         '97f4c221bff44578b0300df4ef119353')
        self.assert_called('DELETE',
                           '/os-quota-sets/97f4c221bff44578b0300df4ef119353')

    def test_user_quota_delete(self):
        self.run_command('quota-delete --tenant '
                         '97f4c221bff44578b0300df4ef119353 '
                         '--user u1')
        self.assert_called(
            'DELETE',
            '/os-quota-sets/97f4c221bff44578b0300df4ef119353?user_id=u1')

    def test_quota_class_show(self):
        self.run_command('quota-class-show test')
        self.assert_called('GET', '/os-quota-class-sets/test')

    def test_quota_class_update(self):
        # The list of args we can update.
        args = (
            '--instances', '--cores', '--ram', '--floating-ips', '--fixed-ips',
            '--metadata-items', '--injected-files',
            '--injected-file-content-bytes', '--injected-file-path-bytes',
            '--key-pairs', '--security-groups', '--security-group-rules',
            '--server-groups', '--server-group-members'
        )
        for arg in args:
            self.run_command('quota-class-update '
                             '97f4c221bff44578b0300df4ef119353 '
                             '%s=5' % arg)
            request_param = arg[2:].replace('-', '_')
            body = {'quota_class_set': {request_param: 5}}
            self.assert_called(
                'PUT', '/os-quota-class-sets/97f4c221bff44578b0300df4ef119353',
                body)

    def test_quota_class_update_injected_file_2_57(self):
        """Tests that trying to update injected_file* quota with microversion
        2.57 fails.
        """
        for quota in ('--injected-files', '--injected-file-content-bytes',
                      '--injected-file-path-bytes'):
            cmd = 'quota-class-update default %s=5' % quota
            self.assertRaises(SystemExit, self.run_command, cmd,
                              api_version='2.57')

    def test_backup(self):
        out, err = self.run_command('backup sample-server back1 daily 1')
        # With microversion < 2.45 there is no output from this command.
        self.assertEqual(0, len(out))
        self.assert_called('POST', '/servers/1234/action',
                           {'createBackup': {'name': 'back1',
                                             'backup_type': 'daily',
                                             'rotation': '1'}})
        self.run_command('backup 1234 back1 daily 1')
        self.assert_called('POST', '/servers/1234/action',
                           {'createBackup': {'name': 'back1',
                                             'backup_type': 'daily',
                                             'rotation': '1'}})

    def test_backup_2_45(self):
        """Tests the backup command with the 2.45 microversion which
        handles a different response and prints out the backup snapshot
        image details.
        """
        out, err = self.run_command(
            'backup sample-server back1 daily 1',
            api_version='2.45')
        # We should see the backup snapshot image name in the output.
        self.assertIn('back1', out)
        self.assertIn('SAVING', out)
        self.assert_called_anytime(
            'POST', '/servers/1234/action',
            {'createBackup': {'name': 'back1',
                              'backup_type': 'daily',
                              'rotation': '1'}})

    def test_limits(self):
        out = self.run_command('limits')[0]
        self.assert_called('GET', '/limits')
        self.assertIn('Personality', out)

        self.run_command('limits --reserved')
        self.assert_called('GET', '/limits?reserved=1')

        self.run_command('limits --tenant 1234')
        self.assert_called('GET', '/limits?tenant_id=1234')

        stdout, _err = self.run_command('limits --tenant 1234')
        self.assertIn('Verb', stdout)
        self.assertIn('Name', stdout)

    def test_print_absolute_limits(self):
        # Note: This test is to validate that no exception is
        #       thrown if in case we pass multiple custom fields
        limits = [TestAbsoluteLimits('maxTotalPrivateNetworks', 3),
                  TestAbsoluteLimits('totalPrivateNetworksUsed', 0),
                  # Above two fields are custom fields
                  TestAbsoluteLimits('maxImageMeta', 15),
                  TestAbsoluteLimits('totalCoresUsed', 10),
                  TestAbsoluteLimits('totalInstancesUsed', 5),
                  TestAbsoluteLimits('maxServerMeta', 10),
                  TestAbsoluteLimits('totalRAMUsed', 10240),
                  TestAbsoluteLimits('totalFloatingIpsUsed', 10)]
        novaclient.v2.shell._print_absolute_limits(limits=limits)

    def test_limits_2_57(self):
        """Tests the limits command at microversion 2.57 where personality
        size limits should not be shown.
        """
        out = self.run_command('limits', api_version='2.57')[0]
        self.assert_called('GET', '/limits')
        self.assertNotIn('Personality', out)

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
        self.run_command('evacuate sample-server new_host '
                         '--on-shared-storage')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'onSharedStorage': True}})

    def test_evacuate_v2_29(self):
        self.run_command('evacuate sample-server new_host', api_version="2.29")
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host'}})
        self.run_command('evacuate sample-server new_host '
                         '--password NewAdminPass', api_version="2.29")
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'adminPass': 'NewAdminPass'}})
        self.run_command('evacuate --force sample-server new_host',
                         api_version="2.29")
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'host': 'new_host',
                                         'force': True}})

    def test_evacuate_with_no_target_host(self):
        self.run_command('evacuate sample-server')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'onSharedStorage': False}})
        self.run_command('evacuate sample-server --password NewAdminPass')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'onSharedStorage': False,
                                         'adminPass': 'NewAdminPass'}})
        self.run_command('evacuate sample-server --on-shared-storage')
        self.assert_called('POST', '/servers/1234/action',
                           {'evacuate': {'onSharedStorage': True}})

    def test_get_password(self):
        self.run_command('get-password sample-server /foo/id_rsa')
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_get_password_without_key(self):
        self.run_command('get-password sample-server')
        self.assert_called('GET', '/servers/1234/os-server-password')

    def test_clear_password(self):
        self.run_command('clear-password sample-server')
        self.assert_called('DELETE', '/servers/1234/os-server-password')

    def test_availability_zone_list(self):
        self.run_command('availability-zone-list')
        self.assert_called('GET', '/os-availability-zone/detail')

    def test_server_security_group_add(self):
        self.run_command('add-secgroup sample-server testgroup')
        self.assert_called('POST', '/servers/1234/action',
                           {'addSecurityGroup': {'name': 'testgroup'}})

    def test_server_security_group_remove(self):
        self.run_command('remove-secgroup sample-server testgroup')
        self.assert_called('POST', '/servers/1234/action',
                           {'removeSecurityGroup': {'name': 'testgroup'}})

    def test_server_security_group_list(self):
        self.run_command('list-secgroup 1234')
        self.assert_called('GET', '/servers/1234/os-security-groups')

    def test_interface_list(self):
        self.run_command('interface-list 1234')
        self.assert_called('GET', '/servers/1234/os-interface')

    def test_interface_attach(self):
        self.run_command('interface-attach --port-id port_id 1234')
        self.assert_called('POST', '/servers/1234/os-interface',
                           {'interfaceAttachment': {'port_id': 'port_id'}})

    def test_interface_attach_with_tag_pre_v2_49(self):
        self.assertRaises(
            SystemExit, self.run_command,
            'interface-attach --port-id port_id --tag test_tag 1234',
            api_version='2.48')

    def test_interface_attach_with_tag(self):
        self.run_command(
            'interface-attach --port-id port_id --tag test_tag 1234',
            api_version='2.49')
        self.assert_called('POST', '/servers/1234/os-interface',
                           {'interfaceAttachment': {'port_id': 'port_id',
                                                    'tag': 'test_tag'}})

    def test_interface_detach(self):
        self.run_command('interface-detach 1234 port_id')
        self.assert_called('DELETE', '/servers/1234/os-interface/port_id')

    def test_volume_attachments(self):
        self.run_command('volume-attachments 1234')
        self.assert_called('GET', '/servers/1234/os-volume_attachments')

    def test_volume_attach(self):
        self.run_command('volume-attach sample-server Work /dev/vdb')
        self.assert_called('POST', '/servers/1234/os-volume_attachments',
                           {'volumeAttachment':
                               {'device': '/dev/vdb',
                                'volumeId': 'Work'}})

    def test_volume_attach_without_device(self):
        self.run_command('volume-attach sample-server Work')
        self.assert_called('POST', '/servers/1234/os-volume_attachments',
                           {'volumeAttachment':
                               {'volumeId': 'Work'}})

    def test_volume_attach_with_tag_pre_v2_49(self):
        self.assertRaises(
            SystemExit, self.run_command,
            'volume-attach --tag test_tag sample-server Work /dev/vdb',
            api_version='2.48')

    def test_volume_attach_with_tag(self):
        self.run_command(
            'volume-attach --tag test_tag sample-server Work /dev/vdb',
            api_version='2.49')
        self.assert_called('POST', '/servers/1234/os-volume_attachments',
                           {'volumeAttachment':
                               {'device': '/dev/vdb',
                                'volumeId': 'Work',
                                'tag': 'test_tag'}})

    def test_volume_update(self):
        self.run_command('volume-update sample-server Work Work')
        self.assert_called('PUT', '/servers/1234/os-volume_attachments/Work',
                           {'volumeAttachment': {'volumeId': 'Work'}})

    def test_volume_detach(self):
        self.run_command('volume-detach sample-server Work')
        self.assert_called('DELETE',
                           '/servers/1234/os-volume_attachments/Work')

    def test_instance_action_list(self):
        self.run_command('instance-action-list sample-server')
        self.assert_called('GET', '/servers/1234/os-instance-actions')

    def test_instance_action_get(self):
        self.run_command('instance-action sample-server req-abcde12345')
        self.assert_called(
            'GET',
            '/servers/1234/os-instance-actions/req-abcde12345')

    def test_instance_action_list_marker_pre_v258_not_allowed(self):
        cmd = 'instance-action-list sample-server --marker %s'
        self.assertRaises(SystemExit, self.run_command,
                          cmd % FAKE_UUID_1, api_version='2.57')

    def test_instance_action_list_limit_pre_v258_not_allowed(self):
        cmd = 'instance-action-list sample-server --limit 10'
        self.assertRaises(SystemExit, self.run_command,
                          cmd, api_version='2.57')

    def test_instance_action_list_changes_since_pre_v258_not_allowed(self):
        cmd = 'instance-action-list sample-server --changes-since ' \
              '2016-02-29T06:23:22'
        self.assertRaises(SystemExit, self.run_command,
                          cmd, api_version='2.57')

    def test_instance_action_list_limit_marker_v258(self):
        out = self.run_command('instance-action-list sample-server --limit 10 '
                               '--marker %s' % FAKE_UUID_1,
                               api_version='2.58')[0]
        # Assert that the updated_at value is in the output.
        self.assertIn('2013-03-25T13:50:09.000000', out)
        self.assert_called(
            'GET',
            '/servers/1234/os-instance-actions?'
            'limit=10&marker=%s' % FAKE_UUID_1)

    def test_instance_action_list_with_changes_since_v258(self):
        self.run_command('instance-action-list sample-server '
                         '--changes-since 2016-02-29T06:23:22',
                         api_version='2.58')
        self.assert_called(
            'GET',
            '/servers/1234/os-instance-actions?'
            'changes-since=2016-02-29T06%3A23%3A22')

    def test_instance_action_list_with_changes_since_invalid_value_v258(self):
        ex = self.assertRaises(
            exceptions.CommandError, self.run_command,
            'instance-action-list sample-server --changes-since 0123456789',
            api_version='2.58')
        self.assertIn('Invalid changes-since value', six.text_type(ex))

    def test_instance_usage_audit_log(self):
        self.run_command('instance-usage-audit-log')
        self.assert_called('GET', '/os-instance_usage_audit_log')

    def test_instance_usage_audit_log_with_before(self):
        self.run_command(
            ["instance-usage-audit-log", "--before",
             "2016-12-10 13:59:59.999999"])
        self.assert_called('GET', '/os-instance_usage_audit_log'
                                  '/2016-12-10%2013%3A59%3A59.999999')

    def test_cell_show(self):
        self.run_command('cell-show child_cell')
        self.assert_called('GET', '/os-cells/child_cell')

    def test_cell_capacities_with_cell_name(self):
        self.run_command('cell-capacities --cell child_cell')
        self.assert_called('GET', '/os-cells/child_cell/capacities')

    def test_cell_capacities_without_cell_name(self):
        self.run_command('cell-capacities')
        self.assert_called('GET', '/os-cells/capacities')

    def test_migration_list(self):
        self.run_command('migration-list')
        self.assert_called('GET', '/os-migrations')

    def test_migration_list_v223(self):
        out, _ = self.run_command('migration-list', api_version="2.23")
        self.assert_called('GET', '/os-migrations')
        # Make sure there is no UUID in the output. Uses "| UUID" to
        # avoid collisions with the "Instance UUID" column.
        self.assertNotIn('| UUID', out)

    def test_migration_list_with_filters(self):
        self.run_command('migration-list --host host1 --status finished')
        self.assert_called('GET',
                           '/os-migrations?host=host1&status=finished')

    def test_migration_list_marker_pre_v259_not_allowed(self):
        cmd = 'migration-list --marker %s'
        self.assertRaises(SystemExit, self.run_command,
                          cmd % FAKE_UUID_1, api_version='2.58')

    def test_migration_list_limit_pre_v259_not_allowed(self):
        cmd = 'migration-list --limit 10'
        self.assertRaises(SystemExit, self.run_command,
                          cmd, api_version='2.58')

    def test_migration_list_changes_since_pre_v259_not_allowed(self):
        cmd = 'migration-list --changes-since 2016-02-29T06:23:22'
        self.assertRaises(SystemExit, self.run_command,
                          cmd, api_version='2.58')

    def test_migration_list_limit_marker_v259(self):
        out, _ = self.run_command(
            'migration-list --limit 10 --marker %s' % FAKE_UUID_1,
            api_version='2.59')
        self.assert_called(
            'GET',
            '/os-migrations?limit=10&marker=%s' % FAKE_UUID_1)
        # Make sure the UUID column is now in the output. Uses "| UUID" to
        # avoid collisions with the "Instance UUID" column.
        self.assertIn('| UUID', out)

    def test_migration_list_with_changes_since_v259(self):
        self.run_command('migration-list --changes-since 2016-02-29T06:23:22',
                         api_version='2.59')
        self.assert_called(
            'GET', '/os-migrations?changes-since=2016-02-29T06%3A23%3A22')

    def test_migration_list_with_changes_since_invalid_value_v259(self):
        ex = self.assertRaises(exceptions.CommandError, self.run_command,
                               'migration-list --changes-since 0123456789',
                               api_version='2.59')
        self.assertIn('Invalid changes-since value', six.text_type(ex))

    @mock.patch('novaclient.v2.shell._find_server')
    @mock.patch('os.system')
    def test_ssh(self, mock_system, mock_find_server):
        class FakeResources(object):
            addresses = {
                "skynet": [
                    {'version': 4, 'addr': "1.1.1.1",
                     "OS-EXT-IPS:type": 'fixed'},
                    {'version': 4, 'addr': "2.2.2.2",
                     "OS-EXT-IPS:type": 'floating'},
                    {'version': 6, 'addr': "2607:f0d0:1002::4",
                     "OS-EXT-IPS:type": 'fixed'},
                    {'version': 6, 'addr': "7612:a1b2:2004::6"}
                ]
            }
        mock_find_server.return_value = FakeResources()

        self.run_command("ssh --login bob server")
        mock_system.assert_called_with("ssh -4 -p22  bob@2.2.2.2 ")
        self.run_command("ssh alice@server")
        mock_system.assert_called_with("ssh -4 -p22  alice@2.2.2.2 ")
        self.run_command("ssh --port 202 server")
        mock_system.assert_called_with("ssh -4 -p202  root@2.2.2.2 ")
        self.run_command("ssh --private server")
        mock_system.assert_called_with("ssh -4 -p22  root@1.1.1.1 ")
        self.run_command("ssh -i ~/my_rsa_key server --private")
        mock_system.assert_called_with("ssh -4 -p22 -i ~/my_rsa_key "
                                       "root@1.1.1.1 ")
        self.run_command("ssh --extra-opts -1 server")
        mock_system.assert_called_with("ssh -4 -p22  root@2.2.2.2 -1")

        self.run_command("ssh --ipv6 --login carol server")
        mock_system.assert_called_with("ssh -6 -p22  carol@7612:a1b2:2004::6 ")
        self.run_command("ssh --ipv6 dan@server")
        mock_system.assert_called_with("ssh -6 -p22  dan@7612:a1b2:2004::6 ")
        self.run_command("ssh --ipv6 --port 2022 server")
        mock_system.assert_called_with("ssh -6 -p2022  "
                                       "root@7612:a1b2:2004::6 ")
        self.run_command("ssh --ipv6 --private server")
        mock_system.assert_called_with("ssh -6 -p22  root@2607:f0d0:1002::4 ")
        self.run_command("ssh --ipv6 --identity /home/me/my_dsa_key "
                         "--private server")
        mock_system.assert_called_with("ssh -6 -p22 -i /home/me/my_dsa_key "
                                       "root@2607:f0d0:1002::4 ")
        self.run_command("ssh --ipv6 --private --extra-opts -1 server")
        mock_system.assert_called_with("ssh -6 -p22  "
                                       "root@2607:f0d0:1002::4 -1")

    @mock.patch('novaclient.v2.shell._find_server')
    @mock.patch('os.system')
    def test_ssh_multinet(self, mock_system, mock_find_server):
        class FakeResources(object):
            addresses = {
                "skynet": [
                    {'version': 4, 'addr': "1.1.1.1",
                     "OS-EXT-IPS:type": 'fixed'},
                    {'version': 4, 'addr': "2.2.2.2"},
                    {'version': 6, 'addr': "2607:f0d0:1002::4",
                     "OS-EXT-IPS:type": 'fixed'}
                ],
                "other": [
                    {'version': 4, 'addr': "2.3.4.5"},
                    {'version': 6, 'addr': "7612:a1b2:2004::6"}
                ]
            }
        mock_find_server.return_value = FakeResources()

        self.run_command("ssh --network other server")
        mock_system.assert_called_with("ssh -4 -p22  root@2.3.4.5 ")
        self.run_command("ssh --ipv6 --network other server")
        mock_system.assert_called_with("ssh -6 -p22  root@7612:a1b2:2004::6 ")
        self.assertRaises(exceptions.ResourceNotFound,
                          self.run_command,
                          "ssh --ipv6 --network nonexistent server")

    def _check_keypair_add(self, expected_key_type=None, extra_args='',
                           api_version=None):
        self.run_command("keypair-add %s test" % extra_args,
                         api_version=api_version)
        expected_body = {"keypair": {"name": "test"}}
        if expected_key_type:
            expected_body["keypair"]["type"] = expected_key_type
        self.assert_called("POST", "/os-keypairs", expected_body)

    def test_keypair_add_v20(self):
        self._check_keypair_add(api_version="2.0")

    def test_keypair_add_v22(self):
        self._check_keypair_add('ssh', api_version="2.2")

    def test_keypair_add_ssh(self):
        self._check_keypair_add('ssh', '--key-type ssh', api_version="2.2")

    def test_keypair_add_ssh_x509(self):
        self._check_keypair_add('x509', '--key-type x509', api_version="2.2")

    def _check_keypair_import(self, expected_key_type=None, extra_args='',
                              api_version=None):
        with mock.patch.object(builtins, 'open',
                               mock.mock_open(read_data='FAKE_PUBLIC_KEY')):
            self.run_command('keypair-add --pub-key test.pub %s test' %
                             extra_args, api_version=api_version)
            expected_body = {"keypair": {'public_key': 'FAKE_PUBLIC_KEY',
                                         'name': 'test'}}
            if expected_key_type:
                expected_body["keypair"]["type"] = expected_key_type
            self.assert_called(
                'POST', '/os-keypairs', expected_body)

    def test_keypair_import_v20(self):
        self._check_keypair_import(api_version="2.0")

    def test_keypair_import_v22(self):
        self._check_keypair_import('ssh', api_version="2.2")

    def test_keypair_import_ssh(self):
        self._check_keypair_import('ssh', '--key-type ssh', api_version="2.2")

    def test_keypair_import_x509(self):
        self._check_keypair_import('x509', '--key-type x509',
                                   api_version="2.2")

    def test_keypair_stdin(self):
        with mock.patch('sys.stdin', six.StringIO('FAKE_PUBLIC_KEY')):
            self.run_command('keypair-add --pub-key - test', api_version="2.2")
            self.assert_called(
                'POST', '/os-keypairs', {
                    'keypair':
                        {'public_key': 'FAKE_PUBLIC_KEY', 'name': 'test',
                         'type': 'ssh'}})

    def test_keypair_list(self):
        self.run_command('keypair-list')
        self.assert_called('GET', '/os-keypairs')

    def test_keypair_list_with_user_id(self):
        self.run_command('keypair-list --user test_user', api_version='2.10')
        self.assert_called('GET', '/os-keypairs?user_id=test_user')

    def test_keypair_list_with_limit_and_marker(self):
        self.run_command('keypair-list --marker test_kp --limit 3',
                         api_version='2.35')
        self.assert_called('GET', '/os-keypairs?limit=3&marker=test_kp')

    def test_keypair_list_with_user_id_limit_and_marker(self):
        self.run_command('keypair-list --user test_user --marker test_kp '
                         '--limit 3', api_version='2.35')
        self.assert_called(
            'GET', '/os-keypairs?limit=3&marker=test_kp&user_id=test_user')

    def test_keypair_show(self):
        self.run_command('keypair-show test')
        self.assert_called('GET', '/os-keypairs/test')

    def test_keypair_delete(self):
        self.run_command('keypair-delete test')
        self.assert_called('DELETE', '/os-keypairs/test')

    def test_create_server_group(self):
        self.run_command('server-group-create wjsg affinity')
        self.assert_called('POST', '/os-server-groups',
                           {'server_group': {'name': 'wjsg',
                                             'policies': ['affinity']}})

    def test_delete_multi_server_groups(self):
        self.run_command('server-group-delete 12345 56789')
        self.assert_called('DELETE', '/os-server-groups/56789')
        self.assert_called('DELETE', '/os-server-groups/12345', pos=-2)

    def test_list_server_group(self):
        self.run_command('server-group-list')
        self.assert_called('GET', '/os-server-groups')

    def test_list_server_group_with_all_projects(self):
        self.run_command('server-group-list --all-projects')
        self.assert_called('GET', '/os-server-groups?all_projects=True')

    def test_list_server_group_with_limit_and_offset(self):
        self.run_command('server-group-list --limit 20 --offset 5')
        self.assert_called('GET', '/os-server-groups?limit=20&offset=5')

    def test_versions(self):
        exclusions = set([
            1,   # Same as version 2.0
            3,   # doesn't require any changes in novaclient
            4,   # fixed-ip-get command is gone
            5,   # doesn't require any changes in novaclient
            7,   # doesn't require any changes in novaclient
            9,   # doesn't require any changes in novaclient
            12,  # no longer supported
            15,  # doesn't require any changes in novaclient
            16,  # doesn't require any changes in novaclient
            18,  # NOTE(andreykurilin): this microversion requires changes in
                 #   HttpClient and our SessionClient, which is based on
                 #   keystoneauth1.session. Skipping this complicated change
                 #   allows to unblock implementation further microversions
                 #   before feature-freeze
                 #   (we can do it, since nova-api change didn't actually add
                 #   new microversion, just an additional checks. See
                 #   https://review.openstack.org/#/c/233076/ for more details)
            20,  # doesn't require any changes in novaclient
            27,  # NOTE(cdent): 27 adds support for updated microversion
                 #   headers, and is tested in test_api_versions, but is
                 #   not explicitly tested via wraps and _SUBSTITUTIONS.
            28,  # doesn't require any changes in novaclient
            31,  # doesn't require any changes in novaclient
            32,  # doesn't require separate version-wrapped methods in
                 # novaclient
            34,  # doesn't require any changes in novaclient
            37,  # There are no versioned wrapped shell method changes for this
            38,  # doesn't require any changes in novaclient
            39,  # There are no versioned wrapped shell method changes for this
            41,  # There are no version-wrapped shell method changes for this.
            42,  # There are no version-wrapped shell method changes for this.
            43,  # There are no version-wrapped shell method changes for this.
            44,  # There are no version-wrapped shell method changes for this.
            45,  # There are no version-wrapped shell method changes for this.
            46,  # There are no version-wrapped shell method changes for this.
            47,  # NOTE(cfriesen): 47 adds support for flavor details embedded
                 # within the server details
            48,  # There are no version-wrapped shell method changes for this.
            51,  # There are no version-wrapped shell method changes for this.
            52,  # There are no version-wrapped shell method changes for this.
            54,  # There are no version-wrapped shell method changes for this.
            57,  # There are no version-wrapped shell method changes for this.
            60,  # There are no client-side changes for volume multiattach.
            61,  # There are no version-wrapped shell method changes for this.
        ])
        versions_supported = set(range(0,
                                 novaclient.API_MAX_VERSION.ver_minor + 1))

        versions_covered = set()
        for key, values in api_versions._SUBSTITUTIONS.items():
            for value in values:
                if value.start_version.ver_major == 2:
                    versions_covered.add(value.start_version.ver_minor)

        versions_not_covered = versions_supported - versions_covered
        unaccounted_for = versions_not_covered - exclusions

        failure_msg = ('Minor versions %s have been skipped.  Please do not '
                       'raise API_MAX_VERSION without adding support or '
                       'excluding them.' % sorted(unaccounted_for))
        self.assertEqual(set([]), unaccounted_for, failure_msg)

    def test_list_v2_10(self):
        self.run_command('list', api_version='2.10')
        self.assert_called('GET', '/servers/detail', pos=0)
        self.assert_called('GET', '/servers/detail?marker=9014')

    def test_server_tag_add(self):
        self.run_command('server-tag-add sample-server tag',
                         api_version='2.26')
        self.assert_called('PUT', '/servers/1234/tags/tag', None)

    def test_server_tag_add_many(self):
        self.run_command('server-tag-add sample-server tag1 tag2 tag3',
                         api_version='2.26')
        self.assert_called('PUT', '/servers/1234/tags/tag1', None, pos=-3)
        self.assert_called('PUT', '/servers/1234/tags/tag2', None, pos=-2)
        self.assert_called('PUT', '/servers/1234/tags/tag3', None, pos=-1)

    def test_server_tag_set(self):
        self.run_command('server-tag-set sample-server tag1 tag2',
                         api_version='2.26')
        self.assert_called('PUT', '/servers/1234/tags',
                           {'tags': ['tag1', 'tag2']})

    def test_server_tag_list(self):
        self.run_command('server-tag-list sample-server', api_version='2.26')
        self.assert_called('GET', '/servers/1234/tags')

    def test_server_tag_delete(self):
        self.run_command('server-tag-delete sample-server tag',
                         api_version='2.26')
        self.assert_called('DELETE', '/servers/1234/tags/tag')

    def test_server_tag_delete_many(self):
        self.run_command('server-tag-delete sample-server tag1 tag2 tag3',
                         api_version='2.26')
        self.assert_called('DELETE', '/servers/1234/tags/tag1', pos=-3)
        self.assert_called('DELETE', '/servers/1234/tags/tag2', pos=-2)
        self.assert_called('DELETE', '/servers/1234/tags/tag3', pos=-1)

    def test_server_tag_delete_all(self):
        self.run_command('server-tag-delete-all sample-server',
                         api_version='2.26')
        self.assert_called('DELETE', '/servers/1234/tags')

    def test_list_v2_26_tags(self):
        self.run_command('list --tags tag1,tag2', api_version='2.26')
        self.assert_called(
            'GET',
            '/servers/detail?tags=tag1%2Ctag2',
            pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?marker=9014&tags=tag1%2Ctag2')

    def test_list_v2_26_tags_any(self):
        self.run_command('list --tags-any tag1,tag2', api_version='2.26')
        self.assert_called(
            'GET',
            '/servers/detail?tags-any=tag1%2Ctag2',
            pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?marker=9014&tags-any=tag1%2Ctag2')

    def test_list_v2_26_not_tags(self):
        self.run_command('list --not-tags tag1,tag2', api_version='2.26')
        self.assert_called(
            'GET',
            '/servers/detail?not-tags=tag1%2Ctag2',
            pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?marker=9014&not-tags=tag1%2Ctag2')

    def test_list_v2_26_not_tags_any(self):
        self.run_command('list --not-tags-any tag1,tag2', api_version='2.26')
        self.assert_called(
            'GET',
            '/servers/detail?not-tags-any=tag1%2Ctag2',
            pos=0)
        self.assert_called(
            'GET',
            '/servers/detail?marker=9014&not-tags-any=tag1%2Ctag2')


class PollForStatusTestCase(utils.TestCase):
    @mock.patch("novaclient.v2.shell.time")
    def test_simple_usage(self, mock_time):
        poll_period = 3
        some_id = "uuuuuuuuuuuiiiiiiiii"
        updated_objects = (
            base.Resource(None, info={"not_default_field": "INPROGRESS"}),
            base.Resource(None, info={"not_default_field": "OK"}))
        poll_fn = mock.MagicMock(side_effect=updated_objects)

        novaclient.v2.shell._poll_for_status(
            poll_fn=poll_fn,
            obj_id=some_id,
            status_field="not_default_field",
            final_ok_states=["ok"],
            poll_period=poll_period,
            # just want to test printing in separate tests
            action="some",
            silent=True,
            show_progress=False
        )
        self.assertEqual([mock.call(poll_period)],
                         mock_time.sleep.call_args_list)
        self.assertEqual([mock.call(some_id)] * 2, poll_fn.call_args_list)

    @mock.patch("novaclient.v2.shell.sys.stdout")
    @mock.patch("novaclient.v2.shell.time")
    def test_print_progress(self, mock_time, mock_stdout):
        updated_objects = (
            base.Resource(None, info={"status": "INPROGRESS", "progress": 0}),
            base.Resource(None, info={"status": "INPROGRESS", "progress": 50}),
            base.Resource(None, info={"status": "OK", "progress": 100}))
        poll_fn = mock.MagicMock(side_effect=updated_objects)
        action = "some"

        novaclient.v2.shell._poll_for_status(
            poll_fn=poll_fn,
            obj_id="uuuuuuuuuuuiiiiiiiii",
            final_ok_states=["ok"],
            poll_period="3",
            action=action,
            show_progress=True,
            silent=False)

        stdout_arg_list = [
            mock.call("\n"),
            mock.call("\rServer %s... 0%% complete" % action),
            mock.call("\rServer %s... 50%% complete" % action),
            mock.call("\rServer %s... 100%% complete" % action),
            mock.call("\nFinished"),
            mock.call("\n")]
        self.assertEqual(
            stdout_arg_list,
            mock_stdout.write.call_args_list
        )

    @mock.patch("novaclient.v2.shell.time")
    def test_error_state(self, mock_time):
        fault_msg = "Oops"
        updated_objects = (
            base.Resource(None, info={"status": "error",
                                      "fault": {"message": fault_msg}}),
            base.Resource(None, info={"status": "error"}))
        poll_fn = mock.MagicMock(side_effect=updated_objects)
        action = "some"

        self.assertRaises(exceptions.ResourceInErrorState,
                          novaclient.v2.shell._poll_for_status,
                          poll_fn=poll_fn,
                          obj_id="uuuuuuuuuuuiiiiiiiii",
                          final_ok_states=["ok"],
                          poll_period="3",
                          action=action,
                          show_progress=True,
                          silent=False)

        self.assertRaises(exceptions.ResourceInErrorState,
                          novaclient.v2.shell._poll_for_status,
                          poll_fn=poll_fn,
                          obj_id="uuuuuuuuuuuiiiiiiiii",
                          final_ok_states=["ok"],
                          poll_period="3",
                          action=action,
                          show_progress=True,
                          silent=False)

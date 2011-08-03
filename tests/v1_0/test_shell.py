
import os
import mock

from novaclient.shell import OpenStackComputeShell
from novaclient import exceptions
from tests.v1_0 import fakes
from tests import utils


class ShellTest(utils.TestCase):

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        global _old_env
        fake_env = {
            'NOVA_USERNAME': 'username',
            'NOVA_API_KEY': 'password',
            'NOVA_PROJECT_ID': 'project_id'
        }
        _old_env, os.environ = os.environ, fake_env.copy()

        # Make a fake shell object, a helping wrapper to call it, and a quick way
        # of asserting that certain API calls were made.
        global shell, _shell, assert_called, assert_called_anytime
        _shell = OpenStackComputeShell()
        _shell._api_class = fakes.FakeClient
        assert_called = lambda m, u, b=None: _shell.cs.assert_called(m, u, b)
        assert_called_anytime = lambda m, u, b=None: \
                                    _shell.cs.assert_called_anytime(m, u, b)

        def shell(cmd):
            command = ['--version=1.0',]
            command.extend(cmd.split())
            _shell.main(command)

    def tearDown(self):
        global _old_env
        os.environ = _old_env

    def test_backup_schedule(self):
        shell('backup-schedule 1234')
        assert_called('GET', '/servers/1234/backup_schedule')

        shell('backup-schedule sample-server --weekly monday')
        assert_called(
            'POST', '/servers/1234/backup_schedule',
            {'backupSchedule': {'enabled': True, 'daily': 'DISABLED',
                                'weekly': 'MONDAY'}}
        )

        shell('backup-schedule sample-server '
              '--weekly disabled --daily h_0000_0200')
        assert_called(
            'POST', '/servers/1234/backup_schedule',
            {'backupSchedule': {'enabled': True, 'daily': 'H_0000_0200',
                                'weekly': 'DISABLED'}}
        )

        shell('backup-schedule sample-server --disable')
        assert_called(
            'POST', '/servers/1234/backup_schedule',
            {'backupSchedule': {'enabled': False, 'daily': 'DISABLED',
                                'weekly': 'DISABLED'}}
        )

    def test_backup_schedule_delete(self):
        shell('backup-schedule-delete 1234')
        assert_called('DELETE', '/servers/1234/backup_schedule')

    def test_boot(self):
        shell('boot --image 1 some-server')
        assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
             'min_count': 1, 'max_count': 1}}
        )

        shell('boot --image 1 --meta foo=bar --meta spam=eggs some-server ')
        assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                        'min_count': 1, 'max_count': 1,
                        'metadata': {'foo': 'bar', 'spam': 'eggs'}}}
        )

    def test_boot_files(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        expected_file_data = open(testfile).read().encode('base64')

        shell('boot some-server --image 1 --file /tmp/foo=%s --file /tmp/bar=%s' %
                                                             (testfile, testfile))

        assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                        'min_count': 1, 'max_count': 1,
                        'personality': [
                            {'path': '/tmp/bar', 'contents': expected_file_data},
                            {'path': '/tmp/foo', 'contents': expected_file_data}
                        ]}
            }
        )

    def test_boot_invalid_file(self):
        invalid_file = os.path.join(os.path.dirname(__file__), 'asdfasdfasdfasdf')
        self.assertRaises(exceptions.CommandError, shell, 'boot some-server --image 1 '
                                               '--file /foo=%s' % invalid_file)

    def test_boot_key_auto(self):
        mock_exists = mock.Mock(return_value=True)
        mock_open = mock.Mock()
        mock_open.return_value = mock.Mock()
        mock_open.return_value.read = mock.Mock(return_value='SSHKEY')

        @mock.patch('os.path.exists', mock_exists)
        @mock.patch('__builtin__.open', mock_open)
        def test_shell_call():
            shell('boot some-server --image 1 --key')
            assert_called(
                'POST', '/servers',
                {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                            'min_count': 1, 'max_count': 1,
                            'personality': [{
                                'path': '/root/.ssh/authorized_keys2',
                                'contents': ('SSHKEY').encode('base64')},
                            ]}
                }
            )

        test_shell_call()

    def test_boot_key_auto_no_keys(self):
        mock_exists = mock.Mock(return_value=False)

        @mock.patch('os.path.exists', mock_exists)
        def test_shell_call():
            self.assertRaises(exceptions.CommandError, shell,
                              'boot some-server --image 1 --key')

        test_shell_call()

    def test_boot_key_file(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        expected_file_data = open(testfile).read().encode('base64')
        shell('boot some-server --image 1 --key %s' % testfile)
        assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                        'min_count': 1, 'max_count': 1,
                        'personality': [
                            {'path': '/root/.ssh/authorized_keys2', 'contents':
                             expected_file_data},
                        ]}
            }
        )

    def test_boot_invalid_keyfile(self):
        invalid_file = os.path.join(os.path.dirname(__file__), 'asdfasdfasdfasdf')
        self.assertRaises(exceptions.CommandError, shell, 'boot some-server '
                                               '--image 1 --key %s' % invalid_file)

    def test_boot_ipgroup(self):
        shell('boot --image 1 --ipgroup 1 some-server')
        assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                        'sharedIpGroupId': 1, 'min_count': 1, 'max_count': 1}}
        )

    def test_boot_ipgroup_name(self):
        shell('boot --image 1 --ipgroup group1 some-server')
        assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                        'sharedIpGroupId': 1, 'min_count': 1, 'max_count': 1}}
        )

    def test_flavor_list(self):
        shell('flavor-list')
        assert_called_anytime('GET', '/flavors/detail')

    def test_image_list(self):
        shell('image-list')
        assert_called('GET', '/images/detail')

    def test_snapshot_create(self):
        shell('image-create sample-server mysnapshot')
        assert_called(
            'POST', '/images',
            {'image': {'name': 'mysnapshot', 'serverId': 1234}}
        )

    def test_image_delete(self):
        shell('image-delete 1')
        assert_called('DELETE', '/images/1')

    def test_ip_share(self):
        shell('ip-share sample-server 1 1.2.3.4')
        assert_called(
            'PUT', '/servers/1234/ips/public/1.2.3.4',
            {'shareIp': {'sharedIpGroupId': 1, 'configureServer': True}}
        )

    def test_ip_unshare(self):
        shell('ip-unshare sample-server 1.2.3.4')
        assert_called('DELETE', '/servers/1234/ips/public/1.2.3.4')

    def test_ipgroup_list(self):
        shell('ipgroup-list')
        assert ('GET', '/shared_ip_groups/detail', None) in \
                  _shell.cs.client.callstack
        assert_called('GET', '/servers/5678')

    def test_ipgroup_show(self):
        shell('ipgroup-show 1')
        assert_called('GET', '/shared_ip_groups/1')
        shell('ipgroup-show group2')
        # does a search, not a direct GET
        assert_called('GET', '/shared_ip_groups/detail')

    def test_ipgroup_create(self):
        shell('ipgroup-create a-group')
        assert_called(
            'POST', '/shared_ip_groups',
            {'sharedIpGroup': {'name': 'a-group'}}
        )
        shell('ipgroup-create a-group sample-server')
        assert_called(
            'POST', '/shared_ip_groups',
            {'sharedIpGroup': {'name': 'a-group', 'server': 1234}}
        )

    def test_ipgroup_delete(self):
        shell('ipgroup-delete group1')
        assert_called('DELETE', '/shared_ip_groups/1')

    def test_list(self):
        shell('list')
        assert_called('GET', '/servers/detail')

    def test_reboot(self):
        shell('reboot sample-server')
        assert_called('POST', '/servers/1234/action', {'reboot': {'type': 'SOFT'}})
        shell('reboot sample-server --hard')
        assert_called('POST', '/servers/1234/action', {'reboot': {'type': 'HARD'}})

    def test_rebuild(self):
        shell('rebuild sample-server 1')
        assert_called('POST', '/servers/1234/action', {'rebuild': {'imageId': 1}})

    def test_rename(self):
        shell('rename sample-server newname')
        assert_called('PUT', '/servers/1234', {'server': {'name': 'newname'}})

    def test_resize(self):
        shell('resize sample-server 1')
        assert_called('POST', '/servers/1234/action', {'resize': {'flavorId': 1}})

    def test_resize_confirm(self):
        shell('resize-confirm sample-server')
        assert_called('POST', '/servers/1234/action', {'confirmResize': None})

    def test_resize_revert(self):
        shell('resize-revert sample-server')
        assert_called('POST', '/servers/1234/action', {'revertResize': None})

    def test_backup(self):
        shell('backup sample-server mybackup daily 1')
        assert_called(
            'POST', '/servers/1234/action',
            {'createBackup': {'name': 'mybackup', 'backup_type': 'daily',
                              'rotation': 1}}
        )

    @mock.patch('getpass.getpass', mock.Mock(return_value='p'))
    def test_root_password(self):
        shell('root-password sample-server')
        assert_called('PUT', '/servers/1234', {'server': {'adminPass': 'p'}})

    def test_show(self):
        shell('show 1234')
        # XXX need a way to test multiple calls
        # assert_called('GET', '/servers/1234')
        assert_called('GET', '/images/2')

    def test_delete(self):
        shell('delete 1234')
        assert_called('DELETE', '/servers/1234')
        shell('delete sample-server')
        assert_called('DELETE', '/servers/1234')

    def test_zone(self):
        shell('zone 1')
        assert_called('GET', '/zones/1')

        shell('zone 1 --api_url=http://zzz --zone_username=frank --password=xxx')
        assert_called(
            'PUT', '/zones/1',
            {'zone': {'api_url': 'http://zzz', 'username': 'frank',
                      'password': 'xxx'}}
        )

    def test_zone_add(self):
        shell('zone-add http://zzz frank xxx 0.0 1.0')
        assert_called(
            'POST', '/zones',
            {'zone': {'api_url': 'http://zzz', 'username': 'frank',
                      'password': 'xxx',
                      'weight_offset': '0.0', 'weight_scale': '1.0'}}
        )

    def test_zone_delete(self):
        shell('zone-delete 1')
        assert_called('DELETE', '/zones/1')

    def test_zone_list(self):
        shell('zone-list')
        assert ('GET', '/zones/detail', None) in _shell.cs.client.callstack

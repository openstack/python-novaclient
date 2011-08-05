
import os
import mock

from novaclient.shell import OpenStackComputeShell
from novaclient import exceptions
from tests.v1_0 import fakes
from tests import utils


class ShellTest(utils.TestCase):

    def setUp(self):
        """Run before each test."""
        self.old_environment = os.environ.copy()
        os.environ = {
            'NOVA_USERNAME': 'username',
            'NOVA_API_KEY': 'password',
            'NOVA_PROJECT_ID': 'project_id',
            'NOVA_VERSION': '1.0',
        }

        self.shell = OpenStackComputeShell()
        self.shell.get_api_class = lambda *_: fakes.FakeClient

    def tearDown(self):
        os.environ = self.old_environment

    def run_command(self, cmd):
        self.shell.main(cmd.split())

    def assert_called(self, method, url, body=None):
        return self.shell.cs.assert_called(method, url, body)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test_backup_schedule(self):
        self.run_command('backup-schedule 1234')
        self.assert_called('GET', '/servers/1234/backup_schedule')

        self.run_command('backup-schedule sample-server --weekly monday')
        self.assert_called(
            'POST', '/servers/1234/backup_schedule',
            {'backupSchedule': {'enabled': True, 'daily': 'DISABLED',
                                'weekly': 'MONDAY'}}
        )

        self.run_command('backup-schedule sample-server '
              '--weekly disabled --daily h_0000_0200')
        self.assert_called(
            'POST', '/servers/1234/backup_schedule',
            {'backupSchedule': {'enabled': True, 'daily': 'H_0000_0200',
                                'weekly': 'DISABLED'}}
        )

        self.run_command('backup-schedule sample-server --disable')
        self.assert_called(
            'POST', '/servers/1234/backup_schedule',
            {'backupSchedule': {'enabled': False, 'daily': 'DISABLED',
                                'weekly': 'DISABLED'}}
        )

    def test_backup_schedule_delete(self):
        self.run_command('backup-schedule-delete 1234')
        self.assert_called('DELETE', '/servers/1234/backup_schedule')

    def test_boot(self):
        self.run_command('boot --image 1 some-server')
        self.assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
             'min_count': 1, 'max_count': 1}}
        )

        self.run_command('boot --image 1 --meta foo=bar --meta spam=eggs some-server ')
        self.assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                        'min_count': 1, 'max_count': 1,
                        'metadata': {'foo': 'bar', 'spam': 'eggs'}}}
        )

    def test_boot_files(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        expected_file_data = open(testfile).read().encode('base64')

        self.run_command('boot some-server --image 1 --file /tmp/foo=%s --file /tmp/bar=%s' %
                                                             (testfile, testfile))

        self.assert_called(
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
        self.assertRaises(exceptions.CommandError, self.run_command, 'boot some-server --image 1 '
                                               '--file /foo=%s' % invalid_file)

    def test_boot_key_auto(self):
        mock_exists = mock.Mock(return_value=True)
        mock_open = mock.Mock()
        mock_open.return_value = mock.Mock()
        mock_open.return_value.read = mock.Mock(return_value='SSHKEY')

        @mock.patch('os.path.exists', mock_exists)
        @mock.patch('__builtin__.open', mock_open)
        def test_shell_call():
            self.run_command('boot some-server --image 1 --key')
            self.assert_called(
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
            self.assertRaises(exceptions.CommandError, self.run_command,
                              'boot some-server --image 1 --key')

        test_shell_call()

    def test_boot_key_file(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        expected_file_data = open(testfile).read().encode('base64')
        self.run_command('boot some-server --image 1 --key %s' % testfile)
        self.assert_called(
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
        self.assertRaises(exceptions.CommandError, self.run_command, 'boot some-server '
                                               '--image 1 --key %s' % invalid_file)

    def test_boot_ipgroup(self):
        self.run_command('boot --image 1 --ipgroup 1 some-server')
        self.assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                        'sharedIpGroupId': 1, 'min_count': 1, 'max_count': 1}}
        )

    def test_boot_ipgroup_name(self):
        self.run_command('boot --image 1 --ipgroup group1 some-server')
        self.assert_called(
            'POST', '/servers',
            {'server': {'flavorId': 1, 'name': 'some-server', 'imageId': '1',
                        'sharedIpGroupId': 1, 'min_count': 1, 'max_count': 1}}
        )

    def test_flavor_list(self):
        self.run_command('flavor-list')
        self.assert_called_anytime('GET', '/flavors/detail')

    def test_image_list(self):
        self.run_command('image-list')
        self.assert_called('GET', '/images/detail')

    def test_snapshot_create(self):
        self.run_command('image-create sample-server mysnapshot')
        self.assert_called(
            'POST', '/images',
            {'image': {'name': 'mysnapshot', 'serverId': 1234}}
        )

    def test_image_delete(self):
        self.run_command('image-delete 1')
        self.assert_called('DELETE', '/images/1')

    def test_ip_share(self):
        self.run_command('ip-share sample-server 1 1.2.3.4')
        self.assert_called(
            'PUT', '/servers/1234/ips/public/1.2.3.4',
            {'shareIp': {'sharedIpGroupId': 1, 'configureServer': True}}
        )

    def test_ip_unshare(self):
        self.run_command('ip-unshare sample-server 1.2.3.4')
        self.assert_called('DELETE', '/servers/1234/ips/public/1.2.3.4')

    def test_ipgroup_list(self):
        self.run_command('ipgroup-list')
        assert ('GET', '/shared_ip_groups/detail', None) in \
                  self.shell.cs.client.callstack
        self.assert_called('GET', '/servers/5678')

    def test_ipgroup_show(self):
        self.run_command('ipgroup-show 1')
        self.assert_called('GET', '/shared_ip_groups/1')
        self.run_command('ipgroup-show group2')
        # does a search, not a direct GET
        self.assert_called('GET', '/shared_ip_groups/detail')

    def test_ipgroup_create(self):
        self.run_command('ipgroup-create a-group')
        self.assert_called(
            'POST', '/shared_ip_groups',
            {'sharedIpGroup': {'name': 'a-group'}}
        )
        self.run_command('ipgroup-create a-group sample-server')
        self.assert_called(
            'POST', '/shared_ip_groups',
            {'sharedIpGroup': {'name': 'a-group', 'server': 1234}}
        )

    def test_ipgroup_delete(self):
        self.run_command('ipgroup-delete group1')
        self.assert_called('DELETE', '/shared_ip_groups/1')

    def test_list(self):
        self.run_command('list')
        self.assert_called('GET', '/servers/detail')

    def test_reboot(self):
        self.run_command('reboot sample-server')
        self.assert_called('POST', '/servers/1234/action', {'reboot': {'type': 'SOFT'}})
        self.run_command('reboot sample-server --hard')
        self.assert_called('POST', '/servers/1234/action', {'reboot': {'type': 'HARD'}})

    def test_rebuild(self):
        self.run_command('rebuild sample-server 1')
        self.assert_called('POST', '/servers/1234/action', {'rebuild': {'imageId': 1}})

    def test_rename(self):
        self.run_command('rename sample-server newname')
        self.assert_called('PUT', '/servers/1234', {'server': {'name': 'newname'}})

    def test_resize(self):
        self.run_command('resize sample-server 1')
        self.assert_called('POST', '/servers/1234/action', {'resize': {'flavorId': 1}})

    def test_resize_confirm(self):
        self.run_command('resize-confirm sample-server')
        self.assert_called('POST', '/servers/1234/action', {'confirmResize': None})

    def test_resize_revert(self):
        self.run_command('resize-revert sample-server')
        self.assert_called('POST', '/servers/1234/action', {'revertResize': None})

    def test_backup(self):
        self.run_command('backup sample-server mybackup daily 1')
        self.assert_called(
            'POST', '/servers/1234/action',
            {'createBackup': {'name': 'mybackup', 'backup_type': 'daily',
                              'rotation': 1}}
        )

    @mock.patch('getpass.getpass', mock.Mock(return_value='p'))
    def test_root_password(self):
        self.run_command('root-password sample-server')
        self.assert_called('PUT', '/servers/1234', {'server': {'adminPass': 'p'}})

    def test_show(self):
        self.run_command('show 1234')
        # XXX need a way to test multiple calls
        # self.assert_called('GET', '/servers/1234')
        self.assert_called('GET', '/images/2')

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/servers/1234')
        self.run_command('delete sample-server')
        self.assert_called('DELETE', '/servers/1234')

    def test_zone(self):
        self.run_command('zone 1')
        self.assert_called('GET', '/zones/1')

        self.run_command('zone 1 --api_url=http://zzz --zone_username=frank --password=xxx')
        self.assert_called(
            'PUT', '/zones/1',
            {'zone': {'api_url': 'http://zzz', 'username': 'frank',
                      'password': 'xxx'}}
        )

    def test_zone_add(self):
        self.run_command('zone-add http://zzz frank xxx 0.0 1.0')
        self.assert_called(
            'POST', '/zones',
            {'zone': {'api_url': 'http://zzz', 'username': 'frank',
                      'password': 'xxx',
                      'weight_offset': '0.0', 'weight_scale': '1.0'}}
        )

    def test_zone_delete(self):
        self.run_command('zone-delete 1')
        self.assert_called('DELETE', '/zones/1')

    def test_zone_list(self):
        self.run_command('zone-list')
        assert ('GET', '/zones/detail', None) in self.shell.cs.client.callstack

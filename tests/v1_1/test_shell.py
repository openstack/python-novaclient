import os
import mock
import sys
import tempfile

import novaclient.shell
import novaclient.client
from novaclient import exceptions
from tests.v1_1 import fakes
from tests import utils


class ShellTest(utils.TestCase):

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        """Run before each test."""
        self.old_environment = os.environ.copy()
        os.environ = {
            'NOVA_USERNAME': 'username',
            'NOVA_PASSWORD': 'password',
            'NOVA_PROJECT_ID': 'project_id',
            'NOVA_VERSION': '1.1',
            'NOVA_URL': 'http://no.where',
        }

        self.shell = novaclient.shell.OpenStackComputeShell()

        #HACK(bcwaldon): replace this when we start using stubs
        self.old_get_client_class = novaclient.client.get_client_class
        novaclient.client.get_client_class = lambda *_: fakes.FakeClient

    def tearDown(self):
        os.environ = self.old_environment
        # For some method like test_image_meta_bad_action we are
        # testing a SystemExit to be thrown and object self.shell has
        # no time to get instantatiated which is OK in this case, so
        # we make sure the method is there before launching it.
        if hasattr(self.shell, 'cs'):
            self.shell.cs.clear_callstack()

        #HACK(bcwaldon): replace this when we start using stubs
        novaclient.client.get_client_class = self.old_get_client_class

    def run_command(self, cmd):
        self.shell.main(cmd.split())

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

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

        self.run_command('boot --image 1 --flavor 1 --meta foo=bar'
                         ' --meta spam=eggs some-server ')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'metadata': {'foo': 'bar', 'spam': 'eggs'},
                'min_count': 1,
                'max_count': 1,
            }},
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

    def test_boot_key_auto(self):
        mock_exists = mock.Mock(return_value=True)
        mock_open = mock.Mock()
        mock_open.return_value = mock.Mock()
        mock_open.return_value.read = mock.Mock(return_value='SSHKEY')

        @mock.patch('os.path.exists', mock_exists)
        @mock.patch('__builtin__.open', mock_open)
        def test_shell_call():
            cmd = 'boot some-server --flavor 1 --image 1 --key_path'
            self.run_command(cmd)
            self.assert_called_anytime(
                'POST', '/servers',
                {'server': {
                    'flavorRef': '1',
                    'name': 'some-server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 1,
                    'personality': [{
                        'path': '/root/.ssh/authorized_keys2',
                        'contents': ('SSHKEY').encode('base64')},
                    ]},
                },
            )

        test_shell_call()

    def test_boot_key_auto_no_keys(self):
        mock_exists = mock.Mock(return_value=False)

        @mock.patch('os.path.exists', mock_exists)
        def test_shell_call():
            cmd = 'boot some-server --flavor 1 --image 1 --key_path'
            self.assertRaises(exceptions.CommandError, self.run_command, cmd)

        test_shell_call()

    def test_boot_key_file(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        expected_file_data = open(testfile).read().encode('base64')
        cmd = 'boot some-server --flavor 1 --image 1 --key_path %s'
        self.run_command(cmd % testfile)
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': '1',
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                'personality': [
                    {'path': '/root/.ssh/authorized_keys2',
                     'contents':expected_file_data},
                 ]},
            },
        )

    def test_boot_invalid_keyfile(self):
        invalid_file = os.path.join(os.path.dirname(__file__),
                                    'asdfasdfasdfasdf')
        cmd = 'boot some-server --flavor 1 --image 1 --key_path %s'
        self.assertRaises(exceptions.CommandError, self.run_command,
                          cmd % invalid_file)

    def test_flavor_list(self):
        self.run_command('flavor-list')
        self.assert_called_anytime('GET', '/flavors/detail')

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

        self.run_command('rebuild sample-server 1 --rebuild_password asdf')
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

    def test_show(self):
        self.run_command('show 1234')
        self.assert_called('GET', '/servers/1234', pos=-3)
        self.assert_called('GET', '/flavors/1', pos=-2)
        self.assert_called('GET', '/images/2')

    def test_show_bad_id(self):
        self.assertRaises(exceptions.CommandError,
                          self.run_command, 'show xxx')

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/servers/1234')
        self.run_command('delete sample-server')
        self.assert_called('DELETE', '/servers/1234')

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
        self.run_command('dns-create zone1 testname 192.168.1.1')
        self.assert_called('POST', '/os-floating-ip-dns')

        self.run_command('dns-create zone1 tn 192.168.1.1 --type A')
        self.assert_called('POST', '/os-floating-ip-dns')

    def test_dns_delete(self):
        self.run_command('dns-delete zone1 testname')
        self.assert_called('DELETE', '/os-floating-ip-dns/zone1?name=testname')

    def test_dns_list(self):
        self.run_command('dns-list zone1 --ip 192.168.1.1')
        self.assert_called('GET', '/os-floating-ip-dns/zone1?ip=192.168.1.1')

        self.run_command('dns-list zone1 --name testname')
        self.assert_called('GET', '/os-floating-ip-dns/zone1?name=testname')

    def test_dns_zones(self):
        self.run_command('dns-zones')
        self.assert_called('GET', '/os-floating-ip-dns')

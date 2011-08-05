
import os
import mock

from novaclient.shell import OpenStackComputeShell
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
            'NOVA_API_KEY': 'password',
            'NOVA_PROJECT_ID': 'project_id',
            'NOVA_VERSION': '1.1',
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

    def test_boot(self):
        self.run_command('boot --image 1 some-server')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': 1,
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
            }}
        )

        self.run_command('boot --image 1 --meta foo=bar --meta spam=eggs some-server ')
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': 1,
                'name': 'some-server',
                'imageRef': '1',
                'metadata': {'foo': 'bar', 'spam': 'eggs'},
                'min_count': 1,
                'max_count': 1,
            }}
        )

    def test_boot_files(self):
        testfile = os.path.join(os.path.dirname(__file__), 'testfile.txt')
        expected_file_data = open(testfile).read().encode('base64')

        cmd = 'boot some-server --image 1 --file /tmp/foo=%s --file /tmp/bar=%s'
        self.run_command(cmd % (testfile, testfile))

        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': 1,
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                'personality': [
                   {'path': '/tmp/bar', 'contents': expected_file_data},
                   {'path': '/tmp/foo', 'contents': expected_file_data}
                ]}
            }
        )

    def test_boot_invalid_file(self):
        invalid_file = os.path.join(os.path.dirname(__file__), 'asdfasdfasdfasdf')
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
            self.run_command('boot some-server --image 1 --key')
            self.assert_called_anytime(
                'POST', '/servers',
                {'server': {
                    'flavorRef': 1,
                    'name': 'some-server',
                    'imageRef': '1',
                    'min_count': 1,
                    'max_count': 1,
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
        self.assert_called_anytime(
            'POST', '/servers',
            {'server': {
                'flavorRef': 1,
                'name': 'some-server',
                'imageRef': '1',
                'min_count': 1,
                'max_count': 1,
                'personality': [
                    {'path': '/root/.ssh/authorized_keys2',
                     'contents':expected_file_data},
                 ]}
            }
        )

    def test_boot_invalid_keyfile(self):
        invalid_file = os.path.join(os.path.dirname(__file__), 'asdfasdfasdfasdf')
        self.assertRaises(exceptions.CommandError, self.run_command, 'boot some-server '
                                               '--image 1 --key %s' % invalid_file)

    def test_flavor_list(self):
        self.run_command('flavor-list')
        self.assert_called_anytime('GET', '/flavors/detail')

    def test_image_list(self):
        self.run_command('image-list')
        self.assert_called('GET', '/images/detail')

    def test_create_image(self):
        self.run_command('image-create sample-server mysnapshot')
        self.assert_called(
            'POST', '/servers/1234/action',
            {'createImage': {'name': 'mysnapshot', 'metadata': {}}}
        )

    def test_image_delete(self):
        self.run_command('image-delete 1')
        self.assert_called('DELETE', '/images/1')

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
        self.assert_called('POST', '/servers/1234/action', {'rebuild': {'imageRef': 1}})

    def test_rename(self):
        self.run_command('rename sample-server newname')
        self.assert_called('PUT', '/servers/1234', {'server': {'name': 'newname'}})

    def test_resize(self):
        self.run_command('resize sample-server 1')
        self.assert_called('POST', '/servers/1234/action', {'resize': {'flavorRef': 1}})

    def test_resize_confirm(self):
        self.run_command('resize-confirm sample-server')
        self.assert_called('POST', '/servers/1234/action', {'confirmResize': None})

    def test_resize_revert(self):
        self.run_command('resize-revert sample-server')
        self.assert_called('POST', '/servers/1234/action', {'revertResize': None})

    @mock.patch('getpass.getpass', mock.Mock(return_value='p'))
    def test_root_password(self):
        self.run_command('root-password sample-server')
        self.assert_called('POST', '/servers/1234/action', {'changePassword': {'adminPass': 'p'}})

    def test_show(self):
        self.run_command('show 1234')
        # XXX need a way to test multiple calls
        # assert_called('GET', '/servers/1234')
        self.assert_called('GET', '/images/2')

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/servers/1234')
        self.run_command('delete sample-server')
        self.assert_called('DELETE', '/servers/1234')

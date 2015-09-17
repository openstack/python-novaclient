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

import distutils.version as dist_version
import re
import sys

import fixtures
from keystoneclient import fixture
import mock
import prettytable
import requests_mock
import six
from testtools import matchers

from novaclient import api_versions
import novaclient.client
from novaclient import exceptions
import novaclient.shell
from novaclient.tests.unit import fake_actions_module
from novaclient.tests.unit import utils

FAKE_ENV = {'OS_USERNAME': 'username',
            'OS_PASSWORD': 'password',
            'OS_TENANT_NAME': 'tenant_name',
            'OS_AUTH_URL': 'http://no.where/v2.0',
            'OS_COMPUTE_API_VERSION': '2'}

FAKE_ENV2 = {'OS_USER_ID': 'user_id',
             'OS_PASSWORD': 'password',
             'OS_TENANT_ID': 'tenant_id',
             'OS_AUTH_URL': 'http://no.where/v2.0',
             'OS_COMPUTE_API_VERSION': '2'}

FAKE_ENV3 = {'OS_USER_ID': 'user_id',
             'OS_PASSWORD': 'password',
             'OS_TENANT_ID': 'tenant_id',
             'OS_AUTH_URL': 'http://no.where/v2.0',
             'NOVA_ENDPOINT_TYPE': 'novaURL',
             'OS_ENDPOINT_TYPE': 'osURL',
             'OS_COMPUTE_API_VERSION': '2'}

FAKE_ENV4 = {'OS_USER_ID': 'user_id',
             'OS_PASSWORD': 'password',
             'OS_TENANT_ID': 'tenant_id',
             'OS_AUTH_URL': 'http://no.where/v2.0',
             'NOVA_ENDPOINT_TYPE': 'internal',
             'OS_ENDPOINT_TYPE': 'osURL',
             'OS_COMPUTE_API_VERSION': '2'}

FAKE_ENV5 = {'OS_USERNAME': 'username',
             'OS_PASSWORD': 'password',
             'OS_TENANT_NAME': 'tenant_name',
             'OS_AUTH_URL': 'http://no.where/v2.0',
             'OS_COMPUTE_API_VERSION': '2',
             'OS_AUTH_SYSTEM': 'rackspace'}


def _create_ver_list(versions):
    return {'versions': {'values': versions}}


class ParserTest(utils.TestCase):

    def setUp(self):
        super(ParserTest, self).setUp()
        self.parser = novaclient.shell.NovaClientArgumentParser()

    def test_ambiguous_option(self):
        self.parser.add_argument('--tic')
        self.parser.add_argument('--tac')

        try:
            self.parser.parse_args(['--t'])
        except SystemExit as err:
            self.assertEqual(2, err.code)
        else:
            self.fail('SystemExit not raised')

    def test_not_really_ambiguous_option(self):
        # current/deprecated forms of the same option
        self.parser.add_argument('--tic-tac', action="store_true")
        self.parser.add_argument('--tic_tac', action="store_true")
        args = self.parser.parse_args(['--tic'])
        self.assertTrue(args.tic_tac)


class ShellTest(utils.TestCase):

    _msg_no_tenant_project = ("You must provide a project name or project"
                              " id via --os-project-name, --os-project-id,"
                              " env[OS_PROJECT_ID] or env[OS_PROJECT_NAME]."
                              " You may use os-project and os-tenant"
                              " interchangeably.")

    def make_env(self, exclude=None, fake_env=FAKE_ENV):
        env = dict((k, v) for k, v in fake_env.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def setUp(self):
        super(ShellTest, self).setUp()
        self.useFixture(fixtures.MonkeyPatch(
                        'novaclient.client.Client',
                        mock.MagicMock()))
        self.nc_util = mock.patch(
            'novaclient.openstack.common.cliutils.isunauthenticated').start()
        self.nc_util.return_value = False
        self.mock_server_version_range = mock.patch(
            'novaclient.api_versions._get_server_version_range').start()
        self.mock_server_version_range.return_value = (
            novaclient.API_MIN_VERSION,
            novaclient.API_MIN_VERSION)
        self.orig_max_ver = novaclient.API_MAX_VERSION
        self.orig_min_ver = novaclient.API_MIN_VERSION
        self.addCleanup(self._clear_fake_version)
        self.addCleanup(mock.patch.stopall)

    def _clear_fake_version(self):
        novaclient.API_MAX_VERSION = self.orig_max_ver
        novaclient.API_MIN_VERSION = self.orig_min_ver

    def shell(self, argstr, exitcodes=(0,)):
        orig = sys.stdout
        orig_stderr = sys.stderr
        try:
            sys.stdout = six.StringIO()
            sys.stderr = six.StringIO()
            _shell = novaclient.shell.OpenStackComputeShell()
            _shell.main(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertIn(exc_value.code, exitcodes)
        finally:
            stdout = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig
            stderr = sys.stderr.getvalue()
            sys.stderr.close()
            sys.stderr = orig_stderr
        return (stdout, stderr)

    def register_keystone_discovery_fixture(self, mreq):
        v2_url = "http://no.where/v2.0"
        v2_version = fixture.V2Discovery(v2_url)
        mreq.register_uri(
            'GET', v2_url, json=_create_ver_list([v2_version]),
            status_code=200)

    def test_help_unknown_command(self):
        self.assertRaises(exceptions.CommandError, self.shell, 'help foofoo')

    def test_invalid_timeout(self):
        for f in [0, -1, -10]:
            cmd_text = '--timeout %s' % (f)
            stdout, stderr = self.shell(cmd_text, exitcodes=[0, 2])
            required = [
                'argument --timeout: %s must be greater than 0' % (f),
            ]
            for r in required:
                self.assertIn(r, stderr)

    def _test_help(self, command, required=None):
        if required is None:
            required = [
                '.*?^usage: ',
                '.*?^\s+set-password\s+Change the admin password',
                '.*?^See "nova help COMMAND" for help on a specific command',
            ]
        stdout, stderr = self.shell(command)
        for r in required:
            self.assertThat((stdout + stderr),
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_help(self):
        self._test_help('help')

    def test_help_option(self):
        self._test_help('--help')
        self._test_help('-h')

    def test_help_no_options(self):
        self._test_help('')

    def test_help_on_subcommand(self):
        required = [
            '.*?^usage: nova set-password',
            '.*?^Change the admin password',
            '.*?^Positional arguments:',
        ]
        self._test_help('help set-password', required=required)

    def test_bash_completion(self):
        stdout, stderr = self.shell('bash-completion')
        # just check we have some output
        required = [
            '.*--matching',
            '.*--wrap',
            '.*help',
            '.*secgroup-delete-rule',
            '.*--priority']
        for r in required:
            self.assertThat((stdout + stderr),
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_no_username(self):
        required = ('You must provide a username or user id'
                    ' via --os-username, --os-user-id,'
                    ' env[OS_USERNAME] or env[OS_USER_ID]')
        self.make_env(exclude='OS_USERNAME')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    def test_no_user_id(self):
        required = ('You must provide a username or user id'
                    ' via --os-username, --os-user-id,'
                    ' env[OS_USERNAME] or env[OS_USER_ID]')
        self.make_env(exclude='OS_USER_ID', fake_env=FAKE_ENV2)
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    def test_no_tenant_name(self):
        required = self._msg_no_tenant_project
        self.make_env(exclude='OS_TENANT_NAME')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    def test_no_tenant_id(self):
        required = self._msg_no_tenant_project
        self.make_env(exclude='OS_TENANT_ID', fake_env=FAKE_ENV2)
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    def test_no_auth_url(self):
        required = ('You must provide an auth url'
                    ' via either --os-auth-url or env[OS_AUTH_URL] or'
                    ' specify an auth_system which defines a default url'
                    ' with --os-auth-system or env[OS_AUTH_SYSTEM]',)
        self.make_env(exclude='OS_AUTH_URL')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args)
        else:
            self.fail('CommandError not raised')

    @mock.patch('novaclient.client.Client')
    @requests_mock.Mocker()
    def test_nova_endpoint_type(self, mock_client, m_requests):
        self.make_env(fake_env=FAKE_ENV3)
        self.register_keystone_discovery_fixture(m_requests)
        self.shell('list')
        client_kwargs = mock_client.call_args_list[0][1]
        self.assertEqual(client_kwargs['endpoint_type'], 'novaURL')

    @mock.patch('novaclient.client.Client')
    @requests_mock.Mocker()
    def test_endpoint_type_like_other_clients(self, mock_client, m_requests):
        self.make_env(fake_env=FAKE_ENV4)
        self.register_keystone_discovery_fixture(m_requests)
        self.shell('list')
        client_kwargs = mock_client.call_args_list[0][1]
        self.assertEqual(client_kwargs['endpoint_type'], 'internalURL')

    @mock.patch('novaclient.client.Client')
    @requests_mock.Mocker()
    def test_os_endpoint_type(self, mock_client, m_requests):
        self.make_env(exclude='NOVA_ENDPOINT_TYPE', fake_env=FAKE_ENV3)
        self.register_keystone_discovery_fixture(m_requests)
        self.shell('list')
        client_kwargs = mock_client.call_args_list[0][1]
        self.assertEqual(client_kwargs['endpoint_type'], 'osURL')

    @mock.patch('novaclient.client.Client')
    def test_default_endpoint_type(self, mock_client):
        self.make_env()
        self.shell('list')
        client_kwargs = mock_client.call_args_list[0][1]
        self.assertEqual(client_kwargs['endpoint_type'], 'publicURL')

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('getpass.getpass', return_value='password')
    @requests_mock.Mocker()
    def test_password(self, mock_getpass, mock_stdin, m_requests):
        mock_stdin.encoding = "utf-8"

        # default output of empty tables differs depending between prettytable
        # versions
        if (hasattr(prettytable, '__version__') and
                dist_version.StrictVersion(prettytable.__version__) <
                dist_version.StrictVersion('0.7.2')):
            ex = '\n'
        else:
            ex = '\n'.join([
                '+----+------+--------+------------+-------------+----------+',
                '| ID | Name | Status | Task State | Power State | Networks |',
                '+----+------+--------+------------+-------------+----------+',
                '+----+------+--------+------------+-------------+----------+',
                ''
            ])
        self.make_env(exclude='OS_PASSWORD')
        self.register_keystone_discovery_fixture(m_requests)
        stdout, stderr = self.shell('list')
        self.assertEqual((stdout + stderr), ex)

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('getpass.getpass', side_effect=EOFError)
    def test_no_password(self, mock_getpass, mock_stdin):
        required = ('Expecting a password provided'
                    ' via either --os-password, env[OS_PASSWORD],'
                    ' or prompted response',)
        self.make_env(exclude='OS_PASSWORD')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args)
        else:
            self.fail('CommandError not raised')

    def _test_service_type(self, version, service_type, mock_client):
        if version is None:
            cmd = 'list'
        else:
            cmd = ('--service_type %s --os-compute-api-version %s list' %
                   (service_type, version))
        self.make_env()
        self.shell(cmd)
        _, client_kwargs = mock_client.call_args_list[0]
        self.assertEqual(service_type, client_kwargs['service_type'])

    @mock.patch('novaclient.client.Client')
    def test_default_service_type(self, mock_client):
        self._test_service_type(None, 'compute', mock_client)

    @mock.patch('novaclient.client.Client')
    def test_v1_1_service_type(self, mock_client):
        self._test_service_type('1.1', 'compute', mock_client)

    @mock.patch('novaclient.client.Client')
    def test_v2_service_type(self, mock_client):
        self._test_service_type('2', 'compute', mock_client)

    @mock.patch('novaclient.client.Client')
    def test_v_unknown_service_type(self, mock_client):
        self.assertRaises(exceptions.UnsupportedVersion,
                          self._test_service_type,
                          'unknown', 'compute', mock_client)

    @mock.patch('sys.argv', ['nova'])
    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    def test_main_noargs(self):
        # Ensure that main works with no command-line arguments
        try:
            novaclient.shell.main()
        except SystemExit:
            self.fail('Unexpected SystemExit')

        # We expect the normal usage as a result
        self.assertIn('Command-line interface to the OpenStack Nova API',
                      sys.stdout.getvalue())

    @mock.patch.object(novaclient.shell.OpenStackComputeShell, 'main')
    def test_main_keyboard_interrupt(self, mock_compute_shell):
        # Ensure that exit code is 130 for KeyboardInterrupt
        mock_compute_shell.side_effect = KeyboardInterrupt()
        try:
            novaclient.shell.main()
        except SystemExit as ex:
            self.assertEqual(ex.code, 130)

    @mock.patch.object(novaclient.shell.OpenStackComputeShell, 'times')
    @requests_mock.Mocker()
    def test_timing(self, m_times, m_requests):
        m_times.append.side_effect = RuntimeError('Boom!')
        self.make_env()
        self.register_keystone_discovery_fixture(m_requests)
        self.shell('list')
        exc = self.assertRaises(RuntimeError, self.shell, '--timings list')
        self.assertEqual('Boom!', str(exc))

    @mock.patch('novaclient.shell.SecretsHelper.tenant_id',
                return_value=True)
    @mock.patch('novaclient.shell.SecretsHelper.auth_token',
                return_value=True)
    @mock.patch('novaclient.shell.SecretsHelper.management_url',
                return_value=True)
    @mock.patch('novaclient.client.Client')
    @requests_mock.Mocker()
    def test_keyring_saver_helper(self, mock_client,
                                  sh_management_url_function,
                                  sh_auth_token_function,
                                  sh_tenant_id_function,
                                  m_requests):
        self.make_env(fake_env=FAKE_ENV)
        self.register_keystone_discovery_fixture(m_requests)
        self.shell('list')
        mock_client_instance = mock_client.return_value
        keyring_saver = mock_client_instance.client.keyring_saver
        self.assertIsInstance(keyring_saver, novaclient.shell.SecretsHelper)

    @mock.patch('novaclient.client.Client')
    def test_microversion_with_latest(self, mock_client):
        self.make_env()
        novaclient.API_MAX_VERSION = api_versions.APIVersion('2.3')
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion("2.1"), api_versions.APIVersion("2.3"))
        self.shell('--os-compute-api-version 2.latest list')
        client_args = mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.3"), client_args[0])

    @mock.patch('novaclient.client.Client')
    def test_microversion_with_specified_version(self, mock_client):
        self.make_env()
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion("2.10"), api_versions.APIVersion("2.100"))
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.90")
        self.shell('--os-compute-api-version 2.99 list')
        client_args = mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.99"), client_args[0])

    @mock.patch('novaclient.client.Client')
    def test_microversion_with_specified_version_out_of_range(self,
                                                              mock_client):
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.90")
        self.assertRaises(exceptions.CommandError,
                          self.shell, '--os-compute-api-version 2.199 list')

    @mock.patch('novaclient.client.Client')
    def test_microversion_with_v2_and_v2_1_server(self, mock_client):
        self.make_env()
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion('2.1'), api_versions.APIVersion('2.3'))
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")
        self.shell('--os-compute-api-version 2 list')
        client_args = mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.0"), client_args[0])

    @mock.patch('novaclient.client.Client')
    def test_microversion_with_v2_and_v2_server(self, mock_client):
        self.make_env()
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion(), api_versions.APIVersion())
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")
        self.shell('--os-compute-api-version 2 list')
        client_args = mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.0"), client_args[0])

    @mock.patch('novaclient.client.Client')
    def test_microversion_with_v2_without_server_compatible(self, mock_client):
        self.make_env()
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion('2.2'), api_versions.APIVersion('2.3'))
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")
        self.assertRaises(
            exceptions.UnsupportedVersion,
            self.shell, '--os-compute-api-version 2 list')

    def test_microversion_with_specific_version_without_microversions(self):
        self.make_env()
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion(), api_versions.APIVersion())
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")
        self.assertRaises(
            exceptions.UnsupportedVersion,
            self.shell,
            '--os-compute-api-version 2.3 list')

    @mock.patch('novaclient.client.Client')
    def test_custom_auth_plugin(self, mock_client):
        self.make_env(fake_env=FAKE_ENV5)
        self.shell('list')
        password = mock_client.call_args_list[0][0][2]
        client_kwargs = mock_client.call_args_list[0][1]
        self.assertEqual(password, 'password')
        self.assertIs(client_kwargs['session'], None)

    @mock.patch.object(novaclient.shell.OpenStackComputeShell, 'main')
    def test_main_error_handling(self, mock_compute_shell):
        class MyException(Exception):
            pass
        with mock.patch('sys.stderr', six.StringIO()):
            mock_compute_shell.side_effect = MyException('message')
            self.assertRaises(SystemExit, novaclient.shell.main)
            err = sys.stderr.getvalue()
        self.assertEqual(err, 'ERROR (MyException): message\n')


class TestLoadVersionedActions(utils.TestCase):

    def test_load_versioned_actions(self):
        parser = novaclient.shell.NovaClientArgumentParser()
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.15"), False)
        self.assertIn('fake-action', shell.subcommands.keys())
        self.assertEqual(
            1, shell.subcommands['fake-action'].get_default('func')())

        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.25"), False)
        self.assertIn('fake-action', shell.subcommands.keys())
        self.assertEqual(
            2, shell.subcommands['fake-action'].get_default('func')())

        self.assertIn('fake-action2', shell.subcommands.keys())
        self.assertEqual(
            3, shell.subcommands['fake-action2'].get_default('func')())

    def test_load_versioned_actions_not_in_version_range(self):
        parser = novaclient.shell.NovaClientArgumentParser()
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.10000"), False)
        self.assertNotIn('fake-action', shell.subcommands.keys())
        self.assertIn('fake-action2', shell.subcommands.keys())

    def test_load_versioned_actions_with_help(self):
        parser = novaclient.shell.NovaClientArgumentParser()
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.10000"), True)
        self.assertIn('fake-action', shell.subcommands.keys())
        expected_desc = ("(Supported by API versions '%(start)s' - "
                         "'%(end)s')") % {'start': '2.10', 'end': '2.30'}
        self.assertIn(expected_desc,
                      shell.subcommands['fake-action'].description)

    @mock.patch.object(novaclient.shell.NovaClientArgumentParser,
                       'add_argument')
    def test_load_versioned_actions_with_args(self, mock_add_arg):
        parser = novaclient.shell.NovaClientArgumentParser(add_help=False)
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.1"), False)
        self.assertIn('fake-action2', shell.subcommands.keys())
        mock_add_arg.assert_has_calls([
            mock.call('-h', '--help', action='help', help='==SUPPRESS=='),
            mock.call('--foo')])

    @mock.patch.object(novaclient.shell.NovaClientArgumentParser,
                       'add_argument')
    def test_load_versioned_actions_with_args2(self, mock_add_arg):
        parser = novaclient.shell.NovaClientArgumentParser(add_help=False)
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.4"), False)
        self.assertIn('fake-action2', shell.subcommands.keys())
        mock_add_arg.assert_has_calls([
            mock.call('-h', '--help', action='help', help='==SUPPRESS=='),
            mock.call('--bar')])

    @mock.patch.object(novaclient.shell.NovaClientArgumentParser,
                       'add_argument')
    def test_load_versioned_actions_with_args_not_in_version_range(
            self, mock_add_arg):
        parser = novaclient.shell.NovaClientArgumentParser(add_help=False)
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.10000"), False)
        self.assertIn('fake-action2', shell.subcommands.keys())
        mock_add_arg.assert_has_calls([
            mock.call('-h', '--help', action='help', help='==SUPPRESS==')])

    @mock.patch.object(novaclient.shell.NovaClientArgumentParser,
                       'add_argument')
    def test_load_versioned_actions_with_args_and_help(self, mock_add_arg):
        parser = novaclient.shell.NovaClientArgumentParser(add_help=False)
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.4"), True)
        mock_add_arg.assert_has_calls([
            mock.call('-h', '--help', action='help', help='==SUPPRESS=='),
            mock.call('-h', '--help', action='help', help='==SUPPRESS=='),
            mock.call('--foo',
                      help=" (Supported by API versions '2.1' - '2.2')"),
            mock.call('--bar',
                      help=" (Supported by API versions '2.3' - '2.4')")])


class ShellTestKeystoneV3(ShellTest):
    def make_env(self, exclude=None, fake_env=FAKE_ENV):
        if 'OS_AUTH_URL' in fake_env:
            fake_env.update({'OS_AUTH_URL': 'http://no.where/v3'})
        env = dict((k, v) for k, v in fake_env.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def register_keystone_discovery_fixture(self, mreq):
        v3_url = "http://no.where/v3"
        v3_version = fixture.V3Discovery(v3_url)
        mreq.register_uri(
            'GET', v3_url, json=_create_ver_list([v3_version]),
            status_code=200)

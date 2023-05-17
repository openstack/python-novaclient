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
import io
import re
import sys
from unittest import mock

import ddt
import fixtures
from keystoneauth1 import fixture
import requests_mock
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
            'OS_COMPUTE_API_VERSION': '2',
            'OS_PROJECT_DOMAIN_ID': 'default',
            'OS_PROJECT_DOMAIN_NAME': 'default',
            'OS_USER_DOMAIN_ID': 'default',
            'OS_USER_DOMAIN_NAME': 'default'}

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
             'OS_AUTH_URL': 'http://no.where/v2.0'}


def _create_ver_list(versions):
    return {'versions': {'values': versions}}


class DeprecatedActionTest(utils.TestCase):
    @mock.patch.object(argparse.Action, '__init__', return_value=None)
    def test_init_emptyhelp_nouse(self, mock_init):
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertIsNone(result.use)
        self.assertEqual(result.real_action_args,
                         ('option_strings', 'dest', 'Deprecated',
                          {'a': 1, 'b': 2, 'c': 3}))
        self.assertIsNone(result.real_action)
        mock_init.assert_called_once_with(
            'option_strings', 'dest', help='Deprecated', a=1, b=2, c=3)

    @mock.patch.object(novaclient.shell.argparse.Action, '__init__',
                       return_value=None)
    def test_init_emptyhelp_withuse(self, mock_init):
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', use='use this instead', a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertEqual(result.use, 'use this instead')
        self.assertEqual(result.real_action_args,
                         ('option_strings', 'dest',
                          'Deprecated; use this instead',
                          {'a': 1, 'b': 2, 'c': 3}))
        self.assertIsNone(result.real_action)
        mock_init.assert_called_once_with(
            'option_strings', 'dest', help='Deprecated; use this instead',
            a=1, b=2, c=3)

    @mock.patch.object(argparse.Action, '__init__', return_value=None)
    def test_init_withhelp_nouse(self, mock_init):
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', help='some help', a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertIsNone(result.use)
        self.assertEqual(result.real_action_args,
                         ('option_strings', 'dest',
                          'some help (Deprecated)',
                          {'a': 1, 'b': 2, 'c': 3}))
        self.assertIsNone(result.real_action)
        mock_init.assert_called_once_with(
            'option_strings', 'dest', help='some help (Deprecated)',
            a=1, b=2, c=3)

    @mock.patch.object(novaclient.shell.argparse.Action, '__init__',
                       return_value=None)
    def test_init_withhelp_withuse(self, mock_init):
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', help='some help',
            use='use this instead', a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertEqual(result.use, 'use this instead')
        self.assertEqual(result.real_action_args,
                         ('option_strings', 'dest',
                          'some help (Deprecated; use this instead)',
                          {'a': 1, 'b': 2, 'c': 3}))
        self.assertIsNone(result.real_action)
        mock_init.assert_called_once_with(
            'option_strings', 'dest',
            help='some help (Deprecated; use this instead)',
            a=1, b=2, c=3)

    @mock.patch.object(argparse.Action, '__init__', return_value=None)
    def test_init_suppresshelp_nouse(self, mock_init):
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', help=argparse.SUPPRESS, a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertIsNone(result.use)
        self.assertEqual(result.real_action_args,
                         ('option_strings', 'dest', argparse.SUPPRESS,
                          {'a': 1, 'b': 2, 'c': 3}))
        self.assertIsNone(result.real_action)
        mock_init.assert_called_once_with(
            'option_strings', 'dest', help=argparse.SUPPRESS, a=1, b=2, c=3)

    @mock.patch.object(novaclient.shell.argparse.Action, '__init__',
                       return_value=None)
    def test_init_suppresshelp_withuse(self, mock_init):
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', help=argparse.SUPPRESS,
            use='use this instead', a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertEqual(result.use, 'use this instead')
        self.assertEqual(result.real_action_args,
                         ('option_strings', 'dest', argparse.SUPPRESS,
                          {'a': 1, 'b': 2, 'c': 3}))
        self.assertIsNone(result.real_action)
        mock_init.assert_called_once_with(
            'option_strings', 'dest', help=argparse.SUPPRESS, a=1, b=2, c=3)

    @mock.patch.object(argparse.Action, '__init__', return_value=None)
    def test_init_action_nothing(self, mock_init):
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', real_action='nothing', a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertIsNone(result.use)
        self.assertIs(result.real_action_args, False)
        self.assertIsNone(result.real_action)
        mock_init.assert_called_once_with(
            'option_strings', 'dest', help='Deprecated', a=1, b=2, c=3)

    @mock.patch.object(argparse.Action, '__init__', return_value=None)
    def test_init_action_string(self, mock_init):
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', real_action='store', a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertIsNone(result.use)
        self.assertEqual(result.real_action_args,
                         ('option_strings', 'dest', 'Deprecated',
                          {'a': 1, 'b': 2, 'c': 3}))
        self.assertEqual(result.real_action, 'store')
        mock_init.assert_called_once_with(
            'option_strings', 'dest', help='Deprecated', a=1, b=2, c=3)

    @mock.patch.object(argparse.Action, '__init__', return_value=None)
    def test_init_action_other(self, mock_init):
        action = mock.Mock()
        result = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', real_action=action, a=1, b=2, c=3)

        self.assertEqual(result.emitted, set())
        self.assertIsNone(result.use)
        self.assertIs(result.real_action_args, False)
        self.assertEqual(result.real_action, action.return_value)
        mock_init.assert_called_once_with(
            'option_strings', 'dest', help='Deprecated', a=1, b=2, c=3)
        action.assert_called_once_with(
            'option_strings', 'dest', help='Deprecated', a=1, b=2, c=3)

    @mock.patch.object(sys, 'stderr', io.StringIO())
    def test_get_action_nolookup(self):
        action_class = mock.Mock()
        parser = mock.Mock(**{
            '_registry_get.return_value': action_class,
        })
        obj = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', real_action='nothing', const=1)
        obj.real_action = 'action'

        result = obj._get_action(parser)

        self.assertEqual(result, 'action')
        self.assertEqual(obj.real_action, 'action')
        self.assertFalse(parser._registry_get.called)
        self.assertFalse(action_class.called)
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch.object(sys, 'stderr', io.StringIO())
    def test_get_action_lookup_noresult(self):
        parser = mock.Mock(**{
            '_registry_get.return_value': None,
        })
        obj = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', real_action='store', const=1)

        result = obj._get_action(parser)

        self.assertIsNone(result)
        self.assertIsNone(obj.real_action)
        parser._registry_get.assert_called_once_with(
            'action', 'store')
        self.assertEqual(sys.stderr.getvalue(),
                         'WARNING: Programming error: Unknown real action '
                         '"store"\n')

    @mock.patch.object(sys, 'stderr', io.StringIO())
    def test_get_action_lookup_withresult(self):
        action_class = mock.Mock()
        parser = mock.Mock(**{
            '_registry_get.return_value': action_class,
        })
        obj = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', real_action='store', const=1)

        result = obj._get_action(parser)

        self.assertEqual(result, action_class.return_value)
        self.assertEqual(obj.real_action, action_class.return_value)
        parser._registry_get.assert_called_once_with(
            'action', 'store')
        action_class.assert_called_once_with(
            'option_strings', 'dest', help='Deprecated', const=1)
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch.object(sys, 'stderr', io.StringIO())
    @mock.patch.object(novaclient.shell.DeprecatedAction, '_get_action')
    def test_call_unemitted_nouse(self, mock_get_action):
        obj = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest')

        obj('parser', 'namespace', 'values', 'option_string')

        self.assertEqual(obj.emitted, set(['option_string']))
        mock_get_action.assert_called_once_with('parser')
        mock_get_action.return_value.assert_called_once_with(
            'parser', 'namespace', 'values', 'option_string')
        self.assertEqual(sys.stderr.getvalue(),
                         'WARNING: Option "option_string" is deprecated\n')

    @mock.patch.object(sys, 'stderr', io.StringIO())
    @mock.patch.object(novaclient.shell.DeprecatedAction, '_get_action')
    def test_call_unemitted_withuse(self, mock_get_action):
        obj = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', use='use this instead')

        obj('parser', 'namespace', 'values', 'option_string')

        self.assertEqual(obj.emitted, set(['option_string']))
        mock_get_action.assert_called_once_with('parser')
        mock_get_action.return_value.assert_called_once_with(
            'parser', 'namespace', 'values', 'option_string')
        self.assertEqual(sys.stderr.getvalue(),
                         'WARNING: Option "option_string" is deprecated; '
                         'use this instead\n')

    @mock.patch.object(sys, 'stderr', io.StringIO())
    @mock.patch.object(novaclient.shell.DeprecatedAction, '_get_action')
    def test_call_emitted_nouse(self, mock_get_action):
        obj = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest')
        obj.emitted.add('option_string')

        obj('parser', 'namespace', 'values', 'option_string')

        self.assertEqual(obj.emitted, set(['option_string']))
        mock_get_action.assert_called_once_with('parser')
        mock_get_action.return_value.assert_called_once_with(
            'parser', 'namespace', 'values', 'option_string')
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch.object(sys, 'stderr', io.StringIO())
    @mock.patch.object(novaclient.shell.DeprecatedAction, '_get_action')
    def test_call_emitted_withuse(self, mock_get_action):
        obj = novaclient.shell.DeprecatedAction(
            'option_strings', 'dest', use='use this instead')
        obj.emitted.add('option_string')

        obj('parser', 'namespace', 'values', 'option_string')

        self.assertEqual(obj.emitted, set(['option_string']))
        mock_get_action.assert_called_once_with('parser')
        mock_get_action.return_value.assert_called_once_with(
            'parser', 'namespace', 'values', 'option_string')
        self.assertEqual(sys.stderr.getvalue(), '')


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


@ddt.ddt
class ShellTest(utils.TestCase):

    _msg_no_tenant_project = ("You must provide a project name or project"
                              " ID via --os-project-name, --os-project-id,"
                              " env[OS_PROJECT_ID] or env[OS_PROJECT_NAME]."
                              " You may use os-project and os-tenant"
                              " interchangeably.")

    def make_env(self, exclude=None, fake_env=FAKE_ENV):
        env = dict((k, v) for k, v in fake_env.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def setUp(self):
        super(ShellTest, self).setUp()
        self.mock_client = mock.MagicMock()
        self.mock_client.return_value.api_version = novaclient.API_MIN_VERSION
        self.useFixture(fixtures.MonkeyPatch('novaclient.client.Client',
                                             self.mock_client))
        self.nc_util = mock.patch('novaclient.utils.isunauthenticated').start()
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
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
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
                '.*?^\\s+set-password\\s+Change the admin password',
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

    def test_help_no_subcommand(self):
        self._test_help('--os-compute-api-version 2.87')

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
            '.*server-group-delete',
            '.*--image-with']
        for r in required:
            self.assertThat((stdout + stderr),
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_no_username(self):
        required = ('You must provide a user name/id (via --os-username, '
                    '--os-user-id, env[OS_USERNAME] or env[OS_USER_ID]) or '
                    'an auth token (via --os-token).')
        self.make_env(exclude='OS_USERNAME')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    def test_no_user_id(self):
        required = ('You must provide a user name/id (via --os-username, '
                    '--os-user-id, env[OS_USERNAME] or env[OS_USER_ID]) or '
                    'an auth token (via --os-token).')
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
                    ' via either --os-auth-url or env[OS_AUTH_URL].',)
        self.make_env(exclude='OS_AUTH_URL')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args)
        else:
            self.fail('CommandError not raised')

    @ddt.data(
        (None, 'project_domain_id', FAKE_ENV['OS_PROJECT_DOMAIN_ID']),
        ('OS_PROJECT_DOMAIN_ID', 'project_domain_id', ''),
        (None, 'project_domain_name', FAKE_ENV['OS_PROJECT_DOMAIN_NAME']),
        ('OS_PROJECT_DOMAIN_NAME', 'project_domain_name', ''),
        (None, 'user_domain_id', FAKE_ENV['OS_USER_DOMAIN_ID']),
        ('OS_USER_DOMAIN_ID', 'user_domain_id', ''),
        (None, 'user_domain_name', FAKE_ENV['OS_USER_DOMAIN_NAME']),
        ('OS_USER_DOMAIN_NAME', 'user_domain_name', '')
    )
    @ddt.unpack
    def test_basic_attributes(self, exclude, client_arg, env_var):
        self.make_env(exclude=exclude, fake_env=FAKE_ENV)
        self.shell('list')
        client_kwargs = self.mock_client.call_args_list[0][1]
        self.assertEqual(env_var, client_kwargs[client_arg])

    @requests_mock.Mocker()
    def test_nova_endpoint_type(self, m_requests):
        self.make_env(fake_env=FAKE_ENV3)
        self.register_keystone_discovery_fixture(m_requests)
        self.shell('list')
        client_kwargs = self.mock_client.call_args_list[0][1]
        self.assertEqual(client_kwargs['endpoint_type'], 'novaURL')

    @requests_mock.Mocker()
    def test_endpoint_type_like_other_clients(self, m_requests):
        self.make_env(fake_env=FAKE_ENV4)
        self.register_keystone_discovery_fixture(m_requests)
        self.shell('list')
        client_kwargs = self.mock_client.call_args_list[0][1]
        self.assertEqual(client_kwargs['endpoint_type'], 'internalURL')

    @requests_mock.Mocker()
    def test_os_endpoint_type(self, m_requests):
        self.make_env(exclude='NOVA_ENDPOINT_TYPE', fake_env=FAKE_ENV3)
        self.register_keystone_discovery_fixture(m_requests)
        self.shell('list')
        client_kwargs = self.mock_client.call_args_list[0][1]
        self.assertEqual(client_kwargs['endpoint_type'], 'osURL')

    def test_default_endpoint_type(self):
        self.make_env()
        self.shell('list')
        client_kwargs = self.mock_client.call_args_list[0][1]
        self.assertEqual(client_kwargs['endpoint_type'], 'publicURL')

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('getpass.getpass', return_value='password')
    @requests_mock.Mocker()
    def test_password(self, mock_getpass, mock_stdin, m_requests):
        mock_stdin.encoding = "utf-8"

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

    def _test_service_type(self, version, service_type, mock_client):
        if version is None:
            cmd = 'list'
        else:
            cmd = ('--service-type %s --os-compute-api-version %s list' %
                   (service_type, version))
        self.make_env()
        self.shell(cmd)
        _client_args, client_kwargs = mock_client.call_args_list[0]
        self.assertEqual(service_type, client_kwargs['service_type'])

    def test_default_service_type(self):
        self._test_service_type(None, 'compute', self.mock_client)

    def test_v2_service_type(self):
        self._test_service_type('2', 'compute', self.mock_client)

    def test_v_unknown_service_type(self):
        self.assertRaises(exceptions.UnsupportedVersion,
                          self._test_service_type,
                          'unknown', 'compute', self.mock_client)

    @mock.patch('sys.stdout', io.StringIO())
    @mock.patch('sys.stderr', io.StringIO())
    def test_main_noargs(self):
        # Ensure that main works with no command-line arguments
        try:
            novaclient.shell.main([])
        except SystemExit:
            self.fail('Unexpected SystemExit')

        # We expect the normal usage as a result
        self.assertIn(
            'Command-line interface to the OpenStack Nova API',
            sys.stdout.getvalue(),
        )
        # We also expect to see the deprecation warning
        self.assertIn(
            'nova CLI is deprecated and will be removed in a future release',
            sys.stderr.getvalue(),
        )

    @mock.patch.object(novaclient.shell.OpenStackComputeShell, 'main')
    def test_main_keyboard_interrupt(self, mock_compute_shell):
        # Ensure that exit code is 130 for KeyboardInterrupt
        mock_compute_shell.side_effect = KeyboardInterrupt()
        try:
            novaclient.shell.main([])
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

    @requests_mock.Mocker()
    def test_osprofiler(self, m_requests):
        self.make_env()

        def client(*args, **kwargs):
            self.assertEqual('swordfish', kwargs['profile'])
        with mock.patch('novaclient.client.Client', client):
            # we are only interested in the fact Client is initialized properly
            self.shell('list --profile swordfish', (0, 2))

    @requests_mock.Mocker()
    def test_osprofiler_not_installed(self, m_requests):
        self.make_env()

        # NOTE(rpodolyaka): osprofiler is in test-requirements, so we have to
        # simulate its absence here
        with mock.patch('novaclient.shell.osprofiler_profiler', None):
            _, stderr = self.shell('list --profile swordfish', (0, 2))
            self.assertIn('unrecognized arguments: --profile swordfish',
                          stderr)

    def test_microversion_with_default_behaviour(self):
        self.make_env(fake_env=FAKE_ENV5)
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion("2.1"), api_versions.APIVersion("2.3"))
        self.shell('list')
        client_args = self.mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.3"), client_args[0])

    def test_microversion_with_default_behaviour_with_legacy_server(self):
        self.make_env(fake_env=FAKE_ENV5)
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion(), api_versions.APIVersion())
        self.shell('list')
        client_args = self.mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.0"), client_args[0])

    def test_microversion_with_latest(self):
        self.make_env()
        novaclient.API_MAX_VERSION = api_versions.APIVersion('2.3')
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion("2.1"), api_versions.APIVersion("2.3"))
        self.shell('--os-compute-api-version 2.latest list')
        client_args = self.mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.3"), client_args[0])

    def test_microversion_with_specified_version(self):
        self.make_env()
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion("2.10"), api_versions.APIVersion("2.100"))
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.90")
        self.shell('--os-compute-api-version 2.99 list')
        client_args = self.mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.99"), client_args[0])

    def test_microversion_with_specified_version_out_of_range(self):
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.90")
        self.assertRaises(exceptions.CommandError,
                          self.shell, '--os-compute-api-version 2.199 list')

    def test_microversion_with_v2_and_v2_1_server(self):
        self.make_env()
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion('2.1'), api_versions.APIVersion('2.3'))
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")
        self.shell('--os-compute-api-version 2 list')
        client_args = self.mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.0"), client_args[0])

    def test_microversion_with_v2_and_v2_server(self):
        self.make_env()
        self.mock_server_version_range.return_value = (
            api_versions.APIVersion(), api_versions.APIVersion())
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.100")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")
        self.shell('--os-compute-api-version 2 list')
        client_args = self.mock_client.call_args_list[1][0]
        self.assertEqual(api_versions.APIVersion("2.0"), client_args[0])

    def test_microversion_with_v2_without_server_compatible(self):
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

    @mock.patch.object(novaclient.shell.OpenStackComputeShell, 'main')
    def test_main_error_handling(self, mock_compute_shell):
        class MyException(Exception):
            pass
        with mock.patch('sys.stderr', io.StringIO()):
            mock_compute_shell.side_effect = MyException('message')
            self.assertRaises(SystemExit, novaclient.shell.main, [])
            err = sys.stderr.getvalue()
        # We expect to see the error propagated
        self.assertIn('ERROR (MyException): message\n', err)
        # We also expect to see the deprecation warning
        self.assertIn(
            'nova CLI is deprecated and will be removed in a future release',
            err,
        )


class TestLoadVersionedActions(utils.TestCase):

    def test_load_versioned_actions(self):
        # first load with API version 2.15, ensuring we use the 2.15 version of
        # the underlying function (which returns 1)
        parser = novaclient.shell.NovaClientArgumentParser()
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.15"), False)
        self.assertIn('fake-action', shell.subcommands.keys())
        self.assertEqual(
            1, shell.subcommands['fake-action'].get_default('func')())

        # now load with API version 2.25, ensuring we now use the
        # correspponding version of the underlying function (which now returns
        # 2)
        parser = novaclient.shell.NovaClientArgumentParser()
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.25"), False)
        self.assertIn('fake-action', shell.subcommands.keys())
        self.assertEqual(
            2, shell.subcommands['fake-action'].get_default('func')())

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
                            api_versions.APIVersion("2.15"), True)
        self.assertIn('fake-action', shell.subcommands.keys())
        expected_desc = (" (Supported by API versions '%(start)s' - "
                         "'%(end)s')") % {'start': '2.10', 'end': '2.30'}
        self.assertEqual(expected_desc,
                         shell.subcommands['fake-action'].description)

    def test_load_versioned_actions_with_help_on_latest(self):
        parser = novaclient.shell.NovaClientArgumentParser()
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.latest"), True)
        self.assertIn('another-fake-action', shell.subcommands.keys())
        expected_desc = (" (Supported by API versions '%(start)s' - "
                         "'%(end)s')%(hint)s") % {
            'start': '2.0', 'end': '2.latest',
            'hint': novaclient.shell.HINT_HELP_MSG}
        self.assertEqual(expected_desc,
                         shell.subcommands['another-fake-action'].description)

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
            mock.call('--bar',
                      help=" (Supported by API versions '2.3' - '2.4')")])

    @mock.patch.object(novaclient.shell.NovaClientArgumentParser,
                       'add_argument')
    def test_load_actions_with_versioned_args(self, mock_add_arg):
        parser = novaclient.shell.NovaClientArgumentParser(add_help=False)
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.20"), False)
        self.assertIn(mock.call('--foo', help="first foo"),
                      mock_add_arg.call_args_list)
        self.assertNotIn(mock.call('--foo', help="second foo"),
                         mock_add_arg.call_args_list)

        mock_add_arg.reset_mock()

        parser = novaclient.shell.NovaClientArgumentParser(add_help=False)
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        shell = novaclient.shell.OpenStackComputeShell()
        shell.subcommands = {}
        shell._find_actions(subparsers, fake_actions_module,
                            api_versions.APIVersion("2.21"), False)
        self.assertNotIn(mock.call('--foo', help="first foo"),
                         mock_add_arg.call_args_list)
        self.assertIn(mock.call('--foo', help="second foo"),
                      mock_add_arg.call_args_list)


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

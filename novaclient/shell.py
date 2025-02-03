# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack Foundation
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

"""
Command-line interface to the OpenStack Nova API.
"""

import argparse
import logging
import os
import sys

from keystoneauth1 import loading
from oslo_utils import encodeutils
from oslo_utils import importutils
from oslo_utils import strutils

import novaclient
from novaclient import api_versions
from novaclient import client
from novaclient import exceptions as exc
import novaclient.extension
from novaclient.i18n import _
from novaclient import utils

osprofiler_profiler = importutils.try_import("osprofiler.profiler")

DEFAULT_MAJOR_OS_COMPUTE_API_VERSION = "2.0"
# The default behaviour of nova client CLI is that CLI negotiates with server
# to find out the most recent version between client and server, and
# '2.latest' means to that. This value never be changed until we decided to
# change the default behaviour of nova client CLI.
DEFAULT_OS_COMPUTE_API_VERSION = '2.latest'
DEFAULT_NOVA_ENDPOINT_TYPE = 'publicURL'
DEFAULT_NOVA_SERVICE_TYPE = "compute"

HINT_HELP_MSG = (" [hint: use '--os-compute-api-version' flag to show help "
                 "message for proper version]")

logger = logging.getLogger(__name__)


class DeprecatedAction(argparse.Action):
    """An argparse action for deprecated options.

    This class is an ``argparse.Action`` subclass that allows command
    line options to be explicitly deprecated.  It modifies the help
    text for the option to indicate that it's deprecated (unless help
    has been suppressed using ``argparse.SUPPRESS``), and provides a
    means to specify an alternate option to use using the ``use``
    keyword argument to ``argparse.ArgumentParser.add_argument()``.
    The original action may be specified with the ``real_action``
    keyword argument, which has the same interpretation as the
    ``action`` argument to ``argparse.ArgumentParser.add_argument()``,
    with the addition of the special "nothing" action which completely
    ignores the option (other than emitting the deprecation warning).
    Note that the deprecation warning is only emitted once per
    specific option string.

    Note: If the ``real_action`` keyword argument specifies an unknown
    action, no warning will be emitted unless the action is used, due
    to limitations with the method used to resolve the action names.
    """

    def __init__(self, option_strings, dest, help=None,
                 real_action=None, use=None, **kwargs):
        """Initialize a ``DeprecatedAction`` instance.

        :param option_strings: The recognized option strings.
        :param dest: The attribute that will be set.
        :param help: Help text.  This will be updated to indicate the
                     deprecation, and if ``use`` is provided, that
                     text will be included as well.
        :param real_action: The actual action to invoke.  This is
                            interpreted the same way as the ``action``
                            parameter.
        :param use: Text explaining which option to use instead.
        """

        # Update the help text
        if not help:
            if use:
                help = _('Deprecated; %(use)s') % {'use': use}
            else:
                help = _('Deprecated')
        elif help != argparse.SUPPRESS:
            if use:
                help = _('%(help)s (Deprecated; %(use)s)') % {
                    'help': help,
                    'use': use,
                }
            else:
                help = _('%(help)s (Deprecated)') % {'help': help}

        # Initialize ourself appropriately
        super(DeprecatedAction, self).__init__(
            option_strings, dest, help=help, **kwargs)

        # 'emitted' tracks which warnings we've emitted
        self.emitted = set()
        self.use = use

        # Select the appropriate action
        if real_action == 'nothing':
            # NOTE(Vek): "nothing" is distinct from a real_action=None
            # argument.  When real_action=None, the argparse default
            # action of "store" is used; when real_action='nothing',
            # however, we explicitly inhibit doing anything with the
            # option
            self.real_action_args = False
            self.real_action = None
        elif real_action is None or isinstance(real_action, str):
            # Specified by string (or None); we have to have a parser
            # to look up the actual action, so defer to later
            self.real_action_args = (option_strings, dest, help, kwargs)
            self.real_action = real_action
        else:
            self.real_action_args = False
            self.real_action = real_action(
                option_strings, dest, help=help, **kwargs)

    def _get_action(self, parser):
        """Retrieve the action callable.

        This internal method is used to retrieve the callable
        implementing the action.  If ``real_action`` was specified as
        ``None`` or one of the standard string names, an internal
        method of the ``argparse.ArgumentParser`` instance is used to
        resolve it into an actual action class, which is then
        instantiated.  This is cached, in case the action is called
        multiple times.

        :param parser: The ``argparse.ArgumentParser`` instance.

        :returns: The action callable.
        """

        # If a lookup is needed, look up the action in the parser
        if self.real_action_args is not False:
            option_strings, dest, help, kwargs = self.real_action_args
            action_class = parser._registry_get('action', self.real_action)

            # Did we find the action class?
            if action_class is None:
                print(_('WARNING: Programming error: Unknown real action '
                        '"%s"') % self.real_action, file=sys.stderr)
                self.real_action = None
            else:
                # OK, instantiate the action class
                self.real_action = action_class(
                    option_strings, dest, help=help, **kwargs)

            # It's been resolved, no further need to look it up
            self.real_action_args = False

        return self.real_action

    def __call__(self, parser, namespace, values, option_string):
        """Implement the action.

        Emits the deprecation warning message (only once for any given
        option string), then calls the real action (if any).

        :param parser: The ``argparse.ArgumentParser`` instance.
        :param namespace: The ``argparse.Namespace`` object which
                          should have an attribute set.
        :param values: Any arguments provided to the option.
        :param option_string: The option string that was used.
        """

        action = self._get_action(parser)

        # Only emit the deprecation warning once per option
        if option_string not in self.emitted:
            if self.use:
                print(_('WARNING: Option "%(option)s" is deprecated; '
                        '%(use)s') % {
                    'option': option_string,
                    'use': self.use,
                }, file=sys.stderr)
            else:
                print(_('WARNING: Option "%(option)s" is deprecated') %
                      {'option': option_string}, file=sys.stderr)
            self.emitted.add(option_string)

        if action:
            action(parser, namespace, values, option_string)


class NovaClientArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(NovaClientArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.
        """
        self.print_usage(sys.stderr)
        # FIXME(lzyeval): if changes occur in argparse.ArgParser._check_value
        choose_from = ' (choose from'
        progparts = self.prog.partition(' ')
        self.exit(2, _("error: %(errmsg)s\nTry '%(mainp)s help %(subp)s'"
                       " for more information.\n") %
                  {'errmsg': message.split(choose_from)[0],
                   'mainp': progparts[0],
                   'subp': progparts[2]})

    def _get_option_tuples(self, option_string):
        """returns (action, option, value) candidates for an option prefix

        Returns [first candidate] if all candidates refers to current and
        deprecated forms of the same options: "nova boot ... --key KEY"
        parsing succeed because --key could only match --key-name,
        --key_name which are current/deprecated forms of the same option.
        """
        option_tuples = (super(NovaClientArgumentParser, self)
                         ._get_option_tuples(option_string))
        if len(option_tuples) > 1:
            # In Python < 3.12, this is a 3-part tuple:
            #   action, option_string, explicit_arg
            # In Python >= 3.12, this is a 4 part tuple:
            #   action, option_string, sep, explicit_arg
            normalizeds = [opt[1].replace('_', '-') for opt in option_tuples]
            if len(set(normalizeds)) == 1:
                return option_tuples[:1]
        return option_tuples


class OpenStackComputeShell(object):
    times = []

    def __init__(self):
        self.client_logger = None

    def _append_global_identity_args(self, parser, argv):
        # Register the CLI arguments that have moved to the session object.
        loading.register_session_argparse_arguments(parser)
        # Peek into argv to see if os-token was given,
        # in which case, the token auth plugin is what the user wants
        # else, we'll default to password
        default_auth_plugin = 'password'
        if "--os-token" in argv:
            default_auth_plugin = 'token'
        loading.register_auth_argparse_arguments(
            parser, argv, default=default_auth_plugin)

        parser.set_defaults(insecure=strutils.bool_from_string(
            utils.env('NOVACLIENT_INSECURE', default=False)))
        parser.set_defaults(os_auth_url=utils.env('OS_AUTH_URL', 'NOVA_URL'))

        parser.set_defaults(os_username=utils.env('OS_USERNAME',
                                                  'NOVA_USERNAME'))
        parser.set_defaults(os_password=utils.env('OS_PASSWORD',
                                                  'NOVA_PASSWORD'))
        parser.set_defaults(os_project_name=utils.env(
            'OS_PROJECT_NAME', 'OS_TENANT_NAME', 'NOVA_PROJECT_ID'))
        parser.set_defaults(os_project_id=utils.env(
            'OS_PROJECT_ID', 'OS_TENANT_ID'))
        parser.set_defaults(
            os_project_domain_id=utils.env('OS_PROJECT_DOMAIN_ID'))
        parser.set_defaults(
            os_project_domain_name=utils.env('OS_PROJECT_DOMAIN_NAME'))
        parser.set_defaults(
            os_user_domain_id=utils.env('OS_USER_DOMAIN_ID'))
        parser.set_defaults(
            os_user_domain_name=utils.env('OS_USER_DOMAIN_NAME'))

    def get_base_parser(self, argv):
        parser = NovaClientArgumentParser(
            prog='nova',
            description=__doc__.strip(),
            epilog='See "nova help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument(
            '-h', '--help',
            action='store_true',
            help=argparse.SUPPRESS,
        )

        parser.add_argument('--version',
                            action='version',
                            version=novaclient.__version__)

        parser.add_argument(
            '--debug',
            default=False,
            action='store_true',
            help=_("Print debugging output."))

        parser.add_argument(
            '--os-cache',
            default=strutils.bool_from_string(
                utils.env('OS_CACHE', default=False), True),
            action='store_true',
            help=_("Use the auth token cache. Defaults to False if "
                   "env[OS_CACHE] is not set."))

        parser.add_argument(
            '--timings',
            default=False,
            action='store_true',
            help=_("Print call timing info."))

        parser.add_argument(
            '--os-region-name',
            metavar='<region-name>',
            default=utils.env('OS_REGION_NAME', 'NOVA_REGION_NAME'),
            help=_('Defaults to env[OS_REGION_NAME].'))

        parser.add_argument(
            '--service-type',
            metavar='<service-type>',
            help=_('Defaults to compute for most actions.'))

        parser.add_argument(
            '--service-name',
            metavar='<service-name>',
            default=utils.env('NOVA_SERVICE_NAME'),
            help=_('Defaults to env[NOVA_SERVICE_NAME].'))

        parser.add_argument(
            '--os-endpoint-type',
            metavar='<endpoint-type>',
            dest='endpoint_type',
            default=utils.env(
                'NOVA_ENDPOINT_TYPE', default=utils.env(
                    'OS_ENDPOINT_TYPE',
                    default=DEFAULT_NOVA_ENDPOINT_TYPE)),
            help=_('Defaults to env[NOVA_ENDPOINT_TYPE], '
                   'env[OS_ENDPOINT_TYPE] or ') +
                 DEFAULT_NOVA_ENDPOINT_TYPE + '.')

        parser.add_argument(
            '--os-compute-api-version',
            metavar='<compute-api-ver>',
            default=utils.env('OS_COMPUTE_API_VERSION',
                              default=DEFAULT_OS_COMPUTE_API_VERSION),
            help=_('Accepts X, X.Y (where X is major and Y is minor part) or '
                   '"X.latest", defaults to env[OS_COMPUTE_API_VERSION].'))

        parser.add_argument(
            '--os-endpoint-override',
            metavar='<bypass-url>',
            dest='endpoint_override',
            default=utils.env('OS_ENDPOINT_OVERRIDE',
                              'NOVACLIENT_ENDPOINT_OVERRIDE',
                              'NOVACLIENT_BYPASS_URL'),
            help=_("Use this API endpoint instead of the Service Catalog. "
                   "Defaults to env[OS_ENDPOINT_OVERRIDE]."))

        parser.set_defaults(func=self.do_help)
        parser.set_defaults(command='')

        if osprofiler_profiler:
            parser.add_argument('--profile',
                                metavar='HMAC_KEY',
                                default=utils.env('OS_PROFILE'),
                                help='HMAC key to use for encrypting context '
                                'data for performance profiling of operation. '
                                'This key should be the value of the HMAC key '
                                'configured for the OSprofiler middleware in '
                                'nova; it is specified in the Nova '
                                'configuration file at "/etc/nova/nova.conf". '
                                'Without the key, profiling will not be '
                                'triggered even if OSprofiler is enabled on '
                                'the server side.')

        self._append_global_identity_args(parser, argv)

        return parser

    def get_subcommand_parser(self, version, do_help=False, argv=None):
        parser = self.get_base_parser(argv)

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        actions_module = importutils.import_module(
            "novaclient.v%s.shell" % version.ver_major)

        self._find_actions(subparsers, actions_module, version, do_help)
        self._find_actions(subparsers, self, version, do_help)

        for extension in self.extensions:
            self._find_actions(subparsers, extension.module, version, do_help)

        self._add_bash_completion_subparser(subparsers)

        return parser

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser(
            'bash_completion',
            add_help=False,
            formatter_class=OpenStackHelpFormatter
        )
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module, version, do_help):
        msg = _(" (Supported by API versions '%(start)s' - '%(end)s')")
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hyphen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            if hasattr(callback, "versioned"):
                additional_msg = ""
                subs = api_versions.get_substitutions(callback)
                if do_help:
                    additional_msg = msg % {
                        'start': subs[0].start_version.get_string(),
                        'end': subs[-1].end_version.get_string()}
                    if version.is_latest():
                        additional_msg += HINT_HELP_MSG
                subs = [versioned_method for versioned_method in subs
                        if version.matches(versioned_method.start_version,
                                           versioned_method.end_version)]
                if subs:
                    # use the "latest" substitution
                    callback = subs[-1].func
                else:
                    # there is no proper versioned method
                    continue
                desc = callback.__doc__ or desc
                desc += additional_msg

            action_help = desc.strip()
            arguments = getattr(callback, 'arguments', [])
            groups = {}

            subparser = subparsers.add_parser(
                command,
                help=action_help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter)
            subparser.add_argument(
                '-h', '--help',
                action='help',
                help=argparse.SUPPRESS,
            )
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                kwargs = kwargs.copy()

                start_version = kwargs.pop("start_version", None)
                end_version = kwargs.pop("end_version", None)
                group = kwargs.pop("group", None)

                if start_version:
                    start_version = api_versions.APIVersion(start_version)
                    if end_version:
                        end_version = api_versions.APIVersion(end_version)
                    else:
                        end_version = api_versions.APIVersion(
                            "%s.latest" % start_version.ver_major)
                    if do_help:
                        kwargs["help"] = kwargs.get("help", "") + (msg % {
                            "start": start_version.get_string(),
                            "end": end_version.get_string()})
                    if not version.matches(start_version, end_version):
                        continue

                if group:
                    if group not in groups:
                        groups[group] = (
                            subparser.add_mutually_exclusive_group()
                        )
                    kwargs['dest'] = kwargs.get('dest', group)
                    groups[group].add_argument(*args, **kwargs)
                else:
                    subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def setup_debugging(self, debug):
        if not debug:
            return

        streamformat = "%(levelname)s (%(module)s:%(lineno)d) %(message)s"
        # Set up the root logger to debug so that the submodules can
        # print debug messages
        logging.basicConfig(level=logging.DEBUG,
                            format=streamformat)
        logging.getLogger('iso8601').setLevel(logging.WARNING)

        self.client_logger = logging.getLogger(client.__name__)
        ch = logging.StreamHandler()
        self.client_logger.setLevel(logging.DEBUG)
        self.client_logger.addHandler(ch)

    def main(self, argv):
        # Parse args once to find version and debug settings
        parser = self.get_base_parser(argv)
        (args, args_list) = parser.parse_known_args(argv)

        self.setup_debugging(args.debug)
        self.extensions = []
        do_help = args.help or not args_list or args_list[0] == 'help'

        # bash-completion should not require authentication
        skip_auth = do_help or (
            'bash-completion' in argv)

        if not args.os_compute_api_version:
            api_version = api_versions.get_api_version(
                DEFAULT_MAJOR_OS_COMPUTE_API_VERSION)
        else:
            api_version = api_versions.get_api_version(
                args.os_compute_api_version)

        auth_token = getattr(args, "os_token", None)

        os_username = getattr(args, "os_username", None)
        os_user_id = getattr(args, "os_user_id", None)
        os_password = None  # Fetched and set later as needed
        os_project_name = getattr(
            args, 'os_project_name', getattr(args, 'os_tenant_name', None))
        os_project_id = getattr(
            args, 'os_project_id', getattr(args, 'os_tenant_id', None))
        os_auth_url = args.os_auth_url
        os_region_name = args.os_region_name

        if "v2.0" not in os_auth_url:
            # NOTE(andreykurilin): assume that keystone V3 is used and try to
            # be more user-friendly, i.e provide default values for domains
            if (not args.os_project_domain_id and
                    not args.os_project_domain_name):
                setattr(args, "os_project_domain_id", "default")

            # os_user_domain_id is redundant in case of Token auth type
            if not auth_token and (not args.os_user_domain_id and
                                   not args.os_user_domain_name):
                setattr(args, "os_user_domain_id", "default")

        os_project_domain_id = args.os_project_domain_id
        os_project_domain_name = args.os_project_domain_name
        os_user_domain_id = getattr(args, "os_user_domain_id", None)
        os_user_domain_name = getattr(args, "os_user_domain_name", None)

        endpoint_type = args.endpoint_type
        insecure = args.insecure
        service_type = args.service_type
        service_name = args.service_name
        endpoint_override = args.endpoint_override
        os_cache = args.os_cache
        cacert = args.os_cacert
        cert = args.os_cert
        timeout = args.timeout

        keystone_session = None
        keystone_auth = None

        if not endpoint_type:
            endpoint_type = DEFAULT_NOVA_ENDPOINT_TYPE

        # This allow users to use endpoint_type as (internal, public or admin)
        # just like other openstack clients (glance, cinder etc)
        if endpoint_type in ['internal', 'public', 'admin']:
            endpoint_type += 'URL'

        if not service_type:
            # Note(alex_xu): We need discover version first, so if there isn't
            # service type specified, we use default nova service type.
            service_type = DEFAULT_NOVA_SERVICE_TYPE

        # We should always auth unless we have a token and we're passing a
        # specific endpoint
        # Expired tokens are handled by client.py:_cs_request
        must_auth = not (auth_token and endpoint_override)

        # FIXME(usrleon): Here should be restrict for project id same as
        # for os_username or os_password but for compatibility it is not.
        if must_auth and not skip_auth:

            if not any([auth_token, os_username, os_user_id]):
                raise exc.CommandError(
                    _("You must provide a user name/id (via --os-username, "
                      "--os-user-id, env[OS_USERNAME] or env[OS_USER_ID]) or "
                      "an auth token (via --os-token)."))

            if not any([os_project_name, os_project_id]):
                raise exc.CommandError(_("You must provide a project name or"
                                         " project ID via --os-project-name,"
                                         " --os-project-id, env[OS_PROJECT_ID]"
                                         " or env[OS_PROJECT_NAME]. You may"
                                         " use os-project and os-tenant"
                                         " interchangeably."))

            if not os_auth_url:
                raise exc.CommandError(
                    _("You must provide an auth url "
                      "via either --os-auth-url or env[OS_AUTH_URL]."))

            # TODO(Shilpasd): need to provide support in python - novaclient
            # for required options for below default auth type plugins:
            # 1. v3oidcclientcredential
            # 2. v3oidcpassword
            # 3. v3oidcauthcode
            # 4. v3oidcaccesstoken
            # 5. v3oauth1
            # 6. v3fedkerb
            # 7. v3adfspassword
            # 8. v3samlpassword
            # 9. v3applicationcredential
            # TODO(Shilpasd): need to provide support in python - novaclient
            # for below extra keystoneauth auth type plugins:
            # We will need to add code to support discovering of versions
            # supported by the keystone service based on the auth_url similar
            # to the one supported by glanceclient.
            # 1. v3password
            # 2. v3token
            # 3. v3kerberos
            # 4. v3totp
            with utils.record_time(self.times, args.timings,
                                   'auth_url', args.os_auth_url):
                keystone_session = (
                    loading.load_session_from_argparse_arguments(args))
                keystone_auth = (
                    loading.load_auth_from_argparse_arguments(args))

        if (not skip_auth and
                not any([os_project_name, os_project_id])):
            raise exc.CommandError(_("You must provide a project name or"
                                     " project id via --os-project-name,"
                                     " --os-project-id, env[OS_PROJECT_ID]"
                                     " or env[OS_PROJECT_NAME]. You may"
                                     " use os-project and os-tenant"
                                     " interchangeably."))

        if not os_auth_url and not skip_auth:
            raise exc.CommandError(
                _("You must provide an auth url "
                  "via either --os-auth-url or env[OS_AUTH_URL]"))

        additional_kwargs = {}
        if osprofiler_profiler:
            additional_kwargs["profile"] = args.profile

        # This client is just used to discover api version. Version API needn't
        # microversion, so we just pass version 2 at here.
        self.cs = client.Client(
            api_versions.APIVersion("2.0"),
            os_username, os_password, project_id=os_project_id,
            project_name=os_project_name, user_id=os_user_id,
            auth_url=os_auth_url, insecure=insecure,
            region_name=os_region_name, endpoint_type=endpoint_type,
            extensions=self.extensions, service_type=service_type,
            service_name=service_name, auth_token=auth_token,
            timings=args.timings, endpoint_override=endpoint_override,
            os_cache=os_cache, http_log_debug=args.debug,
            cacert=cacert, cert=cert, timeout=timeout,
            session=keystone_session, auth=keystone_auth,
            logger=self.client_logger,
            project_domain_id=os_project_domain_id,
            project_domain_name=os_project_domain_name,
            user_domain_id=os_user_domain_id,
            user_domain_name=os_user_domain_name,
            **additional_kwargs)

        if not skip_auth:
            if not api_version.is_latest():
                if api_version > api_versions.APIVersion("2.0"):
                    if not api_version.matches(novaclient.API_MIN_VERSION,
                                               novaclient.API_MAX_VERSION):
                        raise exc.CommandError(
                            _("The specified version isn't supported by "
                              "client. The valid version range is '%(min)s' "
                              "to '%(max)s'") % {
                                "min": novaclient.API_MIN_VERSION.get_string(),
                                "max": novaclient.API_MAX_VERSION.get_string()}
                        )
            api_version = api_versions.discover_version(self.cs, api_version)

        # build available subcommands based on version
        self.extensions = client.discover_extensions(api_version)
        self._run_extension_hooks('__pre_parse_args__')

        subcommand_parser = self.get_subcommand_parser(
            api_version, do_help=do_help, argv=argv)
        self.parser = subcommand_parser

        if args.help or not argv:
            subcommand_parser.print_help()
            return 0

        args = subcommand_parser.parse_args(argv)
        self._run_extension_hooks('__post_parse_args__', args)

        # Short-circuit and deal with help right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        if not args.service_type:
            service_type = (utils.get_service_type(args.func) or
                            DEFAULT_NOVA_SERVICE_TYPE)

        if utils.isunauthenticated(args.func):
            # NOTE(alex_xu): We need authentication for discover microversion.
            # But the subcommands may needn't it. If the subcommand needn't,
            # we clear the session arguments.
            keystone_session = None
            keystone_auth = None

        # Recreate client object with discovered version.
        self.cs = client.Client(
            api_version,
            os_username, os_password, project_id=os_project_id,
            project_name=os_project_name, user_id=os_user_id,
            auth_url=os_auth_url, insecure=insecure,
            region_name=os_region_name, endpoint_type=endpoint_type,
            extensions=self.extensions, service_type=service_type,
            service_name=service_name, auth_token=auth_token,
            timings=args.timings, endpoint_override=endpoint_override,
            os_cache=os_cache, http_log_debug=args.debug,
            cacert=cacert, cert=cert, timeout=timeout,
            session=keystone_session, auth=keystone_auth,
            project_domain_id=os_project_domain_id,
            project_domain_name=os_project_domain_name,
            user_domain_id=os_user_domain_id,
            user_domain_name=os_user_domain_name)

        args.func(self.cs, args)

        if osprofiler_profiler and args.profile:
            trace_id = osprofiler_profiler.get().get_base_id()
            print("To display trace use the command:\n\n"
                  "  osprofiler trace show --html %s " % trace_id)

        if args.timings:
            self._dump_timings(self.times + self.cs.get_timings())

    def _dump_timings(self, timings):
        class Tyme(object):
            def __init__(self, url, seconds):
                self.url = url
                self.seconds = seconds
        results = [Tyme(url, end - start) for url, start, end in timings]
        total = 0.0
        for tyme in results:
            total += tyme.seconds
        results.append(Tyme("Total", total))
        utils.print_list(results, ["url", "seconds"], sortby_index=None)

    def _run_extension_hooks(self, hook_type, *args, **kwargs):
        """Run hooks for all registered extensions."""
        for extension in self.extensions:
            extension.run_hooks(hook_type, *args, **kwargs)

    def do_bash_completion(self, _args):
        """
        Prints all of the commands and options to stdout so that the
        nova.bash_completion script doesn't have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.add(option)

        commands.remove('bash-completion')
        commands.remove('bash_completion')
        print(' '.join(commands | options))

    @utils.arg(
        'command',
        metavar='<subcommand>',
        nargs='?',
        help=_('Display help for <subcommand>.'))
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if args.command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError(_("'%s' is not a valid subcommand") %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog, indent_increment=2, max_help_position=32,
                 width=None):
        super(OpenStackHelpFormatter, self).__init__(prog, indent_increment,
                                                     max_help_position, width)

    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main(argv=sys.argv[1:]):
    try:
        # Special dansmith envvar to hide the warning. Don't rely on this
        # because we will eventually remove all this stuff.
        if os.environ.get("NOVACLIENT_ISHOULDNTBEDOINGTHIS") != "1":
            print(
                _(
                    "nova CLI is deprecated and will be removed in a future "
                    "release"
                ),
                file=sys.stderr,
            )
        argv = [encodeutils.safe_decode(a) for a in argv]
        OpenStackComputeShell().main(argv)
    except Exception as exc:
        logger.debug(exc, exc_info=1)
        print("ERROR (%(type)s): %(msg)s" % {
              'type': exc.__class__.__name__,
              'msg': exc},
              file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print(_("... terminating nova client"), file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()

# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
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
import glob
import httplib2
import imp
import itertools
import os
import pkgutil
import sys

from novaclient import client
from novaclient import exceptions as exc
import novaclient.extension
from novaclient.keystone import shell as shell_keystone
from novaclient import utils
from novaclient.v1_1 import shell as shell_v1_1


def env(*vars):
    """
    returns the first environment variable set
    """
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return ''


class NovaClientArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(NovaClientArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.
        """
        self.print_usage(sys.stderr)
        #FIXME(lzyeval): if changes occur in argparse.ArgParser._check_value
        choose_from = ' (choose from'
        self.exit(2, "error: %s\nTry `%s help' for more information.\n" %
                     (message.split(choose_from)[0], self.prog))


class OpenStackComputeShell(object):

    def get_base_parser(self):
        parser = NovaClientArgumentParser(
            prog='nova',
            description=__doc__.strip(),
            epilog='See "nova help COMMAND" '\
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
            action='help',
            help=argparse.SUPPRESS,
        )

        parser.add_argument('--debug',
            default=False,
            action='store_true',
            help=argparse.SUPPRESS)

        parser.add_argument('--username',
            default=env('OS_USERNAME', 'NOVA_USERNAME'),
            help='Defaults to env[OS_USERNAME].')

        parser.add_argument('--apikey',
            default=env('NOVA_API_KEY'),
            help='Defaults to env[NOVA_API_KEY].')

        parser.add_argument('--password',
            default=env('OS_PASSWORD', 'NOVA_PASSWORD'),
            help='Defaults to env[OS_PASSWORD].')

        parser.add_argument('--projectid',
            default=env('OS_TENANT_NAME', 'NOVA_PROJECT_ID'),
            help='Defaults to env[OS_TENANT_NAME].')

        parser.add_argument('--url',
            default=env('OS_AUTH_URL', 'NOVA_URL'),
            help='Defaults to env[OS_AUTH_URL].')

        parser.add_argument('--region_name',
            default=env('NOVA_REGION_NAME'),
            help='Defaults to env[NOVA_REGION_NAME].')

        parser.add_argument('--endpoint_name',
            default=env('NOVA_ENDPOINT_NAME'),
            help='Defaults to env[NOVA_ENDPOINT_NAME] or "publicURL".')

        parser.add_argument('--version',
            default=env('NOVA_VERSION'),
            help='Accepts 1.1, defaults to env[NOVA_VERSION].')

        parser.add_argument('--insecure',
            default=False,
            action='store_true',
            help=argparse.SUPPRESS)

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_module = {
                '1.1': shell_v1_1,
                '2': shell_v1_1,
            }[version]
        except KeyError:
            actions_module = shell_v1_1

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, shell_keystone)
        self._find_actions(subparsers, self)

        for extension in self.extensions:
            self._find_actions(subparsers, extension.module)

        self._add_bash_completion_subparser(subparsers)

        return parser

    def _discover_extensions(self, version):
        extensions = []
        for name, module in itertools.chain(
                self._discover_via_python_path(version),
                self._discover_via_contrib_path(version)):

            extension = novaclient.extension.Extension(name, module)
            extensions.append(extension)

        return extensions

    def _discover_via_python_path(self, version):
        for (module_loader, name, ispkg) in pkgutil.iter_modules():
            if name.endswith('python_novaclient_ext'):
                if not hasattr(module_loader, 'load_module'):
                    # Python 2.6 compat: actually get an ImpImporter obj
                    module_loader = module_loader.find_module(name)

                module = module_loader.load_module(name)
                yield name, module

    def _discover_via_contrib_path(self, version):
        module_path = os.path.dirname(os.path.abspath(__file__))
        version_str = "v%s" % version.replace('.', '_')
        ext_path = os.path.join(module_path, version_str, 'contrib')
        ext_glob = os.path.join(ext_path, "*.py")

        for ext_path in glob.iglob(ext_glob):
            name = os.path.basename(ext_path)[:-3]

            if name == "__init__":
                continue

            module = imp.load_source(name, ext_path)
            yield name, module

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser('bash_completion',
            add_help=False,
            formatter_class=OpenStackHelpFormatter
        )
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(command,
                help=help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter
            )
            subparser.add_argument('-h', '--help',
                action='help',
                help=argparse.SUPPRESS,
            )
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def main(self, argv):
        # Parse args once to find version
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)

        # build available subcommands based on version
        self.extensions = self._discover_extensions(options.version)
        self._run_extension_hooks('__pre_parse_args__')

        subcommand_parser = self.get_subcommand_parser(options.version)
        self.parser = subcommand_parser

        args = subcommand_parser.parse_args(argv)
        self._run_extension_hooks('__post_parse_args__', args)

        # Deal with global arguments
        if args.debug:
            httplib2.debuglevel = 1

        # Short-circuit and deal with help right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        (user, apikey, password, projectid, url, region_name,
                endpoint_name, insecure) = (args.username, args.apikey,
                        args.password, args.projectid, args.url,
                        args.region_name, args.endpoint_name, args.insecure)

        if not endpoint_name:
            endpoint_name = 'publicURL'

        #FIXME(usrleon): Here should be restrict for project id same as
        # for username or password but for compatibility it is not.

        if not utils.isunauthenticated(args.func):
            if not user:
                raise exc.CommandError("You must provide a username, either "
                                       "via --username or via "
                                       "env[OS_USERNAME]")

            if not password:
                if not apikey:
                    raise exc.CommandError("You must provide a password, "
                            "either via --password or via env[OS_PASSWORD]")
                else:
                    password = apikey

            if not projectid:
                raise exc.CommandError("You must provide an projectid, either "
                                       "via --projectid or via "
                                       "env[OS_TENANT_NAME]")

            if not url:
                raise exc.CommandError("You must provide a auth url, either "
                                       "via --url or via "
                                       "env[OS_AUTH_URL]")

        if options.version and options.version != '1.0':
            if not projectid:
                raise exc.CommandError("You must provide an projectid, "
                                       "either via --projectid or via "
                                       "env[NOVA_PROJECT_ID]")

            if not url:
                raise exc.CommandError("You must provide a auth url,"
                                       " either via --url or via "
                                       "env[NOVA_URL]")

        self.cs = client.Client(options.version, user, password,
                                projectid, url, insecure,
                                region_name=region_name,
                                endpoint_name=endpoint_name,
                                extensions=self.extensions)

        try:
            if not utils.isunauthenticated(args.func):
                self.cs.authenticate()
        except exc.Unauthorized:
            raise exc.CommandError("Invalid OpenStack Nova credentials.")
        except exc.AuthorizationFailure:
            raise exc.CommandError("Unable to authorize user")

        args.func(self.cs, args)

    def _run_extension_hooks(self, hook_type, *args, **kwargs):
        """Run hooks for all registered extensions."""
        for extension in self.extensions:
            extension.run_hooks(hook_type, *args, **kwargs)

    def do_bash_completion(self, args):
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
        print ' '.join(commands | options)

    @utils.arg('command', metavar='<subcommand>', nargs='?',
                    help='Display help for <subcommand>')
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if args.command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        OpenStackComputeShell().main(sys.argv[1:])

    except Exception, e:
        if httplib2.debuglevel == 1:
            raise  # dump stack.
        else:
            print >> sys.stderr, e
        sys.exit(1)

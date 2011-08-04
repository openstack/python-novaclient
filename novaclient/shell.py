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
import httplib2
import os
import prettytable
import sys

from novaclient import exceptions
from novaclient import utils
from novaclient.v1_0 import shell as shell_v1_0
from novaclient.v1_1 import shell as shell_v1_1


def env(e):
    return os.environ.get(e, '')


class OpenStackComputeShell(object):

    def get_base_parser(self):
        parser = argparse.ArgumentParser(
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
            default=env('NOVA_USERNAME'),
            help='Defaults to env[NOVA_USERNAME].')

        parser.add_argument('--apikey',
            default=env('NOVA_API_KEY'),
            help='Defaults to env[NOVA_API_KEY].')

        parser.add_argument('--projectid',
            default=env('NOVA_PROJECT_ID'),
            help='Defaults to env[NOVA_PROJECT_ID].')

        parser.add_argument('--url',
            default=env('NOVA_URL'),
            help='Defaults to env[NOVA_URL].')

        parser.add_argument('--version',
            default=env('NOVA_VERSION'),
            help='Accepts 1.0 or 1.1, defaults to env[NOVA_VERSION].')

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_module = {
                '1.0': shell_v1_0,
                '1.1': shell_v1_1,
            }[version]
        except KeyError:
            actions_module = shell_v1_0

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, self)

        return parser

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
        subcommand_parser = self.get_subcommand_parser(options.version)
        self.parser = subcommand_parser

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Deal with global arguments
        if args.debug:
            httplib2.debuglevel = 1

        # Short-circuit and deal with help right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0

        user, apikey, projectid, url = args.username, args.apikey, \
                                       args.projectid, args.url

        #FIXME(usrleon): Here should be restrict for project id same as
        # for username or apikey but for compatibility it is not.

        if not user:
            raise exceptions.CommandError("You must provide a username, either via "
                               "--username or via env[NOVA_USERNAME]")
        if not apikey:
            raise exceptions.CommandError("You must provide an API key, either via "
                               "--apikey or via env[NOVA_API_KEY]")

        self.cs = self.get_api_class(options.version)(user, apikey, projectid, url)

        try:
            self.cs.authenticate()
        except exceptions.Unauthorized:
            raise exceptions.CommandError("Invalid OpenStack Nova credentials.")

        args.func(self.cs, args)

    def get_api_class(self, version):
        try:
            return {
                "1.0": shell_v1_0.CLIENT_CLASS,
                "1.1": shell_v1_1.CLIENT_CLASS,
            }[version]
        except KeyError:
            return shell_v1_0.CLIENT_CLASS

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
                raise exceptions.CommandError("'%s' is not a valid subcommand." %
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

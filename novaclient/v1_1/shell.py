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
import getpass
import httplib2
import os
import prettytable
import sys
import textwrap
import uuid

import novaclient.v1_1
from novaclient.v1_1 import exceptions
from novaclient.v1_1 import servers


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)

# Sentinal for boot --key
AUTO_KEY = object()


# Decorator for args
def arg(*args, **kwargs):
    def _decorator(func):
        # Because of the sematics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator


class CommandError(Exception):
    pass


def env(e):
    return os.environ.get(e, '')


class OpenStackShell(object):

    # Hook for the test suite to inject a fake server.
    _api_class = novaclient.v1_1.Client

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='nova',
            description=__doc__.strip(),
            epilog='See "nova help COMMAND" '\
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        self.parser.add_argument('-h', '--help',
            action='help',
            help=argparse.SUPPRESS,
        )

        self.parser.add_argument('--debug',
            default=False,
            action='store_true',
            help=argparse.SUPPRESS)

        self.parser.add_argument('--username',
            default=env('NOVA_USERNAME'),
            help='Defaults to env[NOVA_USERNAME].')

        self.parser.add_argument('--apikey',
            default=env('NOVA_API_KEY'),
            help='Defaults to env[NOVA_API_KEY].')

        self.parser.add_argument('--projectid',
            default=env('NOVA_PROJECT_ID'),
            help='Defaults to env[NOVA_PROJECT_ID].')

        auth_url = env('NOVA_URL')
        if auth_url == '':
            auth_url = 'https://auth.api.rackspacecloud.com/v1.0'
        self.parser.add_argument('--url',
            default=auth_url,
            help='Defaults to env[NOVA_URL].')

        # Subcommands
        subparsers = self.parser.add_subparsers(metavar='<subcommand>')
        self.subcommands = {}

        # Everything that's do_* is a subcommand.
        for attr in (a for a in dir(self) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(self, attr)
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
        # Parse args and call whatever callback was selected
        args = self.parser.parse_args(argv)

        # Short-circuit and deal with help right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0

        # Deal with global arguments
        if args.debug:
            httplib2.debuglevel = 1

        user, apikey, projectid, url = args.username, args.apikey, \
                                       args.projectid, args.url

        #FIXME(usrleon): Here should be restrict for project id same as
        # for username or apikey but for compatibility it is not.

        if not user:
            raise CommandError("You must provide a username, either via "
                               "--username or via env[NOVA_USERNAME]")
        if not apikey:
            raise CommandError("You must provide an API key, either via "
                               "--apikey or via env[NOVA_API_KEY]")

        self.cs = self._api_class(user, apikey, projectid, url)
        try:
            self.cs.authenticate()
        except exceptions.Unauthorized:
            raise CommandError("Invalid OpenStack Nova credentials.")

        args.func(args)

    @arg('command', metavar='<subcommand>', nargs='?',
                    help='Display help for <subcommand>')
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if args.command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise CommandError("'%s' is not a valid subcommand." %
                                                         args.command)
        else:
            self.parser.print_help()

    def _boot(self, args, reservation_id=None, min_count=None, max_count=None):
        """Boot a new server."""
        flavor = args.flavor or self.cs.flavors.find(ram=256)
        image = args.image or self.cs.images.find(name="Ubuntu 10.04 LTS "\
                                                       "(lucid)")

        metadata = dict(v.split('=') for v in args.meta)

        files = {}
        for f in args.files:
            dst, src = f.split('=', 1)
            try:
                files[dst] = open(src)
            except IOError, e:
                raise CommandError("Can't open '%s': %s" % (src, e))

        if args.key is AUTO_KEY:
            possible_keys = [os.path.join(os.path.expanduser('~'), '.ssh', k)
                             for k in ('id_dsa.pub', 'id_rsa.pub')]
            for k in possible_keys:
                if os.path.exists(k):
                    keyfile = k
                    break
            else:
                raise CommandError("Couldn't find a key file: tried "
                                   "~/.ssh/id_dsa.pub or ~/.ssh/id_rsa.pub")
        elif args.key:
            keyfile = args.key
        else:
            keyfile = None

        if keyfile:
            try:
                files['/root/.ssh/authorized_keys2'] = open(keyfile)
            except IOError, e:
                raise CommandError("Can't open '%s': %s" % (keyfile, e))

        return (args.name, image, flavor, metadata, files)

    @arg('--flavor',
         default=None,
         metavar='<flavor>',
         help="Flavor ID (see 'novaclient flavors'). "\
              "Defaults to 256MB RAM instance.")
    @arg('--image',
         default=None,
         metavar='<image>',
         help="Image ID (see 'novaclient images'). "\
              "Defaults to Ubuntu 10.04 LTS.")
    @arg('--meta',
         metavar="<key=value>",
         action='append',
         default=[],
         help="Record arbitrary key/value metadata. "\
              "May be give multiple times.")
    @arg('--file',
         metavar="<dst-path=src-path>",
         action='append',
         dest='files',
         default=[],
         help="Store arbitrary files from <src-path> locally to <dst-path> "\
              "on the new server. You may store up to 5 files.")
    @arg('--key',
         metavar='<path>',
         nargs='?',
         const=AUTO_KEY,
         help="Key the server with an SSH keypair. "\
              "Looks in ~/.ssh for a key, "\
              "or takes an explicit <path> to one.")
    @arg('name', metavar='<name>', help='Name for the new server')
    def do_boot(self, args):
        """Boot a new server."""
        name, image, flavor, metadata, files = self._boot(args)

        server = self.cs.servers.create(args.name, image, flavor,
                                        meta=metadata,
                                        files=files)
        print_dict(server._info)

    def _translate_flavor_keys(self, collection):
        convert = [('ram', 'memory_mb'), ('disk', 'local_gb')]
        for item in collection:
            keys = item.__dict__.keys()
            for from_key, to_key in convert:
                if from_key in keys and to_key not in keys:
                    setattr(item, to_key, item._info[from_key])

    @arg('--fixed_ip',
        dest='fixed_ip',
        metavar='<fixed_ip>',
        default=None,
        help='Only match against fixed IP.')
    @arg('--reservation_id',
        dest='reservation_id',
        metavar='<reservation_id>',
        default=None,
        help='Only return instances that match reservation_id.')
    @arg('--recurse_zones',
        dest='recurse_zones',
        metavar='<0|1>',
        nargs='?',
        type=int,
        const=1,
        default=0,
        help='Recurse through all zones if set.')
    @arg('--ip',
        dest='ip',
        metavar='<ip_regexp>',
        default=None,
        help='Search with regular expression match by IP address')
    @arg('--ip6',
        dest='ip6',
        metavar='<ip6_regexp>',
        default=None,
        help='Search with regular expression match by IPv6 address')
    @arg('--server_name',
        dest='server_name',
        metavar='<name_regexp>',
        default=None,
        help='Search with regular expression match by server name')
    @arg('--name',
        dest='display_name',
        metavar='<name_regexp>',
        default=None,
        help='Search with regular expression match by display name')
    @arg('--instance_name',
        dest='name',
        metavar='<name_regexp>',
        default=None,
        help='Search with regular expression match by instance name')
    def do_list(self, args):
        """List active servers."""
        recurse_zones = args.recurse_zones
        search_opts = {
                'reservation_id': args.reservation_id,
                'fixed_ip': args.fixed_ip,
                'recurse_zones': recurse_zones,
                'ip': args.ip,
                'ip6': args.ip6,
                'name': args.name,
                'server_name': args.server_name,
                'display_name': args.display_name}
        if recurse_zones:
            to_print = ['UUID', 'Name', 'Status', 'Public IP', 'Private IP']
        else:
            to_print = ['ID', 'Name', 'Status', 'Public IP', 'Private IP']
        print_list(self.cs.servers.list(search_opts=search_opts),
                to_print)

    def do_flavor_list(self, args):
        """Print a list of available 'flavors' (sizes of servers)."""
        flavors = self.cs.flavors.list()
        self._translate_flavor_keys(flavors)
        print_list(flavors, [
            'ID',
            'Name',
            'Memory_MB',
            'Swap',
            'Local_GB',
            'VCPUs',
            'RXTX_Quota',
            'RXTX_Cap'])

    def do_image_list(self, args):
        """Print a list of available images to boot from."""
        print_list(self.cs.images.list(), ['ID', 'Name', 'Status'])

    @arg('server', metavar='<server>', help='Name or ID of server.')
    @arg('name', metavar='<name>', help='Name of backup or snapshot.')
    @arg('--image-type',
         metavar='<backup|snapshot>',
         default='snapshot',
         help='type of image (default: snapshot)')
    @arg('--backup-type',
         metavar='<daily|weekly>',
         default=None,
         help='type of backup')
    @arg('--rotation',
         default=None,
         type=int,
         metavar='<rotation>',
         help="Number of backups to retain. Used for backup image_type.")
    def do_create_image(self, args):
        """Create a new image by taking a snapshot of a running server."""
        server = self._find_server(args.server)
        server.create_image(args.name)

    @arg('image', metavar='<image>', help='Name or ID of image.')
    def do_image_delete(self, args):
        """
        Delete an image.

        It should go without saying, but you can only delete images you
        created.
        """
        image = self._find_image(args.image)
        image.delete()

    @arg('--hard',
        dest='reboot_type',
        action='store_const',
        const=servers.REBOOT_HARD,
        default=servers.REBOOT_SOFT,
        help='Perform a hard reboot (instead of a soft one).')
    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_reboot(self, args):
        """Reboot a server."""
        self._find_server(args.server).reboot(args.reboot_type)

    @arg('server', metavar='<server>', help='Name or ID of server.')
    @arg('image', metavar='<image>', help="Name or ID of new image.")
    def do_rebuild(self, args):
        """Shutdown, re-image, and re-boot a server."""
        server = self._find_server(args.server)
        image = self._find_image(args.image)
        server.rebuild(image)

    @arg('server', metavar='<server>', help='Name (old name) or ID of server.')
    @arg('name', metavar='<name>', help='New name for the server.')
    def do_rename(self, args):
        """Rename a server."""
        self._find_server(args.server).update(name=args.name)

    @arg('server', metavar='<server>', help='Name or ID of server.')
    @arg('flavor', metavar='<flavor>', help="Name or ID of new flavor.")
    def do_resize(self, args):
        """Resize a server."""
        server = self._find_server(args.server)
        flavor = self._find_flavor(args.flavor)
        server.resize(flavor)

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_migrate(self, args):
        """Migrate a server."""
        self._find_server(args.server).migrate()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_pause(self, args):
        """Pause a server."""
        self._find_server(args.server).pause()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_unpause(self, args):
        """Unpause a server."""
        self._find_server(args.server).unpause()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_suspend(self, args):
        """Suspend a server."""
        self._find_server(args.server).suspend()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_resume(self, args):
        """Resume a server."""
        self._find_server(args.server).resume()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_rescue(self, args):
        """Rescue a server."""
        self._find_server(args.server).rescue()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_unrescue(self, args):
        """Unrescue a server."""
        self._find_server(args.server).unrescue()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_diagnostics(self, args):
        """Retrieve server diagnostics."""
        print_dict(self.cs.servers.diagnostics(args.server)[1])

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_actions(self, args):
        """Retrieve server actions."""
        print_list(
            self.cs.servers.actions(args.server),
            ["Created_At", "Action", "Error"])

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_resize_confirm(self, args):
        """Confirm a previous resize."""
        self._find_server(args.server).confirm_resize()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_resize_revert(self, args):
        """Revert a previous resize (and return to the previous VM)."""
        self._find_server(args.server).revert_resize()

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_root_password(self, args):
        """
        Change the root password for a server.
        """
        server = self._find_server(args.server)
        p1 = getpass.getpass('New password: ')
        p2 = getpass.getpass('Again: ')
        if p1 != p2:
            raise CommandError("Passwords do not match.")
        server.change_password(p1)

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_show(self, args):
        """Show details about the given server."""
        s = self._find_server(args.server)

        info = s._info.copy()
        addresses = info.pop('addresses')
        for network_name in addresses.keys():
            ips = map(lambda x: x["addr"], addresses[network_name])
            info['%s ip' % network_name] = ', '.join(ips)

        flavor = info.get('flavor', {})
        flavor_id = flavor.get('id')
        if flavor_id:
            info['flavor'] = self._find_flavor(flavor_id).name
        image = info.get('image', {})
        image_id = image.get('id')
        if image_id:
            info['image'] = self._find_image(image_id).name

        print_dict(info)

    @arg('server', metavar='<server>', help='Name or ID of server.')
    def do_delete(self, args):
        """Immediately shut down and delete a server."""
        self._find_server(args.server).delete()

    def _find_server(self, server):
        """Get a server by name or ID."""
        return self._find_resource(self.cs.servers, server)

    def _find_image(self, image):
        """Get an image by name or ID."""
        return self._find_resource(self.cs.images, image)

    def _find_flavor(self, flavor):
        """Get a flavor by name, ID, or RAM size."""
        try:
            return self._find_resource(self.cs.flavors, flavor)
        except exceptions.NotFound:
            return self.cs.flavors.find(ram=flavor)

    def _find_resource(self, manager, name_or_id):
        """Helper for the _find_* methods."""
        try:
            if isinstance(name_or_id, int) or name_or_id.isdigit():
                return manager.get(int(name_or_id))

            try:
                uuid.UUID(name_or_id)
                return manager.get(name_or_id)
            except ValueError:
                return manager.find(name=name_or_id)
        except exceptions.NotFound:
            raise CommandError("No %s with a name or ID of '%s' exists." %
                         (manager.resource_class.__name__.lower(), name_or_id))


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


# Helpers
def print_list(objs, fields, formatters={}):
    pt = prettytable.PrettyTable([f for f in fields], caching=False)
    pt.aligns = ['l' for f in fields]

    for o in objs:
        row = []
        for field in fields:
            if field in formatters:
                row.append(formatters[field](o))
            else:
                field_name = field.lower().replace(' ', '_')
                data = getattr(o, field_name, '')
                row.append(data)
        pt.add_row(row)

    pt.printt(sortby=fields[0])


def print_dict(d):
    pt = prettytable.PrettyTable(['Property', 'Value'], caching=False)
    pt.aligns = ['l', 'l']
    [pt.add_row(list(r)) for r in d.iteritems()]
    pt.printt(sortby='Property')


def main():
    try:
        OpenStackShell().main(sys.argv[1:])

    except Exception, e:
        if httplib2.debuglevel == 1:
            raise  # dump stack.
        else:
            print >> sys.stderr, e
        sys.exit(1)

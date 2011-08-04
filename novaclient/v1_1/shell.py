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

import getpass
import os
import uuid

from novaclient import exceptions
from novaclient import utils
from novaclient.v1_1 import client
from novaclient.v1_1 import servers


CLIENT_CLASS = client.Client


AUTO_KEY = object()


def _translate_flavor_keys(collection):
    convert = [('ram', 'memory_mb'), ('disk', 'local_gb')]
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])

@utils.arg('--flavor',
     default=None,
     metavar='<flavor>',
     help="Flavor ID (see 'nova flavors'). "\
          "Defaults to 256MB RAM instance.")
@utils.arg('--image',
     default=None,
     metavar='<image>',
     help="Image ID (see 'nova images'). "\
          "Defaults to Ubuntu 10.04 LTS.")
@utils.arg('--meta',
     metavar="<key=value>",
     action='append',
     default=[],
     help="Record arbitrary key/value metadata. "\
          "May be give multiple times.")
@utils.arg('--file',
     metavar="<dst-path=src-path>",
     action='append',
     dest='files',
     default=[],
     help="Store arbitrary files from <src-path> locally to <dst-path> "\
          "on the new server. You may store up to 5 files.")
@utils.arg('--key',
     metavar='<path>',
     nargs='?',
     const=AUTO_KEY,
     help="Key the server with an SSH keypair. "\
          "Looks in ~/.ssh for a key, "\
          "or takes an explicit <path> to one.")
@utils.arg('name', metavar='<name>', help='Name for the new server')
def do_boot(cs, args):
    """Boot a new server."""
    name, image, flavor, metadata, files = _boot(cs, args)
    server = cs.servers.create(args.name, image, flavor,
                               meta=metadata, files=files)
    utils.print_dict(server._info)


def _boot(cs, args):
    """Boot a new server."""

    flavor = args.flavor or cs.flavors.find(ram=256)
    image = args.image or cs.images.find(name="Ubuntu 10.04 LTS "\
                                                   "(lucid)")

    metadata = dict(v.split('=') for v in args.meta)

    files = {}
    for f in args.files:
        dst, src = f.split('=', 1)
        try:
            files[dst] = open(src)
        except IOError, e:
            raise exceptions.CommandError("Can't open '%s': %s" % (src, e))

    if args.key is AUTO_KEY:
        possible_keys = [os.path.join(os.path.expanduser('~'), '.ssh', k)
                         for k in ('id_dsa.pub', 'id_rsa.pub')]
        for k in possible_keys:
            if os.path.exists(k):
                keyfile = k
                break
        else:
            raise exceptions.CommandError("Couldn't find a key file: tried "
                               "~/.ssh/id_dsa.pub or ~/.ssh/id_rsa.pub")
    elif args.key:
        keyfile = args.key
    else:
        keyfile = None

    if keyfile:
        try:
            files['/root/.ssh/authorized_keys2'] = open(keyfile)
        except IOError, e:
            raise exceptions.CommandError("Can't open '%s': %s" % (keyfile, e))

    return (args.name, image, flavor, metadata, files)


def do_flavor_list(cs, args):
    """Print a list of available 'flavors' (sizes of servers)."""
    flavors = cs.flavors.list()
    _translate_flavor_keys(flavors)
    utils.print_list(flavors, [
        'ID',
        'Name',
        'Memory_MB',
        'Swap',
        'Local_GB',
        'VCPUs',
        'RXTX_Quota',
        'RXTX_Cap'])

def do_image_list(cs, args):
    """Print a list of available images to boot from."""
    utils.print_list(cs.images.list(), ['ID', 'Name', 'Status'])

@utils.arg('image', metavar='<image>', help='Name or ID of image.')
def do_image_delete(cs, args):
    """
    Delete an image.

    It should go without saying, but you can only delete images you
    created.
    """
    image = _find_image(cs, args.image)
    image.delete()

@utils.arg('--fixed_ip',
    dest='fixed_ip',
    metavar='<fixed_ip>',
    default=None,
    help='Only match against fixed IP.')
@utils.arg('--reservation_id',
    dest='reservation_id',
    metavar='<reservation_id>',
    default=None,
    help='Only return instances that match reservation_id.')
@utils.arg('--recurse_zones',
    dest='recurse_zones',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Recurse through all zones if set.')
@utils.arg('--ip',
    dest='ip',
    metavar='<ip_regexp>',
    default=None,
    help='Search with regular expression match by IP address')
@utils.arg('--ip6',
    dest='ip6',
    metavar='<ip6_regexp>',
    default=None,
    help='Search with regular expression match by IPv6 address')
@utils.arg('--server_name',
    dest='server_name',
    metavar='<name_regexp>',
    default=None,
    help='Search with regular expression match by server name')
@utils.arg('--name',
    dest='display_name',
    metavar='<name_regexp>',
    default=None,
    help='Search with regular expression match by display name')
@utils.arg('--instance_name',
    dest='name',
    metavar='<name_regexp>',
    default=None,
    help='Search with regular expression match by instance name')
def do_list(cs, args):
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
    utils.print_list(cs.servers.list(search_opts=search_opts),
            to_print)

@utils.arg('--hard',
    dest='reboot_type',
    action='store_const',
    const=servers.REBOOT_HARD,
    default=servers.REBOOT_SOFT,
    help='Perform a hard reboot (instead of a soft one).')
@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_reboot(cs, args):
    """Reboot a server."""
    _find_server(cs, args.server).reboot(args.reboot_type)

@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('image', metavar='<image>', help="Name or ID of new image.")
def do_rebuild(cs, args):
    """Shutdown, re-image, and re-boot a server."""
    server = _find_server(cs, args.server)
    image = _find_image(cs, args.image)
    server.rebuild(image)

@utils.arg('server', metavar='<server>', help='Name (old name) or ID of server.')
@utils.arg('name', metavar='<name>', help='New name for the server.')
def do_rename(cs, args):
    """Rename a server."""
    _find_server(cs, args.server).update(name=args.name)

@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('flavor', metavar='<flavor>', help="Name or ID of new flavor.")
def do_resize(cs, args):
    """Resize a server."""
    server = _find_server(cs, args.server)
    flavor = _find_flavor(cs, args.flavor)
    server.resize(flavor)

@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_resize_confirm(cs, args):
    """Confirm a previous resize."""
    _find_server(cs, args.server).confirm_resize()

@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_resize_revert(cs, args):
    """Revert a previous resize (and return to the previous VM)."""
    _find_server(cs, args.server).revert_resize()

@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_root_password(cs, args):
    """
    Change the root password for a server.
    """
    server = _find_server(cs, args.server)
    p1 = getpass.getpass('New password: ')
    p2 = getpass.getpass('Again: ')
    if p1 != p2:
        raise exceptions.CommandError("Passwords do not match.")
    server.change_password(p1)

@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('name', metavar='<name>', help='Name of snapshot.')
def do_image_create(cs, args):
    """Create a new image by taking a snapshot of a running server."""
    server = _find_server(cs, args.server)
    cs.servers.create_image(server, args.name)

@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_show(cs, args):
    """Show details about the given server."""
    s = _find_server(cs, args.server)

    info = s._info.copy()
    addresses = info.pop('addresses', [])
    for addrtype in addresses:
        ips = map(lambda x: x['addr'], addresses[addrtype])
        info['%s ip' % addrtype] = ', '.join(ips)

    flavor = info.get('flavor', {})
    flavor_id = flavor.get('id', '')
    info['flavor'] = _find_flavor(cs, flavor_id).name

    image = info.get('image', {})
    image_id = image.get('id', '')
    info['image'] = _find_image(cs, image_id).name

    utils.print_dict(info)

@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_delete(cs, args):
    """Immediately shut down and delete a server."""
    _find_server(cs, args.server).delete()

def _find_server(cs, server):
    """Get a server by name or ID."""
    return _find_resource(cs.servers, server)

def _find_image(cs, image):
    """Get an image by name or ID."""
    return _find_resource(cs.images, image)

def _find_flavor(cs, flavor):
    """Get a flavor by name, ID, or RAM size."""
    try:
        return _find_resource(cs.flavors, flavor)
    except exceptions.NotFound:
        return cs.flavors.find(ram=flavor)

def _find_resource(manager, name_or_id):
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
        raise exceptions.CommandError("No %s with a name or ID of '%s' exists." %
                     (manager.resource_class.__name__.lower(), name_or_id))


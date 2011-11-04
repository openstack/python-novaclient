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

from novaclient import exceptions
from novaclient import utils
from novaclient.v1_1 import client
from novaclient.v1_1 import servers


CLIENT_CLASS = client.Client


AUTO_KEY = object()


def _boot(cs, args, reservation_id=None, min_count=None, max_count=None):
    """Boot a new server."""
    if min_count is None:
        min_count = 1
    if max_count is None:
        max_count = min_count
    if min_count > max_count:
        raise exceptions.CommandError("min_instances should be <= "
                                      "max_instances")
    if not min_count or not max_count:
        raise exceptions.CommandError("min_instances nor max_instances should"
                                      "be 0")

    if not args.image:
        raise exceptions.CommandError("you need to specify a Image ID ")
    if not args.flavor:
        raise exceptions.CommandError("you need to specify a Flavor ID ")

    flavor = args.flavor
    image = args.image

    metadata = dict(v.split('=') for v in args.meta)

    files = {}
    for f in args.files:
        dst, src = f.split('=', 1)
        try:
            files[dst] = open(src)
        except IOError, e:
            raise exceptions.CommandError("Can't open '%s': %s" % (src, e))

    # use the os-keypair extension
    key_name = None
    if args.key_name is not None:
        key_name = args.key_name

    # or use file injection functionality (independent of os-keypair extension)
    keyfile = None
    if args.key_path is AUTO_KEY:
        possible_keys = [os.path.join(os.path.expanduser('~'), '.ssh', k)
                         for k in ('id_dsa.pub', 'id_rsa.pub')]
        for k in possible_keys:
            if os.path.exists(k):
                keyfile = k
                break
        else:
            raise exceptions.CommandError("Couldn't find a key file: tried "
                               "~/.ssh/id_dsa.pub or ~/.ssh/id_rsa.pub")
    elif args.key_path:
        keyfile = args.key_path

    if keyfile:
        try:
            files['/root/.ssh/authorized_keys2'] = open(keyfile)
        except IOError, e:
            raise exceptions.CommandError("Can't open '%s': %s" % (keyfile, e))

    if args.user_data:
        try:
            user_data = open(args.user_data)
        except IOError, e:
            raise exceptions.CommandError("Can't open '%s': %s" % \
                                          (args.user_data, e))
    else:
        user_data = None

    if args.availability_zone:
        availability_zone = args.availability_zone
    else:
        availability_zone = None

    if args.security_groups:
        security_groups = args.security_groups.split(',')
    else:
        security_groups = None
    return (args.name, image, flavor, metadata, files, key_name,
            reservation_id, min_count, max_count, user_data, \
            availability_zone, security_groups)


@utils.arg('--flavor',
     default=None,
     metavar='<flavor>',
     help="Flavor ID (see 'nova flavor-list').")
@utils.arg('--image',
     default=None,
     metavar='<image>',
     help="Image ID (see 'nova image-list'). ")
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
@utils.arg('--key_path',
     metavar='<key_path>',
     nargs='?',
     const=AUTO_KEY,
     help="Key the server with an SSH keypair. "\
          "Looks in ~/.ssh for a key, "\
          "or takes an explicit <path> to one. (uses --file functionality)")
@utils.arg('--key_name',
     metavar='<key_name>',
     help="Key name of keypair that should be created earlier with \
           the command keypair-add")
@utils.arg('name', metavar='<name>', help='Name for the new server')
@utils.arg('--user_data',
     default=None,
     metavar='<user-data>',
     help="user data file to pass to be exposed by the metadata server.")
@utils.arg('--availability_zone',
     default=None,
     metavar='<availability-zone>',
     help="zone id.")
@utils.arg('--security_groups',
     default=None,
     metavar='<security_groups>',
     help="comma separated list of security group names.")
def do_boot(cs, args):
    """Boot a new server."""
    name, image, flavor, metadata, files, key_name, reservation_id, \
        min_count, max_count, user_data, availability_zone, \
        security_groups = _boot(cs, args)

    server = cs.servers.create(args.name, image, flavor,
                                    meta=metadata,
                                    files=files,
                                    min_count=min_count,
                                    max_count=max_count,
                                    userdata=user_data,
                                    availability_zone=availability_zone,
                                    security_groups=security_groups,
                                    key_name=key_name)

    # Keep any information (like adminPass) returned by create
    info = server._info
    server = cs.servers.get(info['id'])
    info.update(server._info)

    flavor = info.get('flavor', {})
    flavor_id = flavor.get('id', '')
    info['flavor'] = _find_flavor(cs, flavor_id).name

    image = info.get('image', {})
    image_id = image.get('id', '')
    info['image'] = _find_image(cs, image_id).name

    info.pop('links', None)
    info.pop('addresses', None)

    utils.print_dict(info)


@utils.arg('--flavor',
     default=None,
     metavar='<flavor>',
     help="Flavor ID (see 'nova flavor-list')")
@utils.arg('--image',
     default=None,
     metavar='<image>',
     help="Image ID (see 'nova image-list').")
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
@utils.arg('--reservation_id',
     default=None,
     metavar='<reservation_id>',
     help="Reservation ID (a UUID). "\
          "If unspecified will be generated by the server.")
@utils.arg('--min_instances',
     default=None,
     type=int,
     metavar='<number>',
     help="The minimum number of instances to build. "\
             "Defaults to 1.")
@utils.arg('--max_instances',
     default=None,
     type=int,
     metavar='<number>',
     help="The maximum number of instances to build. "\
             "Defaults to 'min_instances' setting.")
@utils.arg('name', metavar='<name>', help='Name for the new server')
def do_zone_boot(cs, args):
    """Boot a new server, potentially across Zones."""
    reservation_id = args.reservation_id
    min_count = args.min_instances
    max_count = args.max_instances
    name, image, flavor, metadata, \
            files, reservation_id, min_count, max_count,\
            user_data, availability_zone, security_groups = \
                             _boot(cs, args,
                                        reservation_id=reservation_id,
                                        min_count=min_count,
                                        max_count=max_count)

    reservation_id = cs.zones.boot(args.name, image, flavor,
                                        meta=metadata,
                                        files=files,
                                        reservation_id=reservation_id,
                                        min_count=min_count,
                                        max_count=max_count)
    print "Reservation ID=", reservation_id


def _translate_flavor_keys(collection):
    convert = [('ram', 'memory_mb'), ('disk', 'local_gb')]
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


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


@utils.arg('image',
     metavar='<image>',
     help="Name or ID of image")
@utils.arg('action',
     metavar='<action>',
     choices=['set', 'delete'],
     help="Actions: 'set' or 'delete'")
@utils.arg('metadata',
     metavar='<key=value>',
     nargs='+',
     action='append',
     default=[],
     help='Metadata to add/update or delete (only key is necessary on delete)')
def do_image_meta(cs, args):
    """Set or Delete metadata on an image."""
    image = _find_image(cs, args.image)
    metadata = {}
    for metadatum in args.metadata[0]:
        # Can only pass the key in on 'delete'
        # So this doesn't have to have '='
        if metadatum.find('=') > -1:
            (key, value) = metadatum.split('=', 1)
        else:
            key = metadatum
            value = None

        metadata[key] = value

    if args.action == 'set':
        cs.images.set_meta(image, metadata)
    elif args.action == 'delete':
        cs.images.delete_meta(image, metadata.keys())


def _print_image(image):
    links = image.links
    info = image._info.copy()
    info.pop('links')
    utils.print_dict(info)


@utils.arg('image',
     metavar='<image>',
     help="Name or ID of image")
def do_image_show(cs, args):
    """Show details about the given image."""
    image = _find_image(cs, args.image)
    _print_image(image)


@utils.arg('image', metavar='<image>', help='Name or ID of image.')
def do_image_delete(cs, args):
    """
    Delete an image.

    It should go without saying, but you can only delete images you
    created.
    """
    image = _find_image(cs, args.image)
    image.delete()


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
@utils.arg('--name',
    dest='name',
    metavar='<name_regexp>',
    default=None,
    help='Search with regular expression match by name')
@utils.arg('--instance_name',
    dest='instance_name',
    metavar='<name_regexp>',
    default=None,
    help='Search with regular expression match by instance name')
@utils.arg('--status',
    dest='status',
    metavar='<status>',
    default=None,
    help='Search by server status')
@utils.arg('--flavor',
    dest='flavor',
    metavar='<flavor>',
    type=int,
    default=None,
    help='Search by flavor ID')
@utils.arg('--image',
    dest='image',
    metavar='<image>',
    default=None,
    help='Search by image ID')
@utils.arg('--host',
    dest='host',
    metavar='<hostname>',
    default=None,
    help='Search instances by hostname to which they are assigned')
def do_list(cs, args):
    """List active servers."""
    recurse_zones = args.recurse_zones
    search_opts = {
            'reservation_id': args.reservation_id,
            'recurse_zones': recurse_zones,
            'ip': args.ip,
            'ip6': args.ip6,
            'name': args.name,
            'image': args.image,
            'flavor': args.flavor,
            'status': args.status,
            'host': args.host,
            'instance_name': args.instance_name}

    if recurse_zones:
        id_col = 'UUID'
    else:
        id_col = 'ID'

    columns = [id_col, 'Name', 'Status', 'Networks']
    formatters = {'Networks': _format_servers_list_networks}
    utils.print_list(cs.servers.list(search_opts=search_opts), columns,
                     formatters)


def _format_servers_list_networks(server):
    output = []
    for (network, addresses) in server.networks.items():
        if len(addresses) == 0:
            continue
        addresses_csv = ', '.join(addresses)
        group = "%s=%s" % (network, addresses_csv)
        output.append(group)

    return '; '.join(output)


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
@utils.arg('--password', dest='password', metavar='<password>', default=False,
           help="Set the provided password on the rebuild instance.")
def do_rebuild(cs, args):
    """Shutdown, re-image, and re-boot a server."""
    server = _find_server(cs, args.server)
    image = _find_image(cs, args.image)

    if args.password != False:
        _password = args.password
    else:
        _password = None

    s = server.rebuild(image, _password)
    _print_server(cs, s)


@utils.arg('server', metavar='<server>',
           help='Name (old name) or ID of server.')
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
def do_migrate(cs, args):
    """Migrate a server."""
    _find_server(cs, args.server).migrate()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_pause(cs, args):
    """Pause a server."""
    _find_server(cs, args.server).pause()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_unpause(cs, args):
    """Unpause a server."""
    _find_server(cs, args.server).unpause()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_suspend(cs, args):
    """Suspend a server."""
    _find_server(cs, args.server).suspend()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_resume(cs, args):
    """Resume a server."""
    _find_server(cs, args.server).resume()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_rescue(cs, args):
    """Rescue a server."""
    _find_server(cs, args.server).rescue()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_unrescue(cs, args):
    """Unrescue a server."""
    _find_server(cs, args.server).unrescue()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_diagnostics(cs, args):
    """Retrieve server diagnostics."""
    utils.print_dict(cs.servers.diagnostics(args.server)[1])


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_actions(cs, args):
    """Retrieve server actions."""
    utils.print_list(
        cs.servers.actions(args.server),
        ["Created_At", "Action", "Error"])


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


@utils.arg('server',
     metavar='<server>',
     help="Name or ID of server")
@utils.arg('action',
     metavar='<action>',
     choices=['set', 'delete'],
     help="Actions: 'set' or 'delete'")
@utils.arg('metadata',
     metavar='<key=value>',
     nargs='+',
     action='append',
     default=[],
     help='Metadata to set or delete (only key is necessary on delete)')
def do_meta(cs, args):
    """Set or Delete metadata on a server."""
    server = _find_server(cs, args.server)
    metadata = {}
    for metadatum in args.metadata[0]:
        # Can only pass the key in on 'delete'
        # So this doesn't have to have '='
        if metadatum.find('=') > -1:
            (key, value) = metadatum.split('=', 1)
        else:
            key = metadatum
            value = None

        metadata[key] = value

    if args.action == 'set':
        cs.servers.set_meta(server, metadata)
    elif args.action == 'delete':
        cs.servers.delete_meta(server, metadata.keys())


def _print_server(cs, server):
    # By default when searching via name we will do a
    # findall(name=blah) and due a REST /details which is not the same
    # as a .get() and doesn't get the information about flavors and
    # images. This fix it as we redo the call with the id which does a
    # .get() to get all informations.
    if not 'flavor' in server._info:
        server = _find_server(cs, server.id)

    networks = server.networks
    info = server._info.copy()
    for network_label, address_list in networks.items():
        info['%s network' % network_label] = ', '.join(address_list)

    flavor = info.get('flavor', {})
    flavor_id = flavor.get('id', '')
    info['flavor'] = _find_flavor(cs, flavor_id).name

    image = info.get('image', {})
    image_id = image.get('id', '')
    info['image'] = _find_image(cs, image_id).name

    info.pop('links', None)
    info.pop('addresses', None)

    utils.print_dict(info)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_show(cs, args):
    """Show details about the given server."""
    s = _find_server(cs, args.server)
    _print_server(cs, s)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_delete(cs, args):
    """Immediately shut down and delete a server."""
    _find_server(cs, args.server).delete()


def _find_server(cs, server):
    """Get a server by name or ID."""
    return utils.find_resource(cs.servers, server)


def _find_image(cs, image):
    """Get an image by name or ID."""
    return utils.find_resource(cs.images, image)


def _find_flavor(cs, flavor):
    """Get a flavor by name, ID, or RAM size."""
    try:
        return utils.find_resource(cs.flavors, flavor)
    except exceptions.NotFound:
        return cs.flavors.find(ram=flavor)


# --zone_username is required since --username is already used.
@utils.arg('zone', metavar='<zone_id>', help='ID of the zone', default=None)
@utils.arg('--api_url', dest='api_url', default=None, help='New URL.')
@utils.arg('--zone_username', dest='zone_username', default=None,
                        help='New zone username.')
@utils.arg('--password', dest='password', default=None, help='New password.')
@utils.arg('--weight_offset', dest='weight_offset', default=None,
                        help='Child Zone weight offset.')
@utils.arg('--weight_scale', dest='weight_scale', default=None,
                        help='Child Zone weight scale.')
def do_zone(cs, args):
    """Show or edit a child zone. No zone arg for this zone."""
    zone = cs.zones.get(args.zone)

    # If we have some flags, update the zone
    zone_delta = {}
    if args.api_url:
        zone_delta['api_url'] = args.api_url
    if args.zone_username:
        zone_delta['username'] = args.zone_username
    if args.password:
        zone_delta['password'] = args.password
    if args.weight_offset:
        zone_delta['weight_offset'] = args.weight_offset
    if args.weight_scale:
        zone_delta['weight_scale'] = args.weight_scale
    if zone_delta:
        zone.update(**zone_delta)
    else:
        utils.print_dict(zone._info)


def do_zone_info(cs, args):
    """Get this zones name and capabilities."""
    zone = cs.zones.info()
    utils.print_dict(zone._info)


@utils.arg('zone_name', metavar='<zone_name>',
            help='Name of the child zone being added.')
@utils.arg('api_url', metavar='<api_url>', help="URL for the Zone's Auth API")
@utils.arg('--zone_username', metavar='<zone_username>',
            help='Optional Authentication username. (Default=None)',
            default=None)
@utils.arg('--password', metavar='<password>',
           help='Authentication password. (Default=None)',
           default=None)
@utils.arg('--weight_offset', metavar='<weight_offset>',
           help='Child Zone weight offset (Default=0.0))',
           default=0.0)
@utils.arg('--weight_scale', metavar='<weight_scale>',
           help='Child Zone weight scale (Default=1.0).',
           default=1.0)
def do_zone_add(cs, args):
    """Add a new child zone."""
    zone = cs.zones.create(args.zone_name, args.api_url,
                           args.zone_username, args.password,
                           args.weight_offset, args.weight_scale)
    utils.print_dict(zone._info)


@utils.arg('zone', metavar='<zone>', help='Name or ID of the zone')
def do_zone_delete(cs, args):
    """Delete a zone."""
    cs.zones.delete(args.zone)


def do_zone_list(cs, args):
    """List the children of a zone."""
    utils.print_list(cs.zones.list(), ['ID', 'Name', 'Is Active', \
                        'API URL', 'Weight Offset', 'Weight Scale'])


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('network_id', metavar='<network_id>', help='Network ID.')
def do_add_fixed_ip(cs, args):
    """Add new IP address to network."""
    server = _find_server(cs, args.server)
    server.add_fixed_ip(args.network_id)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('address', metavar='<address>', help='IP Address.')
def do_remove_fixed_ip(cs, args):
    """Remove an IP address from a server."""
    server = _find_server(cs, args.server)
    server.remove_fixed_ip(args.address)


def _find_volume(cs, volume):
    """Get a volume by ID."""
    return utils.find_resource(cs.volumes, volume)


def _print_volume(cs, volume):
    utils.print_dict(volume._info)


def _translate_volume_keys(collection):
    convert = [('displayName', 'display_name')]
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def do_volume_list(cs, args):
    """List all the volumes."""
    volumes = cs.volumes.list()
    _translate_volume_keys(volumes)

    # Create a list of servers to which the volume is attached
    for vol in volumes:
        servers = [server.get('serverId') for server in vol.attachments]
        setattr(vol, 'attached_to', ','.join(map(str, servers)))
    utils.print_list(volumes, ['ID', 'Status', 'Display Name',
                        'Size', 'Attached to'])


@utils.arg('volume', metavar='<volume>', help='ID of the volume.')
def do_volume_show(cs, args):
    """Show details about a volume."""
    volume = _find_volume(cs, args.volume)
    _print_volume(cs, volume)


@utils.arg('size',
    metavar='<size>',
    type=int,
    help='Size of volume in GB')
@utils.arg('--display_name', metavar='<display_name>',
            help='Optional volume name. (Default=None)',
            default=None)
@utils.arg('--display_description', metavar='<display_description>',
            help='Optional volume description. (Default=None)',
            default=None)
def do_volume_create(cs, args):
    """Add a new volume."""
    cs.volumes.create(args.size, args.display_name, args.display_description)


@utils.arg('volume', metavar='<volume>', help='ID of the volume to delete.')
def do_volume_delete(cs, args):
    """Remove a volume."""
    volume = _find_volume(cs, args.volume)
    volume.delete()


@utils.arg('server',
    metavar='<server>',
    help='Name or ID of server.')
@utils.arg('volume',
    metavar='<volume>',
    type=int,
    help='ID of the volume to attach.')
@utils.arg('device', metavar='<device>',
    help='Name of the device e.g. /dev/vdb.')
def do_volume_attach(cs, args):
    """Attach a volume to a server."""
    cs.volumes.create_server_volume(_find_server(cs, args.server).id,
                                        args.volume,
                                        args.device)


@utils.arg('server',
    metavar='<server>',
    help='Name or ID of server.')
@utils.arg('attachment_id',
    metavar='<volume>',
    type=int,
    help='Attachment ID of the volume.')
def do_volume_detach(cs, args):
    """Detach a volume from a server."""
    cs.volumes.delete_server_volume(_find_server(cs, args.server).id,
                                        args.attachment_id)


def _print_floating_ip_list(floating_ips):
    utils.print_list(floating_ips, ['Ip', 'Instance Id', 'Fixed Ip'])


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('address', metavar='<address>', help='IP Address.')
def do_add_floating_ip(cs, args):
    """Add a floating IP address to a server."""
    server = _find_server(cs, args.server)
    server.add_floating_ip(args.address)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('address', metavar='<address>', help='IP Address.')
def do_remove_floating_ip(cs, args):
    """Remove a floating IP address from a server."""
    server = _find_server(cs, args.server)
    server.remove_floating_ip(args.address)


def do_floating_ip_create(cs, args):
    """Allocate a floating IP for the current tenant."""
    _print_floating_ip_list([cs.floating_ips.create()])


@utils.arg('address', metavar='<address>', help='IP of Floating Ip.')
def do_floating_ip_delete(cs, args):
    """De-allocate a floating IP."""
    floating_ips = cs.floating_ips.list()
    for floating_ip in floating_ips:
        if floating_ip.ip == args.address:
            return cs.floating_ips.delete(floating_ip.id)
    raise exceptions.CommandError("Floating ip %s not found.", args.address)


def do_floating_ip_list(cs, args):
    """List floating ips for this tenant."""
    _print_floating_ip_list(cs.floating_ips.list())


def _print_secgroup_rules(rules):
    class FormattedRule:
        def __init__(self, obj):
            items = (obj if isinstance(obj, dict) else obj._info).items()
            for k, v in items:
                if k == 'ip_range':
                    v = v.get('cidr')
                elif k == 'group':
                    k = 'source_group'
                    v = v.get('name')
                if v == None:
                    v = ''

                setattr(self, k, v)

    rules = [FormattedRule(rule) for rule in rules]
    utils.print_list(rules, ['IP Protocol', 'From Port', 'To Port',
                             'IP Range', 'Source Group'])


def _print_secgroups(secgroups):
    utils.print_list(secgroups, ['Name', 'Description'])


def _get_secgroup(cs, secgroup):
    for s in cs.security_groups.list():
        if secgroup == s.name:
            return s
    raise exceptions.CommandError("Secgroup %s not found" % secgroup)


@utils.arg('secgroup', metavar='<secgroup>', help='ID of security group.')
@utils.arg('ip_proto', metavar='<ip_proto>', help='ip_proto (icmp, tcp, udp).')
@utils.arg('from_port', metavar='<from_port>', help='Port at start of range.')
@utils.arg('to_port', metavar='<to_port>', help='Port at end of range.')
@utils.arg('cidr', metavar='<cidr>', help='CIDR for address range.')
def do_secgroup_add_rule(cs, args):
    """Add a rule to a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    rule = cs.security_group_rules.create(secgroup.id,
                                          args.ip_proto,
                                          args.from_port,
                                          args.to_port,
                                          args.cidr)
    _print_secgroup_rules([rule])


@utils.arg('secgroup', metavar='<secgroup>', help='ID of security group.')
@utils.arg('ip_proto', metavar='<ip_proto>', help='ip_proto (icmp, tcp, udp).')
@utils.arg('from_port', metavar='<from_port>', help='Port at start of range.')
@utils.arg('to_port', metavar='<to_port>', help='Port at end of range.')
@utils.arg('cidr', metavar='<cidr>', help='CIDR for address range.')
def do_secgroup_delete_rule(cs, args):
    """Delete a rule from a security group."""

    secgroup = _get_secgroup(cs, args.secgroup)
    for rule in secgroup.rules:
        if (rule['ip_protocol'] == args.ip_proto and
            rule['from_port'] == int(args.from_port) and
            rule['to_port'] == int(args.to_port) and
            rule['ip_range']['cidr'] == args.cidr):
            return cs.security_group_rules.delete(rule['id'])

    raise exceptions.CommandError("Rule not found")


@utils.arg('name', metavar='<name>', help='Name of security group.')
@utils.arg('description', metavar='<description>',
           help='Description of security group.')
def do_secgroup_create(cs, args):
    """Create a security group."""
    _print_secgroups([cs.security_groups.create(args.name, args.description)])


@utils.arg('secgroup', metavar='<secgroup>', help='Name of security group.')
def do_secgroup_delete(cs, args):
    """Delete a security group."""
    cs.security_groups.delete(_get_secgroup(cs, args.secgroup))


def do_secgroup_list(cs, args):
    """List security groups for the curent tenant."""
    _print_secgroups(cs.security_groups.list())


@utils.arg('secgroup', metavar='<secgroup>', help='Name of security group.')
def do_secgroup_list_rules(cs, args):
    """List rules for a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    _print_secgroup_rules(secgroup.rules)


@utils.arg('secgroup', metavar='<secgroup>', help='ID of security group.')
@utils.arg('source_group', metavar='<source_group>',
           help='ID of source group.')
@utils.arg('--ip_proto', metavar='<ip_proto>',
           help='ip_proto (icmp, tcp, udp).')
@utils.arg('--from_port', metavar='<from_port>',
           help='Port at start of range.')
@utils.arg('--to_port', metavar='<to_port>', help='Port at end of range.')
def do_secgroup_add_group_rule(cs, args):
    """Add a source group rule to a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    source_group = _get_secgroup(cs, args.source_group)
    params = {}
    params['group_id'] = source_group.id

    if args.ip_proto or args.from_port or args.to_port:
        if not (args.ip_proto and args.from_port and args.to_port):
            raise exceptions.CommandError("ip_proto, from_port, and to_port"
                                           " must be specified together")
        params['ip_protocol'] = args.ip_proto
        params['from_port'] = args.from_port
        params['to_port'] = args.to_port

    rule = cs.security_group_rules.create(secgroup.id, **params)
    _print_secgroup_rules([rule])


@utils.arg('secgroup', metavar='<secgroup>', help='ID of security group.')
@utils.arg('source_group', metavar='<source_group>',
           help='ID of source group.')
@utils.arg('--ip_proto', metavar='<ip_proto>',
           help='ip_proto (icmp, tcp, udp).')
@utils.arg('--from_port', metavar='<from_port>',
           help='Port at start of range.')
@utils.arg('--to_port', metavar='<to_port>', help='Port at end of range.')
def do_secgroup_delete_group_rule(cs, args):
    """Delete a source group rule from a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    source_group = _get_secgroup(cs, args.source_group)
    params = {}
    params['group_name'] = source_group.name

    if args.ip_proto or args.from_port or args.to_port:
        if not (args.ip_proto and args.from_port and args.to_port):
            raise exceptions.CommandError("ip_proto, from_port, and to_port"
                                           " must be specified together")
        params['ip_protocol'] = args.ip_proto
        params['from_port'] = int(args.from_port)
        params['to_port'] = int(args.to_port)

    for rule in secgroup.rules:
        if (rule.get('ip_protocol') == params.get('ip_protocol') and
            rule.get('from_port') == params.get('from_port') and
            rule.get('to_port') == params.get('to_port') and
            rule.get('group', {}).get('name') ==\
                     params.get('group_name')):
            return cs.security_group_rules.delete(rule['id'])

    raise exceptions.CommandError("Rule not found")


@utils.arg('name', metavar='<name>', help='Name of key.')
@utils.arg('--pub_key', metavar='<pub_key>', help='Path to a public ssh key.',
           default=None)
def do_keypair_add(cs, args):
    """Create a new key pair for use with instances"""
    name = args.name
    pub_key = args.pub_key

    if pub_key:
        try:
            with open(pub_key) as f:
                pub_key = f.read()
        except IOError, e:
            raise exceptions.CommandError("Can't open or read '%s': %s" % \
                                                          (pub_key, e))

    keypair = cs.keypairs.create(name, pub_key)

    if not pub_key:
        private_key = keypair.private_key
        print private_key


@utils.arg('name', metavar='<name>', help='Keypair name to delete.')
def do_keypair_delete(cs, args):
    """Delete keypair by its id"""
    name = args.name
    cs.keypairs.delete(name)


def do_keypair_list(cs, args):
    """Print a list of keypairs for a user"""
    keypairs = cs.keypairs.list()
    columns = ['Name', 'Fingerprint']
    utils.print_list(keypairs, columns)

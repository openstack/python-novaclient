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

import datetime
import getpass
import os

from novaclient import exceptions
from novaclient import utils
from novaclient.v1_1 import servers


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

    if not args.image and not args.block_device_mapping:
        raise exceptions.CommandError("you need to specify an Image ID "
                                      "or a block device mapping ")
    if not args.flavor:
        raise exceptions.CommandError("you need to specify a Flavor ID ")

    flavor = args.flavor
    image = args.image

    meta = dict(v.split('=') for v in args.meta)

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

    if args.user_data:
        try:
            userdata = open(args.user_data)
        except IOError, e:
            raise exceptions.CommandError("Can't open '%s': %s" % \
                                          (args.user_data, e))
    else:
        userdata = None

    if args.availability_zone:
        availability_zone = args.availability_zone
    else:
        availability_zone = None

    if args.security_groups:
        security_groups = args.security_groups.split(',')
    else:
        security_groups = None

    block_device_mapping = {}
    for bdm in args.block_device_mapping:
        device_name, mapping = bdm.split('=', 1)
        block_device_mapping[device_name] = mapping

    nics = []
    for nic_str in args.nics:
        nic_info = {"net-id": "", "v4-fixed-ip": ""}
        for kv_str in nic_str.split(","):
            k, v = kv_str.split("=")
            nic_info[k] = v
        nics.append(nic_info)

    hints = {}
    if args.scheduler_hints:
        hint_set = [dict({hint[0]: hint[1]}) for hint in \
                [hint_set.split('=') for hint_set in args.scheduler_hints]]
        for hint in hint_set:
            hints.update(hint.items())
    else:
        hints = {}
    boot_args = [args.name, image, flavor]

    boot_kwargs = dict(
            meta=meta,
            files=files,
            key_name=key_name,
            reservation_id=reservation_id,
            min_count=min_count,
            max_count=max_count,
            userdata=userdata,
            availability_zone=availability_zone,
            security_groups=security_groups,
            block_device_mapping=block_device_mapping,
            nics=nics,
            scheduler_hints=hints)

    return boot_args, boot_kwargs


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
@utils.arg('--block_device_mapping',
     metavar="<dev_name=mapping>",
     action='append',
     default=[],
     help="Block device mapping in the format "
         "<dev_name=<id>:<type>:<size(GB)>:<delete_on_terminate>.")
@utils.arg('--hint',
        action='append',
        dest='scheduler_hints',
        default=[],
        metavar='<key=value>',
        help="Send arbitrary key/value pairs to the scheduler for custom use.")
@utils.arg('--nic',
     metavar="<net-id=net-uuid,v4-fixed-ip=ip-addr>",
     action='append',
     dest='nics',
     default=[],
     help="Create a NIC on the server.\n"
           "Specify option multiple times to create multiple NICs.\n"
           "net-id: attach NIC to network with this UUID (optional)\n"
           "v4-fixed-ip: IPv4 fixed address for NIC (optional).")
def do_boot(cs, args):
    """Boot a new server."""
    boot_args, boot_kwargs = _boot(cs, args)

    extra_boot_kwargs = utils.get_resource_manager_extra_kwargs(do_boot, args)
    boot_kwargs.update(extra_boot_kwargs)

    server = cs.servers.create(*boot_args, **boot_kwargs)

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
    boot_args, boot_kwargs = _boot(cs,
                                   args,
                                   reservation_id=args.reservation_id,
                                   min_count=args.min_instances,
                                   max_count=args.max_instances)

    extra_boot_kwargs = utils.get_resource_manager_extra_kwargs(
            do_zone_boot, args)
    boot_kwargs.update(extra_boot_kwargs)

    reservation_id = cs.zones.boot(*boot_args, **boot_kwargs)
    print "Reservation ID=", reservation_id


def _translate_flavor_keys(collection):
    convert = [('ram', 'memory_mb'), ('disk', 'local_gb')]
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _print_flavor_list(flavors):
    _translate_flavor_keys(flavors)
    utils.print_list(flavors, [
        'ID',
        'Name',
        'Memory_MB',
        'Swap',
        'Local_GB',
        'VCPUs',
        'RXTX_Factor'])


def do_flavor_list(cs, args):
    """Print a list of available 'flavors' (sizes of servers)."""
    flavors = cs.flavors.list()
    _print_flavor_list(flavors)


@utils.arg('id',
     metavar='<id>',
     help="Unique ID of the flavor to delete")
def do_flavor_delete(cs, args):
    """Delete a specific flavor"""
    cs.flavors.delete(args.id)


@utils.arg('name',
     metavar='<name>',
     help="Name of the new flavor")
@utils.arg('id',
     metavar='<id>',
     help="Unique integer ID for the new flavor")
@utils.arg('ram',
     metavar='<ram>',
     help="Memory size in MB")
@utils.arg('disk',
     metavar='<disk>',
     help="Disk size in GB")
@utils.arg('vcpus',
     metavar='<vcpus>',
     help="Number of vcpus")
@utils.arg('--swap',
     metavar='<swap>',
     help="Swap space size in MB (default 0)",
     default=0)
@utils.arg('--rxtx-factor',
     metavar='<factor>',
     help="RX/TX factor (default 1)",
     default=1)
def do_flavor_create(cs, args):
    """Create a new flavor"""
    f = cs.flavors.create(args.name, args.ram, args.vcpus, args.disk, args.id,
                          args.swap, args.rxtx_factor)
    _print_flavor_list([f])


def do_image_list(cs, args):
    """Print a list of available images to boot from."""
    image_list = cs.images.list()

    def parse_server_name(image):
        try:
            return image.server['id']
        except (AttributeError, KeyError):
            return ''

    fmts = {'Server': parse_server_name}
    utils.print_list(image_list, ['ID', 'Name', 'Status', 'Server'], fmts)


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
    metadata = _extract_metadata(args)

    if args.action == 'set':
        cs.images.set_meta(image, metadata)
    elif args.action == 'delete':
        cs.images.delete_meta(image, metadata.keys())


def _extract_metadata(args):
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
    return metadata


def _print_image(image):
    info = image._info.copy()

    # ignore links, we don't need to present those
    info.pop('links')

    # try to replace a server entity to just an id
    server = info.pop('server', None)
    try:
        info['server'] = server['id']
    except (KeyError, TypeError):
        pass

    # break up metadata and display each on its own row
    metadata = info.pop('metadata', {})
    try:
        for key, value in metadata.items():
            _key = 'metadata %s' % key
            info[_key] = value
    except AttributeError:
        pass

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
@utils.arg('--all_tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
def do_list(cs, args):
    """List active servers."""
    recurse_zones = args.recurse_zones
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
            'all_tenants': all_tenants,
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
    formatters = {'Networks': utils._format_servers_list_networks}
    utils.print_list(cs.servers.list(search_opts=search_opts), columns,
                     formatters)


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
@utils.arg('--rebuild_password', dest='rebuild_password',
           metavar='<rebuild_password>', default=False,
           help="Set the provided password on the rebuild instance.")
def do_rebuild(cs, args):
    """Shutdown, re-image, and re-boot a server."""
    server = _find_server(cs, args.server)
    image = _find_image(cs, args.image)

    if args.rebuild_password is not False:
        _password = args.rebuild_password
    else:
        _password = None

    kwargs = utils.get_resource_manager_extra_kwargs(do_rebuild, args)
    s = server.rebuild(image, _password, **kwargs)
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
    kwargs = utils.get_resource_manager_extra_kwargs(do_resize, args)
    server.resize(flavor, **kwargs)


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
    utils.print_dict(_find_server(cs, args.server).rescue()[1])


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
    metadata = _extract_metadata(args)

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
@utils.arg('--zone_password', dest='zone_password', default=None,
                        help='New password.')
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
    if args.zone_password:
        zone_delta['password'] = args.zone_password
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
@utils.arg('--zone_password', metavar='<zone_password>',
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
                           args.zone_username, args.zone_password,
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


def _find_volume_snapshot(cs, snapshot):
    """Get a volume snapshot by ID."""
    return utils.find_resource(cs.volume_snapshots, snapshot)


def _print_volume(cs, volume):
    utils.print_dict(volume._info)


def _print_volume_snapshot(cs, snapshot):
    utils.print_dict(snapshot._info)


def _translate_volume_keys(collection):
    convert = [('displayName', 'display_name')]
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _translate_volume_snapshot_keys(collection):
    convert = [('displayName', 'display_name'), ('volumeId', 'volume_id')]
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
@utils.arg('--snapshot_id',
    metavar='<snapshot_id>',
    help='Optional snapshot id to create the volume from. (Default=None)',
    default=None)
@utils.arg('--display_name', metavar='<display_name>',
            help='Optional volume name. (Default=None)',
            default=None)
@utils.arg('--display_description', metavar='<display_description>',
            help='Optional volume description. (Default=None)',
            default=None)
def do_volume_create(cs, args):
    """Add a new volume."""
    cs.volumes.create(args.size,
                        args.snapshot_id,
                        args.display_name,
                        args.display_description)


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


def do_volume_snapshot_list(cs, args):
    """List all the snapshots."""
    snapshots = cs.volume_snapshots.list()
    _translate_volume_snapshot_keys(snapshots)
    utils.print_list(snapshots, ['ID', 'Volume ID', 'Status', 'Display Name',
                        'Size'])


@utils.arg('snapshot', metavar='<snapshot>', help='ID of the snapshot.')
def do_volume_snapshot_show(cs, args):
    """Show details about a snapshot."""
    snapshot = _find_volume_snapshot(cs, args.snapshot)
    _print_volume_snapshot(cs, snapshot)


@utils.arg('volume_id',
    metavar='<volume_id>',
    type=int,
    help='ID of the volume to snapshot')
@utils.arg('--force',
    metavar='<True|False>',
    help='Optional flag to indicate whether to snapshot a volume even if its '
        'attached to an instance. (Default=False)',
    default=False)
@utils.arg('--display_name', metavar='<display_name>',
            help='Optional snapshot name. (Default=None)',
            default=None)
@utils.arg('--display_description', metavar='<display_description>',
            help='Optional snapshot description. (Default=None)',
            default=None)
def do_volume_snapshot_create(cs, args):
    """Add a new snapshot."""
    cs.volume_snapshots.create(args.volume_id,
                        args.force,
                        args.display_name,
                        args.display_description)


@utils.arg('snapshot_id',
    metavar='<snapshot_id>',
    help='ID of the snapshot to delete.')
def do_volume_snapshot_delete(cs, args):
    """Remove a snapshot."""
    snapshot = _find_volume_snapshot(cs, args.snapshot_id)
    snapshot.delete()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('console_type',
    metavar='<console_type>',
    help='Type of vnc console ("novnc" or "xvpvnc").')
def do_get_vnc_console(cs, args):
    """Get a vnc console to a server."""
    server = _find_server(cs, args.server)
    data = server.get_vnc_console(args.console_type)

    class VNCConsole:
        def __init__(self, console_dict):
            self.type = console_dict['type']
            self.url = console_dict['url']

    utils.print_list([VNCConsole(data['console'])], ['Type', 'Url'])


def _print_floating_ip_list(floating_ips):
    utils.print_list(floating_ips, ['Ip', 'Instance Id', 'Fixed Ip', 'Pool'])


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


@utils.arg('pool',
           metavar='<floating_ip_pool>',
           help='Name of Floating IP Pool. (Optional)',
           nargs='?',
           default=None)
def do_floating_ip_create(cs, args):
    """Allocate a floating IP for the current tenant."""
    _print_floating_ip_list([cs.floating_ips.create(pool=args.pool)])


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


def do_floating_ip_pool_list(cs, args):
    """List all floating ip pools."""
    utils.print_list(cs.floating_ip_pools.list(), ['name'])


def _print_dns_list(dns_entries):
    utils.print_list(dns_entries, ['ip', 'name', 'domain'])


def _print_domain_list(domain_entries):
    utils.print_list(domain_entries, ['domain', 'scope',
                                   'project', 'availability_zone'])


def do_dns_domains(cs, args):
    """Print a list of available dns domains."""
    domains = cs.dns_domains.domains()
    _print_domain_list(domains)


@utils.arg('domain', metavar='<domain>', help='DNS domain')
@utils.arg('--ip', metavar='<ip>', help='ip address', default=None)
@utils.arg('--name', metavar='<name>', help='DNS name', default=None)
def do_dns_list(cs, args):
    """List current DNS entries for domain and ip or domain and name."""
    if not (args.ip or args.name):
        raise exceptions.CommandError(
              "You must specify either --ip or --name")
    if args.name:
        entry = cs.dns_entries.get(args.domain, args.name)
        _print_dns_list([entry])
    else:
        entries = cs.dns_entries.get_for_ip(args.domain,
                                            ip=args.ip)
        _print_dns_list(entries)


@utils.arg('ip', metavar='<ip>', help='ip address')
@utils.arg('name', metavar='<name>', help='DNS name')
@utils.arg('domain', metavar='<domain>', help='DNS domain')
@utils.arg('--type', metavar='<type>', help='dns type (e.g. "A")',
           default='A')
def do_dns_create(cs, args):
    """Create a DNS entry for domain, name and ip."""
    entries = cs.dns_entries.create(args.domain, args.name,
                                    args.ip, args.type)


@utils.arg('domain', metavar='<domain>', help='DNS domain')
@utils.arg('name', metavar='<name>', help='DNS name')
def do_dns_delete(cs, args):
    """Delete the specified DNS entry."""
    cs.dns_entries.delete(args.domain, args.name)


@utils.arg('domain', metavar='<domain>', help='DNS domain')
def do_dns_delete_domain(cs, args):
    """Delete the specified DNS domain."""
    cs.dns_domains.delete(args.domain)


@utils.arg('domain', metavar='<domain>', help='DNS domain')
@utils.arg('--availability_zone', metavar='<availability_zone>',
           help='Limit access to this domain to instances '
                'in the specified availability zone.',
           default=None)
def do_dns_create_private_domain(cs, args):
    """Create the specified DNS domain."""
    cs.dns_domains.create_private(args.domain,
                                  args.availability_zone)


@utils.arg('domain', metavar='<domain>', help='DNS domain')
@utils.arg('--project', metavar='<project>',
           help='Limit access to this domain to users '
                'of the specified project.',
           default=None)
def do_dns_create_public_domain(cs, args):
    """Create the specified DNS domain."""
    cs.dns_domains.create_public(args.domain,
                                 args.project)


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
                if v is None:
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
            rule.get('group', {}).get('name') == \
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


def do_absolute_limits(cs, args):
    """Print a list of absolute limits for a user"""
    limits = cs.limits.get().absolute
    columns = ['Name', 'Value']
    utils.print_list(limits, columns)


def do_rate_limits(cs, args):
    """Print a list of rate limits for a user"""
    limits = cs.limits.get().rate
    columns = ['Verb', 'URI', 'Value', 'Remain', 'Unit', 'Next_Available']
    utils.print_list(limits, columns)


@utils.arg('--start', metavar='<start>',
           help='Usage range start date ex 2012-01-20 (default: 4 weeks ago)',
           default=None)
@utils.arg('--end', metavar='<end>',
           help='Usage range end date, ex 2012-01-20 (default: tomorrow) ',
           default=None)
def do_usage_list(cs, args):
    """List usage data for all tenants"""
    dateformat = "%Y-%m-%d"
    rows = ["Tenant ID", "Instances", "RAM MB-Hours", "CPU Hours",
            "Disk GB-Hours"]

    if args.start:
        start = datetime.datetime.strptime(args.start, dateformat)
    else:
        start = (datetime.datetime.today() -
                 datetime.timedelta(weeks=4))

    if args.end:
        end = datetime.datetime.strptime(args.end, dateformat)
    else:
        end = (datetime.datetime.today() +
                 datetime.timedelta(days=1))

    def simplify_usage(u):
        simplerows = map(lambda x: x.lower().replace(" ", "_"), rows)

        setattr(u, simplerows[0], u.tenant_id)
        setattr(u, simplerows[1], "%d" % len(u.server_usages))
        setattr(u, simplerows[2], "%.2f" % u.total_memory_mb_usage)
        setattr(u, simplerows[3], "%.2f" % u.total_vcpus_usage)
        setattr(u, simplerows[4], "%.2f" % u.total_local_gb_usage)

    usage_list = cs.usage.list(start, end, detailed=True)

    print "Usage from %s to %s:" % (start.strftime(dateformat),
                                    end.strftime(dateformat))

    for usage in usage_list:
        simplify_usage(usage)

    utils.print_list(usage_list, rows)


@utils.arg('pk_filename',
           metavar='<private_key_file>',
           nargs='?',
           default='pk.pem',
           help='Filename to write the private key to.')
@utils.arg('cert_filename',
           metavar='<x509_cert>',
           nargs='?',
           default='cert.pem',
           help='Filename to write the x509 cert.')
def do_x509_create_cert(cs, args):
    """Create x509 cert for a user in tenant"""

    if os.path.exists(args.pk_filename):
        raise exceptions.CommandError("Unable to write privatekey - %s exists."
                        % args.pk_filename)
    if os.path.exists(args.cert_filename):
        raise exceptions.CommandError("Unable to write x509 cert - %s exists."
                        % args.cert_filename)

    certs = cs.certs.create()

    with open(args.pk_filename, 'w') as private_key:
        private_key.write(certs.private_key)
        print "Wrote private key to %s" % args.pk_filename

    with open(args.cert_filename, 'w') as cert:
        cert.write(certs.data)
        print "Wrote x509 certificate to %s" % args.cert_filename


@utils.arg('filename',
           metavar='<filename>',
           nargs='?',
           default='cacert.pem',
           help='Filename to write the x509 root cert.')
def do_x509_get_root_cert(cs, args):
    """Fetches the x509 root cert."""
    if os.path.exists(args.filename):
        raise exceptions.CommandError("Unable to write x509 root cert - \
                                      %s exists." % args.filename)

    with open(args.filename, 'w') as cert:
        cacert = cs.certs.get()
        cert.write(cacert.data)
        print "Wrote x509 root cert to %s" % args.filename


def do_aggregate_list(cs, args):
    """Print a list of all aggregates."""
    aggregates = cs.aggregates.list()
    columns = ['Id', 'Name', 'Availability Zone', 'Operational State']
    utils.print_list(aggregates, columns)


@utils.arg('name', metavar='<name>', help='Name of aggregate.')
@utils.arg('availability_zone', metavar='<availability_zone>',
           help='The availablity zone of the aggregate.')
def do_aggregate_create(cs, args):
    """Create a new aggregate with the specified details."""
    aggregate = cs.aggregates.create(args.name, args.availability_zone)
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Aggregate id to delete.')
def do_aggregate_delete(cs, args):
    """Delete the aggregate by its id."""
    cs.aggregates.delete(args.id)
    print "Aggregate %s has been succesfully deleted." % args.id


@utils.arg('id', metavar='<id>', help='Aggregate id to udpate.')
@utils.arg('name', metavar='<name>', help='Name of aggregate.')
@utils.arg('availability_zone', metavar='<availability_zone>',
           help='The availablity zone of the aggregate.', nargs='?')
def do_aggregate_update(cs, args):
    """Update the aggregate's name and optionally availablity zone."""
    updates = {"name": args.name}
    if args.availability_zone:
        updates["availability_zone"] = args.availability_zone

    aggregate = cs.aggregates.update(args.id, updates)
    print "Aggregate %s has been succesfully updated." % args.id
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Aggregate id to udpate.')
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           action='append',
           default=[],
           help='Metadata to add/update to aggregate')
def do_aggregate_set_metadata(cs, args):
    """Update the metadata associated with the aggregate."""
    metadata = _extract_metadata(args)
    aggregate = cs.aggregates.set_metadata(args.id, metadata)
    print "Aggregate %s has been succesfully updated." % args.id
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Host aggregate id to delete.')
@utils.arg('host', metavar='<host>', help='The host to add to the aggregate.')
def do_aggregate_add_host(cs, args):
    """Add the host to the specified aggregate."""
    aggregate = cs.aggregates.add_host(args.id, args.host)
    print "Aggregate %s has been succesfully updated." % args.id
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Host aggregate id to delete.')
@utils.arg('host', metavar='<host>', help='The host to add to the aggregate.')
def do_aggregate_remove_host(cs, args):
    """Remove the specified host from the specfied aggregate."""
    aggregate = cs.aggregates.remove_host(args.id, args.host)
    print "Aggregate %s has been succesfully updated." % args.id
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Host aggregate id to delete.')
def do_aggregate_details(cs, args):
    """Show details of the specified aggregate."""
    _print_aggregate_details(cs.aggregates.get_details(args.id))


def _print_aggregate_details(aggregate):
    columns = ['Id', 'Name', 'Availability Zone', 'Operational State',
               'Hosts', 'Metadata']
    utils.print_list([aggregate], columns)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('host', metavar='<host>', help='destination host name.')
@utils.arg('--block_migrate', action='store_true', dest='block_migrate',
           default=False,
           help='True in case of block_migration.\
                (Default=False:live_migration)')
@utils.arg('--disk_over_commit', action='store_true', dest='disk_over_commit',
           default=False,
           help='Allow overcommit.(Default=Flase)')
def do_live_migration(cs, args):
    """Migrates a running instance to a new machine."""
    _find_server(cs, args.server).live_migrate(args.host,
                                               args.block_migrate,
                                               args.disk_over_commit)


@utils.arg('host', metavar='<hostname>', help='Name of host.')
def do_describe_resource(cs, args):
    """Show details about a resource"""
    result = cs.hosts.get(args.host)
    columns = ["HOST", "PROJECT", "cpu", "memory_mb", "disk_gb"]
    utils.print_list(result, columns)

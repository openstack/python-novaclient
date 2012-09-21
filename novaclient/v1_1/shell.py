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

import argparse
import datetime
import getpass
import locale
import os
import sys
import time

from novaclient import exceptions
from novaclient.openstack.common import timeutils
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

    flavor = _find_flavor(cs, args.flavor)
    image = _find_image(cs, args.image)

    meta = dict(v.split('=', 1) for v in args.meta)

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
        nic_info = {"net-id": "", "v4-fixed-ip": "", "port-id": ""}
        for kv_str in nic_str.split(","):
            k, v = kv_str.split("=", 1)
            nic_info[k] = v
        nics.append(nic_info)

    hints = {}
    if args.scheduler_hints:
        for hint in args.scheduler_hints:
            key, _sep, value = hint.partition('=')
            # NOTE(vish): multiple copies of the same hint will
            #             result in a list of values
            if key in hints:
                if isinstance(hints[key], basestring):
                    hints[key] = [hints[key]]
                hints[key] += [value]
            else:
                hints[key] = value
    boot_args = [args.name, image, flavor]

    if str(args.config_drive).lower() in ("true", "1"):
        config_drive = True
    elif str(args.config_drive).lower() in ("false", "0", "", "none"):
        config_drive = None
    else:
        config_drive = args.config_drive

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
            scheduler_hints=hints,
            config_drive=config_drive)

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
     help="Record arbitrary key/value metadata to /meta.js "\
          "on the new server. Can be specified multiple times.")
@utils.arg('--file',
     metavar="<dst-path=src-path>",
     action='append',
     dest='files',
     default=[],
     help="Store arbitrary files from <src-path> locally to <dst-path> "\
          "on the new server. You may store up to 5 files.")
@utils.arg('--key-name',
    metavar='<key-name>',
    help="Key name of keypair that should be created earlier with \
        the command keypair-add")
@utils.arg('--key_name',
    help=argparse.SUPPRESS)
@utils.arg('name', metavar='<name>', help='Name for the new server')
@utils.arg('--user-data',
    default=None,
    metavar='<user-data>',
    help="user data file to pass to be exposed by the metadata server.")
@utils.arg('--user_data',
    help=argparse.SUPPRESS)
@utils.arg('--availability-zone',
    default=None,
    metavar='<availability-zone>',
    help="The availability zone for instance placement.")
@utils.arg('--availability_zone',
    help=argparse.SUPPRESS)
@utils.arg('--security-groups',
    default=None,
    metavar='<security-groups>',
    help="Comma separated list of security group names.")
@utils.arg('--security_groups',
    help=argparse.SUPPRESS)
@utils.arg('--block-device-mapping',
    metavar="<dev-name=mapping>",
    action='append',
    default=[],
    help="Block device mapping in the format "
        "<dev-name>=<id>:<type>:<size(GB)>:<delete-on-terminate>.")
@utils.arg('--block_device_mapping',
    action='append',
    help=argparse.SUPPRESS)
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
           "v4-fixed-ip: IPv4 fixed address for NIC (optional).\n"
           "port-id: attach NIC to port with this UUID (optional)")
@utils.arg('--config-drive',
     metavar="<value>",
     dest='config_drive',
     default=False,
     help="Enable config drive")
@utils.arg('--poll',
    dest='poll',
    action="store_true",
    default=False,
    help='Blocks while instance builds so progress can be reported.')
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

    if args.poll:
        _poll_for_status(cs.servers.get, info['id'], 'building', ['active'])


def do_cloudpipe_list(cs, _args):
    """Print a list of all cloudpipe instances."""
    cloudpipes = cs.cloudpipe.list()
    columns = ['Project Id', "Public IP", "Public Port", "Internal IP"]
    utils.print_list(cloudpipes, columns)


@utils.arg('project', metavar='<project>', help='Name of the project.')
def do_cloudpipe_create(cs, args):
    """Create a cloudpipe instance for the given project"""
    cs.cloudpipe.create(args.project)


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True,
                     status_field="status", silent=False):
    """Block while an action is being performed, periodically printing
    progress.
    """
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    if not silent:
        print

    while True:
        obj = poll_fn(obj_id)

        status = getattr(obj, status_field)

        if status:
            status = status.lower()

        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            if not silent:
                print_progress(100)
                print "\nFinished"
            break
        elif status == "error":
            if not silent:
                print "\nError %(action)s instance" % locals()
            break

        if not silent:
            print_progress(progress)

        time.sleep(poll_period)


def _translate_flavor_keys(collection):
    convert = [('ram', 'memory_mb')]
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _print_flavor_extra_specs(flavor):
    try:
        return flavor.get_keys()
    except exceptions.NotFound:
        return "N/A"


def _print_flavor_list(cs, flavors):
    _translate_flavor_keys(flavors)
    formatters = {'extra_specs': _print_flavor_extra_specs}
    utils.print_list(flavors, [
        'ID',
        'Name',
        'Memory_MB',
        'Disk',
        'Ephemeral',
        'Swap',
        'VCPUs',
        'RXTX_Factor',
        'Is_Public',
        'extra_specs'], formatters)


def do_flavor_list(cs, _args):
    """Print a list of available 'flavors' (sizes of servers)."""
    flavors = cs.flavors.list()
    for flavor in flavors:
        # int needed for numerical sort
        flavor.id = int(flavor.id)
    _print_flavor_list(cs, flavors)


@utils.arg('id',
     metavar='<id>',
     help="Unique ID of the flavor to delete")
def do_flavor_delete(cs, args):
    """Delete a specific flavor"""
    cs.flavors.delete(args.id)


@utils.arg('flavor',
     metavar='<flavor>',
     help="Name or ID of flavor")
def do_flavor_show(cs, args):
    """Show details about the given flavor."""
    flavor = _find_flavor(cs, args.flavor)
    _print_flavor(cs, flavor)


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
@utils.arg('--ephemeral',
     metavar='<ephemeral>',
     help="Ephemeral space size in GB (default 0)",
     default=0)
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
@utils.arg('--is-public',
     metavar='<is-public>',
     help="Make flavor accessible to the public (default true)",
     type=utils.bool_from_str,
     default=True)
def do_flavor_create(cs, args):
    """Create a new flavor"""
    f = cs.flavors.create(args.name, args.ram, args.vcpus, args.disk, args.id,
                          args.ephemeral, args.swap, args.rxtx_factor,
                          args.is_public)
    _print_flavor_list(cs, [f])


@utils.arg('flavor',
    metavar='<flavor>',
    help="Name or ID of flavor")
@utils.arg('action',
    metavar='<action>',
    choices=['set', 'unset'],
    help="Actions: 'set' or 'unset'")
@utils.arg('metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help='Extra_specs to set/unset (only key is necessary on unset)')
def do_flavor_key(cs, args):
    """Set or unset extra_spec for a flavor."""
    flavor = _find_flavor(cs, args.flavor)
    keypair = _extract_metadata(args)

    if args.action == 'set':
        flavor.set_keys(keypair)
    elif args.action == 'unset':
        flavor.unset_keys(keypair.keys())


@utils.arg('--flavor',
     metavar='<flavor>',
     help="Filter results by flavor name or ID.")
@utils.arg('--tenant', metavar='<tenant_id>',
           help='Filter results by tenant ID.')
def do_flavor_access_list(cs, args):
    """Print access information about the given flavor."""
    if args.flavor and args.tenant:
        raise exceptions.CommandError("Unable to filter results by "
                                      "both --flavor and --tenant.")
    elif args.flavor:
        flavor = _find_flavor(cs, args.flavor)
        if flavor.is_public:
            raise exceptions.CommandError("Failed to get access list "
                                          "for public flavor type.")
        kwargs = {'flavor': flavor}
    elif args.tenant:
        kwargs = {'tenant': args.tenant}
    else:
        raise exceptions.CommandError("Unable to get all access lists. "
                                      "Specify --flavor or --tenant")

    try:
        access_list = cs.flavor_access.list(**kwargs)
    except NotImplementedError, e:
        raise exceptions.CommandError("%s" % str(e))

    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


@utils.arg('flavor',
     metavar='<flavor>',
     help="Filter results by flavor name or ID.")
@utils.arg('tenant', metavar='<tenant_id>',
           help='Filter results by tenant ID.')
def do_flavor_access_add(cs, args):
    """Add flavor access for the given tenant."""
    flavor = _find_flavor(cs, args.flavor)
    access_list = cs.flavor_access.add_tenant_access(flavor, args.tenant)
    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


@utils.arg('flavor',
     metavar='<flavor>',
     help="Filter results by flavor name or ID.")
@utils.arg('tenant', metavar='<tenant_id>',
           help='Filter results by tenant ID.')
def do_flavor_access_remove(cs, args):
    """Remove flavor access for the given tenant."""
    flavor = _find_flavor(cs, args.flavor)
    access_list = cs.flavor_access.remove_tenant_access(flavor, args.tenant)
    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


def do_network_list(cs, _args):
    """Print a list of available networks."""
    network_list = cs.networks.list()
    columns = ['ID', 'Label', 'Cidr']
    utils.print_list(network_list, columns)


@utils.arg('network',
     metavar='<network>',
     help="uuid or label of network")
def do_network_show(cs, args):
    """Show details about the given network."""
    network = utils.find_resource(cs.networks, args.network)
    utils.print_dict(network._info)


def do_image_list(cs, _args):
    """Print a list of available images to boot from."""
    image_list = cs.images.list()

    def parse_server_name(image):
        try:
            return image.server['id']
        except (AttributeError, KeyError):
            return ''

    fmts = {'Server': parse_server_name}
    utils.print_list(image_list, ['ID', 'Name', 'Status', 'Server'],
                     fmts, sortby_index=1)


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


def _print_flavor(cs, flavor):
    info = flavor._info.copy()
    # ignore links, we don't need to present those
    info.pop('links')
    info.update({"extra_specs": _print_flavor_extra_specs(flavor)})
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


@utils.arg('--reservation-id',
    dest='reservation_id',
    metavar='<reservation-id>',
    default=None,
    help='Only return instances that match reservation-id.')
@utils.arg('--reservation_id',
    help=argparse.SUPPRESS)
@utils.arg('--ip',
    dest='ip',
    metavar='<ip-regexp>',
    default=None,
    help='Search with regular expression match by IP address')
@utils.arg('--ip6',
    dest='ip6',
    metavar='<ip6-regexp>',
    default=None,
    help='Search with regular expression match by IPv6 address')
@utils.arg('--name',
    dest='name',
    metavar='<name-regexp>',
    default=None,
    help='Search with regular expression match by name')
@utils.arg('--instance-name',
    dest='instance_name',
    metavar='<name-regexp>',
    default=None,
    help='Search with regular expression match by instance name')
@utils.arg('--instance_name',
    help=argparse.SUPPRESS)
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
@utils.arg('--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@utils.arg('--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
def do_list(cs, args):
    """List active servers."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
            'all_tenants': all_tenants,
            'reservation_id': args.reservation_id,
            'ip': args.ip,
            'ip6': args.ip6,
            'name': args.name,
            'image': args.image,
            'flavor': args.flavor,
            'status': args.status,
            'host': args.host,
            'instance_name': args.instance_name}

    id_col = 'ID'

    columns = [id_col, 'Name', 'Status', 'Networks']
    formatters = {'Networks': utils._format_servers_list_networks}
    utils.print_list(cs.servers.list(search_opts=search_opts), columns,
                     formatters, sortby_index=1)


@utils.arg('--hard',
    dest='reboot_type',
    action='store_const',
    const=servers.REBOOT_HARD,
    default=servers.REBOOT_SOFT,
    help='Perform a hard reboot (instead of a soft one).')
@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('--poll',
    dest='poll',
    action="store_true",
    default=False,
    help='Blocks while instance is rebooting.')
def do_reboot(cs, args):
    """Reboot a server."""
    server = _find_server(cs, args.server)
    server.reboot(args.reboot_type)

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'rebooting', ['active'],
                         show_progress=False)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('image', metavar='<image>', help="Name or ID of new image.")
@utils.arg('--rebuild-password',
    dest='rebuild_password',
    metavar='<rebuild-password>',
    default=False,
    help="Set the provided password on the rebuild instance.")
@utils.arg('--rebuild_password',
    help=argparse.SUPPRESS)
@utils.arg('--poll',
    dest='poll',
    action="store_true",
    default=False,
    help='Blocks while instance rebuilds so progress can be reported.')
@utils.arg('--minimal',
    dest='minimal',
    action="store_true",
    default=False,
    help='Skips flavor/image lookups when showing instances')
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
    _print_server(cs, args)

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'rebuilding', ['active'])


@utils.arg('server', metavar='<server>',
           help='Name (old name) or ID of server.')
@utils.arg('name', metavar='<name>', help='New name for the server.')
def do_rename(cs, args):
    """Rename a server."""
    _find_server(cs, args.server).update(name=args.name)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('flavor', metavar='<flavor>', help="Name or ID of new flavor.")
@utils.arg('--poll',
    dest='poll',
    action="store_true",
    default=False,
    help='Blocks while instance resizes so progress can be reported.')
def do_resize(cs, args):
    """Resize a server."""
    server = _find_server(cs, args.server)
    flavor = _find_flavor(cs, args.flavor)
    kwargs = utils.get_resource_manager_extra_kwargs(do_resize, args)
    server.resize(flavor, **kwargs)
    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'resizing',
                         ['active', 'verify_resize'])


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_resize_confirm(cs, args):
    """Confirm a previous resize."""
    _find_server(cs, args.server).confirm_resize()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_resize_revert(cs, args):
    """Revert a previous resize (and return to the previous VM)."""
    _find_server(cs, args.server).revert_resize()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('--poll',
    dest='poll',
    action="store_true",
    default=False,
    help='Blocks while instance migrates so progress can be reported.')
def do_migrate(cs, args):
    """Migrate a server."""
    server = _find_server(cs, args.server)
    server.migrate()

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'migrating',
                         ['active', 'verify_resize'])


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_pause(cs, args):
    """Pause a server."""
    _find_server(cs, args.server).pause()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_unpause(cs, args):
    """Unpause a server."""
    _find_server(cs, args.server).unpause()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_stop(cs, args):
    """Stop a server."""
    _find_server(cs, args.server).stop()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_start(cs, args):
    """Start a server."""
    _find_server(cs, args.server).start()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_lock(cs, args):
    """Lock a server."""
    _find_server(cs, args.server).lock()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_unlock(cs, args):
    """Unlock a server."""
    _find_server(cs, args.server).unlock()


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
    server = _find_server(cs, args.server)
    utils.print_dict(cs.servers.diagnostics(server)[1])


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_actions(cs, args):
    """Retrieve server actions."""
    server = _find_server(cs, args.server)
    utils.print_list(
        cs.servers.actions(server),
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
@utils.arg('--poll',
    dest='poll',
    action="store_true",
    default=False,
    help='Blocks while instance snapshots so progress can be reported.')
def do_image_create(cs, args):
    """Create a new image by taking a snapshot of a running server."""
    server = _find_server(cs, args.server)
    image_uuid = cs.servers.create_image(server, args.name)

    if args.poll:
        _poll_for_status(cs.images.get, image_uuid, 'snapshotting',
                         ['active'])

        # NOTE(sirp):  A race-condition exists between when the image finishes
        # uploading and when the servers's `task_state` is cleared. To account
        # for this, we need to poll a second time to ensure the `task_state` is
        # cleared before returning, ensuring that a snapshot taken immediately
        # after this function returns will succeed.
        #
        # A better long-term solution will be to separate 'snapshotting' and
        # 'image-uploading' in Nova and clear the task-state once the VM
        # snapshot is complete but before the upload begins.
        task_state_field = "OS-EXT-STS:task_state"
        if hasattr(server, task_state_field):
            _poll_for_status(cs.servers.get, server.id, 'image_snapshot',
                             [None], status_field=task_state_field,
                             show_progress=False, silent=True)


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


def _print_server(cs, args):
    # By default when searching via name we will do a
    # findall(name=blah) and due a REST /details which is not the same
    # as a .get() and doesn't get the information about flavors and
    # images. This fix it as we redo the call with the id which does a
    # .get() to get all informations.
    server = _find_server(cs, args.server)

    networks = server.networks
    info = server._info.copy()
    for network_label, address_list in networks.items():
        info['%s network' % network_label] = ', '.join(address_list)

    flavor = info.get('flavor', {})
    flavor_id = flavor.get('id', '')
    if args.minimal:
        info['flavor'] = flavor_id
    else:
        info['flavor'] = '%s (%s)' % (_find_flavor(cs, flavor_id).name,
                                      flavor_id)

    image = info.get('image', {})
    image_id = image.get('id', '')
    if args.minimal:
        info['image'] = image_id
    else:
        try:
            info['image'] = '%s (%s)' % (_find_image(cs, image_id).name,
                                         image_id)
        except Exception:
            info['image'] = '%s (%s)' % ("Image not found", image_id)

    info.pop('links', None)
    info.pop('addresses', None)

    utils.print_dict(info)


@utils.arg('--minimal',
    dest='minimal',
    action="store_true",
    default=False,
    help='Skips flavor/image lookups when showing instances')
@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_show(cs, args):
    """Show details about the given server."""
    _print_server(cs, args)


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


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('network_id',
    metavar='<network-id>',
    help='Network ID.')
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


def _print_volume(volume):
    utils.print_dict(volume._info)


def _print_volume_snapshot(snapshot):
    utils.print_dict(snapshot._info)


def _translate_volume_keys(collection):
    convert = [('displayName', 'display_name'), ('volumeType', 'volume_type')]
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


@utils.service_type('volume')
def do_volume_list(cs, _args):
    """List all the volumes."""
    volumes = cs.volumes.list()
    _translate_volume_keys(volumes)

    # Create a list of servers to which the volume is attached
    for vol in volumes:
        servers = [s.get('server_id') for s in vol.attachments]
        setattr(vol, 'attached_to', ','.join(map(str, servers)))
    utils.print_list(volumes, ['ID', 'Status', 'Display Name',
                        'Size', 'Volume Type', 'Attached to'])


@utils.arg('volume', metavar='<volume>', help='ID of the volume.')
@utils.service_type('volume')
def do_volume_show(cs, args):
    """Show details about a volume."""
    volume = _find_volume(cs, args.volume)
    _print_volume(volume)


@utils.arg('size',
    metavar='<size>',
    type=int,
    help='Size of volume in GB')
@utils.arg('--snapshot-id',
    metavar='<snapshot-id>',
    default=None,
    help='Optional snapshot id to create the volume from. (Default=None)')
@utils.arg('--snapshot_id',
    help=argparse.SUPPRESS)
@utils.arg('--image-id',
    metavar='<image-id>',
    help='Optional image id to create the volume from. (Default=None)',
    default=None)
@utils.arg('--display-name',
    metavar='<display-name>',
    default=None,
    help='Optional volume name. (Default=None)')
@utils.arg('--display_name',
    help=argparse.SUPPRESS)
@utils.arg('--display-description',
    metavar='<display-description>',
    default=None,
    help='Optional volume description. (Default=None)')
@utils.arg('--display_description',
    help=argparse.SUPPRESS)
@utils.arg('--volume-type',
    metavar='<volume-type>',
    default=None,
    help='Optional volume type. (Default=None)')
@utils.arg('--volume_type',
    help=argparse.SUPPRESS)
@utils.arg('--availability-zone', metavar='<availability-zone>',
    help='Optional Availability Zone for volume. (Default=None)',
    default=None)
@utils.service_type('volume')
def do_volume_create(cs, args):
    """Add a new volume."""
    volume = cs.volumes.create(args.size,
                               args.snapshot_id,
                               args.display_name,
                               args.display_description,
                               args.volume_type,
                               args.availability_zone,
                               imageRef=args.image_id)
    _print_volume(volume)


@utils.arg('volume', metavar='<volume>', help='ID of the volume to delete.')
@utils.service_type('volume')
def do_volume_delete(cs, args):
    """Remove a volume."""
    volume = _find_volume(cs, args.volume)
    volume.delete()


@utils.arg('server',
    metavar='<server>',
    help='Name or ID of server.')
@utils.arg('volume',
    metavar='<volume>',
    help='ID of the volume to attach.')
@utils.arg('device', metavar='<device>',
    help='Name of the device e.g. /dev/vdb. '
         'Use "auto" for autoassign (if supported)')
def do_volume_attach(cs, args):
    """Attach a volume to a server."""
    if args.device == 'auto':
        args.device = None

    volume = cs.volumes.create_server_volume(_find_server(cs, args.server).id,
                                             args.volume,
                                             args.device)
    _print_volume(volume)


@utils.arg('server',
    metavar='<server>',
    help='Name or ID of server.')
@utils.arg('attachment_id',
    metavar='<volume>',
    help='Attachment ID of the volume.')
def do_volume_detach(cs, args):
    """Detach a volume from a server."""
    cs.volumes.delete_server_volume(_find_server(cs, args.server).id,
                                        args.attachment_id)


@utils.service_type('volume')
def do_volume_snapshot_list(cs, _args):
    """List all the snapshots."""
    snapshots = cs.volume_snapshots.list()
    _translate_volume_snapshot_keys(snapshots)
    utils.print_list(snapshots, ['ID', 'Volume ID', 'Status', 'Display Name',
                        'Size'])


@utils.arg('snapshot', metavar='<snapshot>', help='ID of the snapshot.')
@utils.service_type('volume')
def do_volume_snapshot_show(cs, args):
    """Show details about a snapshot."""
    snapshot = _find_volume_snapshot(cs, args.snapshot)
    _print_volume_snapshot(snapshot)


@utils.arg('volume_id',
    metavar='<volume-id>',
    help='ID of the volume to snapshot')
@utils.arg('--force',
    metavar='<True|False>',
    help='Optional flag to indicate whether to snapshot a volume even if its '
        'attached to an instance. (Default=False)',
    default=False)
@utils.arg('--display-name',
    metavar='<display-name>',
    default=None,
    help='Optional snapshot name. (Default=None)')
@utils.arg('--display_name',
    help=argparse.SUPPRESS)
@utils.arg('--display-description',
    metavar='<display-description>',
    default=None,
    help='Optional snapshot description. (Default=None)')
@utils.arg('--display_description',
    help=argparse.SUPPRESS)
@utils.service_type('volume')
def do_volume_snapshot_create(cs, args):
    """Add a new snapshot."""
    snapshot = cs.volume_snapshots.create(args.volume_id,
                                          args.force,
                                          args.display_name,
                                          args.display_description)
    _print_volume_snapshot(snapshot)


@utils.arg('snapshot_id',
    metavar='<snapshot-id>',
    help='ID of the snapshot to delete.')
@utils.service_type('volume')
def do_volume_snapshot_delete(cs, args):
    """Remove a snapshot."""
    snapshot = _find_volume_snapshot(cs, args.snapshot_id)
    snapshot.delete()


def _print_volume_type_list(vtypes):
    utils.print_list(vtypes, ['ID', 'Name'])


@utils.service_type('volume')
def do_volume_type_list(cs, args):
    """Print a list of available 'volume types'."""
    vtypes = cs.volume_types.list()
    _print_volume_type_list(vtypes)


@utils.arg('name',
     metavar='<name>',
     help="Name of the new flavor")
@utils.service_type('volume')
def do_volume_type_create(cs, args):
    """Create a new volume type."""
    vtype = cs.volume_types.create(args.name)
    _print_volume_type_list([vtype])


@utils.arg('id',
     metavar='<id>',
     help="Unique ID of the volume type to delete")
@utils.service_type('volume')
def do_volume_type_delete(cs, args):
    """Delete a specific flavor"""
    cs.volume_types.delete(args.id)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('console_type',
    metavar='<console-type>',
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
@utils.arg('--length',
           metavar='<length>',
           default=None,
           help='Length in lines to tail.')
def do_console_log(cs, args):
    """Get console log output of a server."""
    server = _find_server(cs, args.server)
    data = server.get_console_output(length=args.length)
    print data


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


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('secgroup', metavar='<secgroup>', help='Name of Security Group.')
def do_add_secgroup(cs, args):
    """Add a Security Group to a server."""
    server = _find_server(cs, args.server)
    server.add_security_group(args.secgroup)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('secgroup', metavar='<secgroup>', help='Name of Security Group.')
def do_remove_secgroup(cs, args):
    """Remove a Security Group from a server."""
    server = _find_server(cs, args.server)
    server.remove_security_group(args.secgroup)


@utils.arg('pool',
           metavar='<floating-ip-pool>',
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
    raise exceptions.CommandError("Floating ip %s not found." % args.address)


def do_floating_ip_list(cs, _args):
    """List floating ips for this tenant."""
    _print_floating_ip_list(cs.floating_ips.list())


def do_floating_ip_pool_list(cs, _args):
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
@utils.arg('--type', metavar='<type>', help='dns type (e.g. "A")', default='A')
def do_dns_create(cs, args):
    """Create a DNS entry for domain, name and ip."""
    cs.dns_entries.create(args.domain, args.name, args.ip, args.type)


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
@utils.arg('--availability-zone',
    metavar='<availability-zone>',
    default=None,
    help='Limit access to this domain to instances '
        'in the specified availability zone.')
@utils.arg('--availability_zone',
    help=argparse.SUPPRESS)
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
        encoding = (locale.getpreferredencoding() or
            sys.stdin.encoding or
            'UTF-8')
        s.name = s.name.encode(encoding)
        if secgroup == s.name:
            return s
    raise exceptions.CommandError("Secgroup %s not found" % secgroup)


@utils.arg('secgroup', metavar='<secgroup>', help='ID of security group.')
@utils.arg('ip_proto',
    metavar='<ip-proto>',
    help='IP protocol (icmp, tcp, udp).')
@utils.arg('from_port',
    metavar='<from-port>',
    help='Port at start of range.')
@utils.arg('to_port',
    metavar='<to-port>',
    help='Port at end of range.')
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
@utils.arg('ip_proto',
    metavar='<ip-proto>',
    help='IP protocol (icmp, tcp, udp).')
@utils.arg('from_port',
    metavar='<from-port>',
    help='Port at start of range.')
@utils.arg('to_port',
    metavar='<to-port>',
    help='Port at end of range.')
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


@utils.arg('--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@utils.arg('--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
def do_secgroup_list(cs, args):
    """List security groups for the current tenant."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {'all_tenants': all_tenants}
    _print_secgroups(cs.security_groups.list(search_opts=search_opts))


@utils.arg('secgroup', metavar='<secgroup>', help='Name of security group.')
def do_secgroup_list_rules(cs, args):
    """List rules for a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    _print_secgroup_rules(secgroup.rules)


@utils.arg('secgroup', metavar='<secgroup>', help='ID of security group.')
@utils.arg('source_group',
    metavar='<source-group>',
    help='ID of source group.')
@utils.arg('ip_proto',
    metavar='<ip-proto>',
    help='IP protocol (icmp, tcp, udp).')
@utils.arg('from_port',
    metavar='<from-port>',
    help='Port at start of range.')
@utils.arg('to_port',
    metavar='<to-port>',
    help='Port at end of range.')
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
@utils.arg('source_group',
    metavar='<source-group>',
    help='ID of source group.')
@utils.arg('ip_proto',
    metavar='<ip-proto>',
    help='IP protocol (icmp, tcp, udp).')
@utils.arg('from_port',
    metavar='<from-port>',
    help='Port at start of range.')
@utils.arg('to_port',
    metavar='<to-port>',
    help='Port at end of range.')
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
@utils.arg('--pub-key',
    metavar='<pub-key>',
    default=None,
    help='Path to a public ssh key.')
@utils.arg('--pub_key',
    help=argparse.SUPPRESS)
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

    now = timeutils.utcnow()

    if args.start:
        start = datetime.datetime.strptime(args.start, dateformat)
    else:
        start = now - datetime.timedelta(weeks=4)

    if args.end:
        end = datetime.datetime.strptime(args.end, dateformat)
    else:
        end = now + datetime.timedelta(days=1)

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
    metavar='<private-key-filename>',
    nargs='?',
    default='pk.pem',
    help='Filename for the private key [Default: pk.pem]')
@utils.arg('cert_filename',
    metavar='<x509-cert-filename>',
    nargs='?',
    default='cert.pem',
    help='Filename for the X.509 certificate [Default: cert.pem]')
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
    columns = ['Id', 'Name', 'Availability Zone']
    utils.print_list(aggregates, columns)


@utils.arg('name', metavar='<name>', help='Name of aggregate.')
@utils.arg('availability_zone',
    metavar='<availability-zone>',
    help='The availability zone of the aggregate.')
def do_aggregate_create(cs, args):
    """Create a new aggregate with the specified details."""
    aggregate = cs.aggregates.create(args.name, args.availability_zone)
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Aggregate id to delete.')
def do_aggregate_delete(cs, args):
    """Delete the aggregate by its id."""
    cs.aggregates.delete(args.id)
    print "Aggregate %s has been successfully deleted." % args.id


@utils.arg('id', metavar='<id>', help='Aggregate id to update.')
@utils.arg('name', metavar='<name>', help='Name of aggregate.')
@utils.arg('availability_zone',
    metavar='<availability-zone>',
    nargs='?',
    default=None,
    help='The availability zone of the aggregate.')
def do_aggregate_update(cs, args):
    """Update the aggregate's name and optionally availability zone."""
    updates = {"name": args.name}
    if args.availability_zone:
        updates["availability_zone"] = args.availability_zone

    aggregate = cs.aggregates.update(args.id, updates)
    print "Aggregate %s has been successfully updated." % args.id
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Aggregate id to update.')
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
    print "Aggregate %s has been successfully updated." % args.id
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Host aggregate id to delete.')
@utils.arg('host', metavar='<host>', help='The host to add to the aggregate.')
def do_aggregate_add_host(cs, args):
    """Add the host to the specified aggregate."""
    aggregate = cs.aggregates.add_host(args.id, args.host)
    print "Aggregate %s has been successfully updated." % args.id
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Host aggregate id to delete.')
@utils.arg('host', metavar='<host>', help='The host to add to the aggregate.')
def do_aggregate_remove_host(cs, args):
    """Remove the specified host from the specified aggregate."""
    aggregate = cs.aggregates.remove_host(args.id, args.host)
    print "Aggregate %s has been successfully updated." % args.id
    _print_aggregate_details(aggregate)


@utils.arg('id', metavar='<id>', help='Host aggregate id to delete.')
def do_aggregate_details(cs, args):
    """Show details of the specified aggregate."""
    _print_aggregate_details(cs.aggregates.get_details(args.id))


def _print_aggregate_details(aggregate):
    columns = ['Id', 'Name', 'Availability Zone', 'Hosts', 'Metadata']
    utils.print_list([aggregate], columns)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('host', metavar='<host>', help='destination host name.')
@utils.arg('--block-migrate',
    action='store_true',
    dest='block_migrate',
    default=False,
    help='True in case of block_migration.\
        (Default=False:live_migration)')
@utils.arg('--block_migrate',
    action='store_true',
    help=argparse.SUPPRESS)
@utils.arg('--disk-over-commit',
    action='store_true',
    dest='disk_over_commit',
    default=False,
    help='Allow overcommit.(Default=Flase)')
@utils.arg('--disk_over_commit',
    action='store_true',
    help=argparse.SUPPRESS)
def do_live_migration(cs, args):
    """Migrates a running instance to a new machine."""
    _find_server(cs, args.server).live_migrate(args.host,
                                               args.block_migrate,
                                               args.disk_over_commit)


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('--active', action='store_const', dest='state',
           default='error', const='active',
           help='Request the instance be reset to "active" state instead '
           'of "error" state (the default).')
def do_reset_state(cs, args):
    """Reset the state of an instance"""
    _find_server(cs, args.server).reset_state(args.state)


@utils.arg('host', metavar='<hostname>', help='Name of host.')
def do_host_describe(cs, args):
    """Describe a specific host"""
    result = cs.hosts.get(args.host)
    columns = ["HOST", "PROJECT", "cpu", "memory_mb", "disk_gb"]
    utils.print_list(result, columns)


def do_host_list(cs, args):
    """List all hosts by service"""
    columns = ["host_name", "service"]
    result = cs.hosts.list_all()
    utils.print_list(result, columns)


@utils.arg('host', metavar='<hostname>', help='Name of host.')
@utils.arg('--status', metavar='<status>', default=None, dest='status',
           help='Either enable or disable a host.')
@utils.arg('--maintenance',
    metavar='<maintenance-mode>',
    default=None,
    dest='maintenance',
    help='Either put or resume host to/from maintenance.')
def do_host_update(cs, args):
    """Update host settings."""
    updates = {}
    columns = ["HOST"]
    if args.status:
        updates['status'] = args.status
        columns.append("status")
    if args.maintenance:
        updates['maintenance_mode'] = args.maintenance
        columns.append("maintenance_mode")
    result = cs.hosts.update(args.host, updates)
    utils.print_list([result], columns)


@utils.arg('host', metavar='<hostname>', help='Name of host.')
@utils.arg('--action', metavar='<action>', dest='action',
           choices=['startup', 'shutdown', 'reboot'],
           help='A power action: startup, reboot, or shutdown.')
def do_host_action(cs, args):
    """Perform a power action on a host."""
    result = cs.hosts.host_action(args.host, args.action)
    utils.print_list([result], ['HOST', 'power_action'])


@utils.arg('--matching', metavar='<hostname>', default=None,
           help='List hypervisors matching the given <hostname>.')
def do_hypervisor_list(cs, args):
    """List hypervisors."""
    columns = ['ID', 'Hypervisor hostname']
    if args.matching:
        utils.print_list(cs.hypervisors.search(args.matching), columns)
    else:
        # Since we're not outputting detail data, choose
        # detailed=False for server-side efficiency
        utils.print_list(cs.hypervisors.list(False), columns)


@utils.arg('hostname', metavar='<hostname>',
           help='The hypervisor hostname (or pattern) to search for.')
def do_hypervisor_servers(cs, args):
    """List instances belonging to specific hypervisors."""
    hypers = cs.hypervisors.search(args.hostname, servers=True)

    class InstanceOnHyper(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    # Massage the result into a list to be displayed
    instances = []
    for hyper in hypers:
        hyper_host = hyper.hypervisor_hostname
        hyper_id = hyper.id
        instances.extend([InstanceOnHyper(id=serv['uuid'],
                                          name=serv['name'],
                                          hypervisor_hostname=hyper_host,
                                          hypervisor_id=hyper_id)
                          for serv in hyper.servers])

    # Output the data
    utils.print_list(instances, ['ID', 'Name', 'Hypervisor ID',
                                 'Hypervisor Hostname'])


@utils.arg('hypervisor_id',
    metavar='<hypervisor-id>',
    help='The ID of the hypervisor to show the details of.')
def do_hypervisor_show(cs, args):
    """Display the details of the specified hypervisor."""
    hyper = utils.find_resource(cs.hypervisors, args.hypervisor_id)

    # Build up the dict
    info = hyper._info.copy()
    info['service_id'] = info['service']['id']
    info['service_host'] = info['service']['host']
    del info['service']

    utils.print_dict(info)


@utils.arg('hypervisor_id',
    metavar='<hypervisor-id>',
    help='The ID of the hypervisor to show the uptime of.')
def do_hypervisor_uptime(cs, args):
    """Display the uptime of the specified hypervisor."""
    hyper = cs.hypervisors.uptime(args.hypervisor_id)

    # Output the uptime information
    utils.print_dict(hyper._info.copy())


def do_hypervisor_stats(cs, args):
    """Get hypervisor statistics over all compute nodes."""
    stats = cs.hypervisors.statistics()
    utils.print_dict(stats._info.copy())


def ensure_service_catalog_present(cs):
    if not hasattr(cs.client, 'service_catalog'):
        # Turn off token caching and re-auth
        cs.client.unauthenticate()
        cs.client.use_token_cache(False)
        cs.client.authenticate()


def do_endpoints(cs, _args):
    """Discover endpoints that get returned from the authenticate services"""
    ensure_service_catalog_present(cs)
    catalog = cs.client.service_catalog.catalog
    for e in catalog['access']['serviceCatalog']:
        utils.print_dict(e['endpoints'][0], e['name'])


def do_credentials(cs, _args):
    """Show user credentials returned from auth"""
    ensure_service_catalog_present(cs)
    catalog = cs.client.service_catalog.catalog
    utils.print_dict(catalog['access']['user'], "User Credentials")
    utils.print_dict(catalog['access']['token'], "Token")


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
@utils.arg('--port',
    dest='port',
    action='store',
    type=int,
    default=22,
    help='Optional flag to indicate which port to use for ssh. '
         '(Default=22)')
@utils.arg('--private',
    dest='private',
    action='store_true',
    default=False,
    help='Optional flag to indicate whether to use private address '
         'attached to an instance. (Default=False)')
@utils.arg('--ipv6',
    dest='ipv6',
    action='store_true',
    default=False,
    help='Optional flag to indicate whether to use an IPv6 address '
         'attached to an instance. (Defaults to IPv4 address)')
@utils.arg('--login', metavar='<login>', help='Login to use.', default="root")
@utils.arg('-i', '--identity',
    dest='identity',
    help='Private key file, same as the -i option to the ssh command.',
    default='')
def do_ssh(cs, args):
    """SSH into a server."""
    addresses = _find_server(cs, args.server).addresses
    address_type = "private" if args.private else "public"
    version = 6 if args.ipv6 else 4

    if address_type not in addresses:
        print "ERROR: No %s addresses found for '%s'." % (address_type,
                                                          args.server)
        return

    ip_address = None
    for address in addresses[address_type]:
        if address['version'] == version:
            ip_address = address['addr']
            break

    identity = '-i %s' % args.identity if len(args.identity) else ''

    if ip_address:
        os.system("ssh -%d -p%d %s %s@%s" % (version, args.port, identity,
                                             args.login, ip_address))
    else:
        pretty_version = "IPv%d" % version
        print "ERROR: No %s %s address found." % (address_type,
                                                  pretty_version)
        return


_quota_resources = ['instances', 'cores', 'ram', 'volumes', 'gigabytes',
                    'floating_ips', 'metadata_items', 'injected_files',
                    'injected_file_content_bytes']


def _quota_show(quotas):
    quota_dict = {}
    for resource in _quota_resources:
        quota_dict[resource] = getattr(quotas, resource, None)
    utils.print_dict(quota_dict)


def _quota_update(manager, identifier, args):
    updates = {}
    for resource in _quota_resources:
        val = getattr(args, resource, None)
        if val is not None:
            updates[resource] = val

    if updates:
        manager.update(identifier, **updates)


@utils.arg('tenant',
    metavar='<tenant-id>',
    help='UUID of tenant to list the quotas for.')
def do_quota_show(cs, args):
    """List the quotas for a tenant."""

    _quota_show(cs.quotas.get(args.tenant))


@utils.arg('tenant',
    metavar='<tenant-id>',
    help='UUID of tenant to list the default quotas for.')
def do_quota_defaults(cs, args):
    """List the default quotas for a tenant."""

    _quota_show(cs.quotas.defaults(args.tenant))


@utils.arg('tenant',
    metavar='<tenant-id>',
    help='UUID of tenant to set the quotas for.')
@utils.arg('--instances',
           metavar='<instances>',
           type=int, default=None,
           help='New value for the "instances" quota.')
@utils.arg('--cores',
           metavar='<cores>',
           type=int, default=None,
           help='New value for the "cores" quota.')
@utils.arg('--ram',
           metavar='<ram>',
           type=int, default=None,
           help='New value for the "ram" quota.')
@utils.arg('--volumes',
           metavar='<volumes>',
           type=int, default=None,
           help='New value for the "volumes" quota.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='New value for the "gigabytes" quota.')
@utils.arg('--floating-ips',
    metavar='<floating-ips>',
    type=int,
    default=None,
    help='New value for the "floating-ips" quota.')
@utils.arg('--floating_ips',
    type=int,
    help=argparse.SUPPRESS)
@utils.arg('--metadata-items',
    metavar='<metadata-items>',
    type=int,
    default=None,
    help='New value for the "metadata-items" quota.')
@utils.arg('--metadata_items',
    type=int,
    help=argparse.SUPPRESS)
@utils.arg('--injected-files',
    metavar='<injected-files>',
    type=int,
    default=None,
    help='New value for the "injected-files" quota.')
@utils.arg('--injected_files',
    type=int,
    help=argparse.SUPPRESS)
@utils.arg('--injected-file-content-bytes',
    metavar='<injected-file-content-bytes>',
    type=int,
    default=None,
    help='New value for the "injected-file-content-bytes" quota.')
@utils.arg('--injected_file_content_bytes',
    type=int,
    help=argparse.SUPPRESS)
def do_quota_update(cs, args):
    """Update the quotas for a tenant."""

    _quota_update(cs.quotas, args.tenant, args)


@utils.arg('class_name',
    metavar='<class>',
    help='Name of quota class to list the quotas for.')
def do_quota_class_show(cs, args):
    """List the quotas for a quota class."""

    _quota_show(cs.quota_classes.get(args.class_name))


@utils.arg('class_name',
    metavar='<class>',
    help='Name of quota class to set the quotas for.')
@utils.arg('--instances',
           metavar='<instances>',
           type=int, default=None,
           help='New value for the "instances" quota.')
@utils.arg('--cores',
           metavar='<cores>',
           type=int, default=None,
           help='New value for the "cores" quota.')
@utils.arg('--ram',
           metavar='<ram>',
           type=int, default=None,
           help='New value for the "ram" quota.')
@utils.arg('--volumes',
           metavar='<volumes>',
           type=int, default=None,
           help='New value for the "volumes" quota.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='New value for the "gigabytes" quota.')
@utils.arg('--floating-ips',
    metavar='<floating-ips>',
    type=int,
    default=None,
    help='New value for the "floating-ips" quota.')
@utils.arg('--floating_ips',
    type=int,
    help=argparse.SUPPRESS)
@utils.arg('--metadata-items',
    metavar='<metadata-items>',
    type=int,
    default=None,
    help='New value for the "metadata-items" quota.')
@utils.arg('--metadata_items',
    type=int,
    help=argparse.SUPPRESS)
@utils.arg('--injected-files',
    metavar='<injected-files>',
    type=int,
    default=None,
    help='New value for the "injected-files" quota.')
@utils.arg('--injected_files',
    type=int,
    help=argparse.SUPPRESS)
@utils.arg('--injected-file-content-bytes',
    metavar='<injected-file-content-bytes>',
    type=int,
    default=None,
    help='New value for the "injected-file-content-bytes" quota.')
@utils.arg('--injected_file_content_bytes',
    type=int,
    help=argparse.SUPPRESS)
def do_quota_class_update(cs, args):
    """Update the quotas for a quota class."""

    _quota_update(cs.quota_classes, args.class_name, args)

# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from __future__ import print_function

import argparse
import codecs
import collections
import datetime
import getpass
import logging
import os
import pprint
import sys
import time

from oslo_utils import netutils
from oslo_utils import strutils
from oslo_utils import timeutils
import six

import novaclient
from novaclient import api_versions
from novaclient import base
from novaclient import client
from novaclient import exceptions
from novaclient.i18n import _
from novaclient import shell
from novaclient import utils
from novaclient.v2 import availability_zones
from novaclient.v2 import quotas
from novaclient.v2 import servers


logger = logging.getLogger(__name__)


def emit_duplicated_image_with_warning(img, image_with):
    img_uuid_list = [str(image.id) for image in img]
    print(_('WARNING: Multiple matching images: %(img_uuid_list)s\n'
            'Using image: %(chosen_one)s') %
          {'img_uuid_list': img_uuid_list,
           'chosen_one': img_uuid_list[0]},
          file=sys.stderr)


CLIENT_BDM2_KEYS = {
    'id': 'uuid',
    'source': 'source_type',
    'dest': 'destination_type',
    'bus': 'disk_bus',
    'device': 'device_name',
    'size': 'volume_size',
    'format': 'guest_format',
    'bootindex': 'boot_index',
    'type': 'device_type',
    'shutdown': 'delete_on_termination',
    'tag': 'tag',
}


def _key_value_pairing(text):
    try:
        (k, v) = text.split('=', 1)
        return (k, v)
    except ValueError:
        msg = _("'%s' is not in the format of 'key=value'") % text
        raise argparse.ArgumentTypeError(msg)


def _meta_parsing(metadata):
    try:
        return dict(v.split('=', 1) for v in metadata)
    except ValueError:
        msg = _("'%s' is not in the format of 'key=value'") % metadata
        raise argparse.ArgumentTypeError(msg)


def _match_image(cs, wanted_properties):
    image_list = cs.glance.list()
    images_matched = []
    match = set(wanted_properties)
    for img in image_list:
        img_dict = {}
        # exclude any unhashable entries
        for key, value in img.to_dict().items():
            try:
                set([key, value])
            except TypeError:
                pass
            else:
                img_dict[key] = value
        if match == match.intersection(set(img_dict.items())):
            images_matched.append(img)
    return images_matched


def _supports_block_device_tags(cs):
    if (cs.api_version == api_versions.APIVersion('2.32') or
            cs.api_version >= api_versions.APIVersion('2.42')):
        return True
    else:
        return False


def _parse_device_spec(device_spec):
    spec_dict = {}
    for arg in device_spec.split(','):
        if '=' in arg:
            spec_dict.update([arg.split('=')])
        else:
            raise argparse.ArgumentTypeError(
                _("Expected a comma-separated list of key=value pairs. '%s' "
                  "is not a key=value pair.") % arg)
    return spec_dict


def _parse_block_device_mapping_v2(cs, args, image):
    bdm = []

    if args.boot_volume:
        bdm_dict = {'uuid': args.boot_volume, 'source_type': 'volume',
                    'destination_type': 'volume', 'boot_index': 0,
                    'delete_on_termination': False}
        bdm.append(bdm_dict)

    if args.snapshot:
        bdm_dict = {'uuid': args.snapshot, 'source_type': 'snapshot',
                    'destination_type': 'volume', 'boot_index': 0,
                    'delete_on_termination': False}
        bdm.append(bdm_dict)

    for device_spec in args.block_device:
        spec_dict = _parse_device_spec(device_spec)
        bdm_dict = {}

        if ('tag' in spec_dict and not _supports_block_device_tags(cs)):
            raise exceptions.CommandError(
                _("'tag' in block device mapping is not supported "
                  "in API version %(version)s.")
                % {'version': cs.api_version.get_string()})

        for key, value in spec_dict.items():
            bdm_dict[CLIENT_BDM2_KEYS[key]] = value

        source_type = bdm_dict.get('source_type')
        if not source_type:
            bdm_dict['source_type'] = 'blank'
        elif source_type not in (
                'volume', 'image', 'snapshot', 'blank'):
            raise exceptions.CommandError(
                _("The value of source_type key of --block-device "
                  "should be one of 'volume', 'image', 'snapshot' "
                  "or 'blank' but it was '%(action)s'")
                % {'action': source_type})

        destination_type = bdm_dict.get('destination_type')
        if not destination_type:
            source_type = bdm_dict['source_type']
            if source_type in ('image', 'blank'):
                bdm_dict['destination_type'] = 'local'
            if source_type in ('snapshot', 'volume'):
                bdm_dict['destination_type'] = 'volume'
        elif destination_type not in ('local', 'volume'):
            raise exceptions.CommandError(
                _("The value of destination_type key of --block-device "
                  "should be either 'local' or 'volume' but it "
                  "was '%(action)s'")
                % {'action': destination_type})

        # Convert the delete_on_termination to a boolean or set it to true by
        # default for local block devices when not specified.
        if 'delete_on_termination' in bdm_dict:
            action = bdm_dict['delete_on_termination']
            if action not in ['remove', 'preserve']:
                raise exceptions.CommandError(
                    _("The value of shutdown key of --block-device shall be "
                      "either 'remove' or 'preserve' but it was '%(action)s'")
                    % {'action': action})

            bdm_dict['delete_on_termination'] = (action == 'remove')
        elif bdm_dict.get('destination_type') == 'local':
            bdm_dict['delete_on_termination'] = True

        bdm.append(bdm_dict)

    for ephemeral_spec in args.ephemeral:
        bdm_dict = {'source_type': 'blank', 'destination_type': 'local',
                    'boot_index': -1, 'delete_on_termination': True}
        try:
            eph_dict = _parse_device_spec(ephemeral_spec)
        except ValueError:
            err_msg = (_("Invalid ephemeral argument '%s'.") % args.ephemeral)
            raise argparse.ArgumentTypeError(err_msg)
        if 'size' in eph_dict:
            bdm_dict['volume_size'] = eph_dict['size']
        if 'format' in eph_dict:
            bdm_dict['guest_format'] = eph_dict['format']

        bdm.append(bdm_dict)

    if args.swap:
        bdm_dict = {'source_type': 'blank', 'destination_type': 'local',
                    'boot_index': -1, 'delete_on_termination': True,
                    'guest_format': 'swap', 'volume_size': args.swap}
        bdm.append(bdm_dict)

    return bdm


def _supports_nic_tags(cs):
    if ((cs.api_version >= api_versions.APIVersion('2.32') and
         cs.api_version <= api_versions.APIVersion('2.36')) or
            cs.api_version >= api_versions.APIVersion('2.42')):
        return True
    else:
        return False


def _parse_nics(cs, args):
    supports_auto_alloc = cs.api_version >= api_versions.APIVersion('2.37')
    supports_nic_tags = _supports_nic_tags(cs)

    nic_keys = {'net-id', 'v4-fixed-ip', 'v6-fixed-ip', 'port-id', 'net-name'}

    if supports_auto_alloc and supports_nic_tags:
        # API version >= 2.42
        nic_keys.add('tag')
        err_msg = (_("Invalid nic argument '%s'. Nic arguments must be of "
                     "the form --nic <auto,none,net-id=net-uuid,"
                     "net-name=network-name,v4-fixed-ip=ip-addr,"
                     "v6-fixed-ip=ip-addr,port-id=port-uuid,tag=tag>, "
                     "with only one of net-id, net-name or port-id "
                     "specified. Specifying a --nic of auto or none cannot "
                     "be used with any other --nic value."))
    elif supports_auto_alloc and not supports_nic_tags:
        # 2.41 >= API version >= 2.37
        err_msg = (_("Invalid nic argument '%s'. Nic arguments must be of "
                     "the form --nic <auto,none,net-id=net-uuid,"
                     "net-name=network-name,v4-fixed-ip=ip-addr,"
                     "v6-fixed-ip=ip-addr,port-id=port-uuid>, "
                     "with only one of net-id, net-name or port-id "
                     "specified. Specifying a --nic of auto or none cannot "
                     "be used with any other --nic value."))
    elif not supports_auto_alloc and supports_nic_tags:
        # 2.36 >= API version >= 2.32
        nic_keys.add('tag')
        err_msg = (_("Invalid nic argument '%s'. Nic arguments must be of "
                     "the form --nic <net-id=net-uuid,"
                     "net-name=network-name,v4-fixed-ip=ip-addr,"
                     "v6-fixed-ip=ip-addr,port-id=port-uuid,tag=tag>, "
                     "with only one of net-id, net-name or port-id "
                     "specified."))
    else:
        # API version <= 2.31
        err_msg = (_("Invalid nic argument '%s'. Nic arguments must be of "
                     "the form --nic <net-id=net-uuid,"
                     "net-name=network-name,v4-fixed-ip=ip-addr,"
                     "v6-fixed-ip=ip-addr,port-id=port-uuid>, "
                     "with only one of net-id, net-name or port-id "
                     "specified."))
    auto_or_none = False
    nics = []
    for nic_str in args.nics:
        nic_info = {}
        nic_info_set = False
        for kv_str in nic_str.split(","):
            if auto_or_none:
                # Since we start with auto_or_none being False, it being true
                # means we've parsed an auto or none argument, then continued
                # after the comma to another key=value pair. Since auto or none
                # can only be given by themselves, raise.
                raise exceptions.CommandError(_("'auto' or 'none' cannot be "
                                                "used with any other nic "
                                                "arguments"))
            try:
                # handle the special auto/none cases
                if kv_str in ('auto', 'none'):
                    if not supports_auto_alloc:
                        raise exceptions.CommandError(err_msg % nic_str)
                    if nic_info_set:
                        # Since we start with nic_info_set being False, it
                        # being true means we've parsed a key=value pair, then
                        # landed on a auto or none argument after the comma.
                        # Since auto or none can only be given by themselves,
                        # raise.
                        raise exceptions.CommandError(
                            _("'auto' or 'none' cannot be used with any "
                              "other nic arguments"))
                    nics.append(kv_str)
                    auto_or_none = True
                    continue
                k, v = kv_str.split("=", 1)
            except ValueError:
                raise exceptions.CommandError(err_msg % nic_str)

            if k in nic_keys:
                # if user has given a net-name resolve it to network ID
                if k == 'net-name':
                    k = 'net-id'
                    v = _find_network_id(cs, v)
                # if some argument was given multiple times
                if k in nic_info:
                    raise exceptions.CommandError(err_msg % nic_str)
                nic_info[k] = v
                nic_info_set = True
            else:
                raise exceptions.CommandError(err_msg % nic_str)

        if auto_or_none:
            continue

        if 'v4-fixed-ip' in nic_info and not netutils.is_valid_ipv4(
                nic_info['v4-fixed-ip']):
            raise exceptions.CommandError(_("Invalid ipv4 address."))

        if 'v6-fixed-ip' in nic_info and not netutils.is_valid_ipv6(
                nic_info['v6-fixed-ip']):
            raise exceptions.CommandError(_("Invalid ipv6 address."))

        if bool(nic_info.get('net-id')) == bool(nic_info.get('port-id')):
            raise exceptions.CommandError(err_msg % nic_str)

        nics.append(nic_info)

    if nics:
        if auto_or_none:
            if len(nics) > 1:
                raise exceptions.CommandError(err_msg % nic_str)
            # change the single list entry to a string
            nics = nics[0]
    else:
        # Default to 'auto' if API version >= 2.37 and nothing was specified
        if supports_auto_alloc:
            nics = 'auto'

    return nics


def _boot(cs, args):
    """Boot a new server."""
    if not args.flavor:
        raise exceptions.CommandError(_("you need to specify a Flavor ID."))

    if args.image:
        image = _find_image(cs, args.image)
    else:
        image = None

    if not image and args.image_with:
        images = _match_image(cs, args.image_with)
        if len(images) > 1:
            emit_duplicated_image_with_warning(images, args.image_with)
        if images:
            image = images[0]
        else:
            raise exceptions.CommandError(_("No images match the property "
                                            "expected by --image-with"))

    min_count = 1
    max_count = 1
    if args.min_count is not None:
        if args.min_count < 1:
            raise exceptions.CommandError(_("min_count should be >= 1"))
        min_count = args.min_count
        max_count = min_count
    if args.max_count is not None:
        if args.max_count < 1:
            raise exceptions.CommandError(_("max_count should be >= 1"))
        max_count = args.max_count
    if (args.min_count is not None and
            args.max_count is not None and
            args.min_count > args.max_count):
        raise exceptions.CommandError(_("min_count should be <= max_count"))

    flavor = _find_flavor(cs, args.flavor)

    meta = _meta_parsing(args.meta)

    include_files = cs.api_version < api_versions.APIVersion('2.57')
    if include_files:
        files = {}
        for f in args.files:
            try:
                dst, src = f.split('=', 1)
                files[dst] = open(src)
            except IOError as e:
                raise exceptions.CommandError(
                    _("Can't open '%(src)s': %(exc)s") %
                    {'src': src, 'exc': e})
            except ValueError:
                raise exceptions.CommandError(
                    _("Invalid file argument '%s'. "
                      "File arguments must be of the "
                      "form '--file <dst-path=src-path>'") % f)

    # use the os-keypair extension
    key_name = None
    if args.key_name is not None:
        key_name = args.key_name

    if args.user_data:
        try:
            userdata = open(args.user_data)
        except IOError as e:
            raise exceptions.CommandError(_("Can't open '%(user_data)s': "
                                            "%(exc)s") %
                                          {'user_data': args.user_data,
                                           'exc': e})
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

    block_device_mapping_v2 = _parse_block_device_mapping_v2(cs, args, image)

    n_boot_args = len(list(filter(
        bool, (image, args.boot_volume, args.snapshot))))
    have_bdm = block_device_mapping_v2 or block_device_mapping

    # Fail if more than one boot devices are present
    # or if there is no device to boot from.
    if n_boot_args > 1 or n_boot_args == 0 and not have_bdm:
        raise exceptions.CommandError(
            _("you need to specify at least one source ID (Image, Snapshot, "
              "or Volume), a block device mapping or provide a set of "
              "properties to match against an image"))

    if block_device_mapping and block_device_mapping_v2:
        raise exceptions.CommandError(
            _("you can't mix old block devices (--block-device-mapping) "
              "with the new ones (--block-device, --boot-volume, --snapshot, "
              "--ephemeral, --swap)"))

    nics = _parse_nics(cs, args)

    hints = {}
    if args.scheduler_hints:
        for hint in args.scheduler_hints:
            key, _sep, value = hint.partition('=')
            # NOTE(vish): multiple copies of the same hint will
            #             result in a list of values
            if key in hints:
                if isinstance(hints[key], six.string_types):
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
        key_name=key_name,
        min_count=min_count,
        max_count=max_count,
        userdata=userdata,
        availability_zone=availability_zone,
        security_groups=security_groups,
        block_device_mapping=block_device_mapping,
        block_device_mapping_v2=block_device_mapping_v2,
        nics=nics,
        scheduler_hints=hints,
        config_drive=config_drive,
        admin_pass=args.admin_pass,
        access_ip_v4=args.access_ip_v4,
        access_ip_v6=args.access_ip_v6,
        reservation_id=args.return_reservation_id)

    if 'description' in args:
        boot_kwargs["description"] = args.description

    if 'tags' in args and args.tags:
        boot_kwargs["tags"] = args.tags.split(',')

    if include_files:
        boot_kwargs['files'] = files

    return boot_args, boot_kwargs


@utils.arg(
    '--flavor',
    default=None,
    metavar='<flavor>',
    help=_("Name or ID of flavor (see 'nova flavor-list')."))
@utils.arg(
    '--image',
    default=None,
    metavar='<image>',
    help=_("Name or ID of image (see 'glance image-list'). "))
@utils.arg(
    '--image-with',
    default=[],
    type=_key_value_pairing,
    action='append',
    metavar='<key=value>',
    help=_("Image metadata property (see 'glance image-show'). "))
@utils.arg(
    '--boot-volume',
    default=None,
    metavar="<volume_id>",
    help=_("Volume ID to boot from."))
@utils.arg(
    '--snapshot',
    default=None,
    metavar="<snapshot_id>",
    help=_("Snapshot ID to boot from (will create a volume)."))
@utils.arg(
    '--min-count',
    default=None,
    type=int,
    metavar='<number>',
    help=_("Boot at least <number> servers (limited by quota)."))
@utils.arg(
    '--max-count',
    default=None,
    type=int,
    metavar='<number>',
    help=_("Boot up to <number> servers (limited by quota)."))
@utils.arg(
    '--meta',
    metavar="<key=value>",
    action='append',
    default=[],
    help=_("Record arbitrary key/value metadata to /meta_data.json "
           "on the metadata server. Can be specified multiple times."))
@utils.arg(
    '--file',
    metavar="<dst-path=src-path>",
    action='append',
    dest='files',
    default=[],
    help=_("Store arbitrary files from <src-path> locally to <dst-path> "
           "on the new server. More files can be injected using multiple "
           "'--file' options. Limited by the 'injected_files' quota value. "
           "The default value is 5. You can get the current quota value by "
           "'Personality' limit from 'nova limits' command."),
    start_version='2.0', end_version='2.56')
@utils.arg(
    '--key-name',
    default=os.environ.get('NOVACLIENT_DEFAULT_KEY_NAME'),
    metavar='<key-name>',
    help=_("Key name of keypair that should be created earlier with \
           the command keypair-add."))
@utils.arg('name', metavar='<name>', help=_('Name for the new server.'))
@utils.arg(
    '--user-data',
    default=None,
    metavar='<user-data>',
    help=_("user data file to pass to be exposed by the metadata server."))
@utils.arg(
    '--availability-zone',
    default=None,
    metavar='<availability-zone>',
    help=_("The availability zone for server placement."))
@utils.arg(
    '--security-groups',
    default=None,
    metavar='<security-groups>',
    help=_("Comma separated list of security group names."))
@utils.arg(
    '--block-device-mapping',
    metavar="<dev-name=mapping>",
    action='append',
    default=[],
    help=_("Block device mapping in the format "
           "<dev-name>=<id>:<type>:<size(GiB)>:<delete-on-terminate>."))
@utils.arg(
    '--block-device',
    metavar="key1=value1[,key2=value2...]",
    action='append',
    default=[],
    start_version='2.0',
    end_version='2.31',
    help=_("Block device mapping with the keys: "
           "id=UUID (image_id, snapshot_id or volume_id only if using source "
           "image, snapshot or volume) "
           "source=source type (image, snapshot, volume or blank), "
           "dest=destination type of the block device (volume or local), "
           "bus=device's bus (e.g. uml, lxc, virtio, ...; if omitted, "
           "hypervisor driver chooses a suitable default, "
           "honoured only if device type is supplied) "
           "type=device type (e.g. disk, cdrom, ...; defaults to 'disk') "
           "device=name of the device (e.g. vda, xda, ...; "
           "if omitted, hypervisor driver chooses suitable device "
           "depending on selected bus; note the libvirt driver always "
           "uses default device names), "
           "size=size of the block device in MB(for swap) and in "
           "GiB(for other formats) "
           "(if omitted, hypervisor driver calculates size), "
           "format=device will be formatted (e.g. swap, ntfs, ...; optional), "
           "bootindex=integer used for ordering the boot disks "
           "(for image backed instances it is equal to 0, "
           "for others need to be specified) and "
           "shutdown=shutdown behaviour (either preserve or remove, "
           "for local destination set to remove)."))
@utils.arg(
    '--block-device',
    metavar="key1=value1[,key2=value2...]",
    action='append',
    default=[],
    start_version='2.32',
    end_version='2.32',
    help=_("Block device mapping with the keys: "
           "id=UUID (image_id, snapshot_id or volume_id only if using source "
           "image, snapshot or volume) "
           "source=source type (image, snapshot, volume or blank), "
           "dest=destination type of the block device (volume or local), "
           "bus=device's bus (e.g. uml, lxc, virtio, ...; if omitted, "
           "hypervisor driver chooses a suitable default, "
           "honoured only if device type is supplied) "
           "type=device type (e.g. disk, cdrom, ...; defaults to 'disk') "
           "device=name of the device (e.g. vda, xda, ...; "
           "tag=device metadata tag (optional) "
           "if omitted, hypervisor driver chooses suitable device "
           "depending on selected bus; note the libvirt driver always "
           "uses default device names), "
           "size=size of the block device in MB(for swap) and in "
           "GiB(for other formats) "
           "(if omitted, hypervisor driver calculates size), "
           "format=device will be formatted (e.g. swap, ntfs, ...; optional), "
           "bootindex=integer used for ordering the boot disks "
           "(for image backed instances it is equal to 0, "
           "for others need to be specified) and "
           "shutdown=shutdown behaviour (either preserve or remove, "
           "for local destination set to remove)."))
@utils.arg(
    '--block-device',
    metavar="key1=value1[,key2=value2...]",
    action='append',
    default=[],
    start_version='2.33',
    end_version='2.41',
    help=_("Block device mapping with the keys: "
           "id=UUID (image_id, snapshot_id or volume_id only if using source "
           "image, snapshot or volume) "
           "source=source type (image, snapshot, volume or blank), "
           "dest=destination type of the block device (volume or local), "
           "bus=device's bus (e.g. uml, lxc, virtio, ...; if omitted, "
           "hypervisor driver chooses a suitable default, "
           "honoured only if device type is supplied) "
           "type=device type (e.g. disk, cdrom, ...; defaults to 'disk') "
           "device=name of the device (e.g. vda, xda, ...; "
           "if omitted, hypervisor driver chooses suitable device "
           "depending on selected bus; note the libvirt driver always "
           "uses default device names), "
           "size=size of the block device in MB(for swap) and in "
           "GiB(for other formats) "
           "(if omitted, hypervisor driver calculates size), "
           "format=device will be formatted (e.g. swap, ntfs, ...; optional), "
           "bootindex=integer used for ordering the boot disks "
           "(for image backed instances it is equal to 0, "
           "for others need to be specified) and "
           "shutdown=shutdown behaviour (either preserve or remove, "
           "for local destination set to remove)."))
@utils.arg(
    '--block-device',
    metavar="key1=value1[,key2=value2...]",
    action='append',
    default=[],
    start_version='2.42',
    help=_("Block device mapping with the keys: "
           "id=UUID (image_id, snapshot_id or volume_id only if using source "
           "image, snapshot or volume) "
           "source=source type (image, snapshot, volume or blank), "
           "dest=destination type of the block device (volume or local), "
           "bus=device's bus (e.g. uml, lxc, virtio, ...; if omitted, "
           "hypervisor driver chooses a suitable default, "
           "honoured only if device type is supplied) "
           "type=device type (e.g. disk, cdrom, ...; defaults to 'disk') "
           "device=name of the device (e.g. vda, xda, ...; "
           "if omitted, hypervisor driver chooses suitable device "
           "depending on selected bus; note the libvirt driver always "
           "uses default device names), "
           "size=size of the block device in MB(for swap) and in "
           "GiB(for other formats) "
           "(if omitted, hypervisor driver calculates size), "
           "format=device will be formatted (e.g. swap, ntfs, ...; optional), "
           "bootindex=integer used for ordering the boot disks "
           "(for image backed instances it is equal to 0, "
           "for others need to be specified), "
           "shutdown=shutdown behaviour (either preserve or remove, "
           "for local destination set to remove) and "
           "tag=device metadata tag (optional)."))
@utils.arg(
    '--swap',
    metavar="<swap_size>",
    default=None,
    help=_("Create and attach a local swap block device of <swap_size> MB."))
@utils.arg(
    '--ephemeral',
    metavar="size=<size>[,format=<format>]",
    action='append',
    default=[],
    help=_("Create and attach a local ephemeral block device of <size> GiB "
           "and format it to <format>."))
@utils.arg(
    '--hint',
    action='append',
    dest='scheduler_hints',
    default=[],
    metavar='<key=value>',
    help=_("Send arbitrary key/value pairs to the scheduler for custom "
           "use."))
@utils.arg(
    '--nic',
    metavar="<net-id=net-uuid,net-name=network-name,v4-fixed-ip=ip-addr,"
            "v6-fixed-ip=ip-addr,port-id=port-uuid>",
    action='append',
    dest='nics',
    default=[],
    start_version='2.0',
    end_version='2.31',
    help=_("Create a NIC on the server. "
           "Specify option multiple times to create multiple NICs. "
           "net-id: attach NIC to network with this UUID "
           "net-name: attach NIC to network with this name "
           "(either port-id or net-id or net-name must be provided), "
           "v4-fixed-ip: IPv4 fixed address for NIC (optional), "
           "v6-fixed-ip: IPv6 fixed address for NIC (optional), "
           "port-id: attach NIC to port with this UUID "
           "(either port-id or net-id must be provided)."))
@utils.arg(
    '--nic',
    metavar="<net-id=net-uuid,net-name=network-name,v4-fixed-ip=ip-addr,"
            "v6-fixed-ip=ip-addr,port-id=port-uuid,tag=tag>",
    action='append',
    dest='nics',
    default=[],
    start_version='2.32',
    end_version='2.36',
    help=_("Create a NIC on the server. "
           "Specify option multiple times to create multiple nics. "
           "net-id: attach NIC to network with this UUID "
           "net-name: attach NIC to network with this name "
           "(either port-id or net-id or net-name must be provided), "
           "v4-fixed-ip: IPv4 fixed address for NIC (optional), "
           "v6-fixed-ip: IPv6 fixed address for NIC (optional), "
           "port-id: attach NIC to port with this UUID "
           "tag: interface metadata tag (optional) "
           "(either port-id or net-id must be provided)."))
@utils.arg(
    '--nic',
    metavar="<auto,none,"
            "net-id=net-uuid,net-name=network-name,port-id=port-uuid,"
            "v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr>",
    action='append',
    dest='nics',
    default=[],
    start_version='2.37',
    end_version='2.41',
    help=_("Create a NIC on the server. "
           "Specify option multiple times to create multiple nics unless "
           "using the special 'auto' or 'none' values. "
           "auto: automatically allocate network resources if none are "
           "available. This cannot be specified with any other nic value and "
           "cannot be specified multiple times. "
           "none: do not attach a NIC at all. This cannot be specified "
           "with any other nic value and cannot be specified multiple times. "
           "net-id: attach NIC to network with a specific UUID. "
           "net-name: attach NIC to network with this name "
           "(either port-id or net-id or net-name must be provided), "
           "v4-fixed-ip: IPv4 fixed address for NIC (optional), "
           "v6-fixed-ip: IPv6 fixed address for NIC (optional), "
           "port-id: attach NIC to port with this UUID "
           "(either port-id or net-id must be provided)."))
@utils.arg(
    '--nic',
    metavar="<auto,none,"
            "net-id=net-uuid,net-name=network-name,port-id=port-uuid,"
            "v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr,tag=tag>",
    action='append',
    dest='nics',
    default=[],
    start_version='2.42',
    help=_("Create a NIC on the server. "
           "Specify option multiple times to create multiple nics unless "
           "using the special 'auto' or 'none' values. "
           "auto: automatically allocate network resources if none are "
           "available. This cannot be specified with any other nic value and "
           "cannot be specified multiple times. "
           "none: do not attach a NIC at all. This cannot be specified "
           "with any other nic value and cannot be specified multiple times. "
           "net-id: attach NIC to network with a specific UUID. "
           "net-name: attach NIC to network with this name "
           "(either port-id or net-id or net-name must be provided), "
           "v4-fixed-ip: IPv4 fixed address for NIC (optional), "
           "v6-fixed-ip: IPv6 fixed address for NIC (optional), "
           "port-id: attach NIC to port with this UUID "
           "tag: interface metadata tag (optional) "
           "(either port-id or net-id must be provided)."))
@utils.arg(
    '--config-drive',
    metavar="<value>",
    dest='config_drive',
    default=False,
    help=_("Enable config drive."))
@utils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the new server boot progress until it completes.'))
@utils.arg(
    '--admin-pass',
    dest='admin_pass',
    metavar='<value>',
    default=None,
    help=_('Admin password for the instance.'))
@utils.arg(
    '--access-ip-v4',
    dest='access_ip_v4',
    metavar='<value>',
    default=None,
    help=_('Alternative access IPv4 of the instance.'))
@utils.arg(
    '--access-ip-v6',
    dest='access_ip_v6',
    metavar='<value>',
    default=None,
    help=_('Alternative access IPv6 of the instance.'))
@utils.arg(
    '--description',
    metavar='<description>',
    dest='description',
    default=None,
    help=_('Description for the server.'),
    start_version="2.19")
@utils.arg(
    '--tags',
    metavar='<tags>',
    default=None,
    help=_('Tags for the server.'
           'Tags must be separated by commas: --tags <tag1,tag2>'),
    start_version="2.52")
@utils.arg(
    '--return-reservation-id',
    dest='return_reservation_id',
    action="store_true",
    default=False,
    help=_("Return a reservation id bound to created servers."))
def do_boot(cs, args):
    """Boot a new server."""
    boot_args, boot_kwargs = _boot(cs, args)

    server = cs.servers.create(*boot_args, **boot_kwargs)
    if boot_kwargs['reservation_id']:
        new_server = {'reservation_id': server}
        utils.print_dict(new_server)
        return
    else:
        _print_server(cs, args, server)

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'building', ['active'])


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True,
                     status_field="status", silent=False):
    """Block while an action is being performed, periodically printing
    progress.
    """
    def print_progress(progress):
        if show_progress:
            msg = (_('\rServer %(action)s... %(progress)s%% complete')
                   % dict(action=action, progress=progress))
        else:
            msg = _('\rServer %(action)s...') % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    if not silent:
        print()

    while True:
        obj = poll_fn(obj_id)

        status = getattr(obj, status_field)

        if status:
            status = status.lower()

        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            if not silent:
                print_progress(100)
                print(_("\nFinished"))
            break
        elif status == "error":
            if not silent:
                print(_("\nError %s server") % action)
            raise exceptions.ResourceInErrorState(obj)
        elif status == "deleted":
            if not silent:
                print(_("\nDeleted %s server") % action)
            raise exceptions.InstanceInDeletedState(obj.fault["message"])

        if not silent:
            print_progress(progress)

        time.sleep(poll_period)


def _expand_dict_attr(collection, attr):
    """Expand item attribute whose value is a dict.

    Take a collection of items where the named attribute is known to have a
    dictionary value and replace the named attribute with multiple attributes
    whose names are the keys of the dictionary namespaced with the original
    attribute name.
    """
    for item in collection:
        field = getattr(item, attr)
        delattr(item, attr)
        for subkey in field.keys():
            setattr(item, attr + ':' + subkey, field[subkey])
            item.set_info(attr + ':' + subkey, field[subkey])


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__.keys()
        item_dict = item.to_dict()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item_dict[from_key])
                item.set_info(to_key, item_dict[from_key])


def _translate_extended_states(collection):
    power_states = [
        'NOSTATE',      # 0x00
        'Running',      # 0x01
        '',             # 0x02
        'Paused',       # 0x03
        'Shutdown',     # 0x04
        '',             # 0x05
        'Crashed',      # 0x06
        'Suspended'     # 0x07
    ]

    for item in collection:
        try:
            setattr(item, 'power_state',
                    power_states[getattr(item, 'power_state')])
        except AttributeError:
            setattr(item, 'power_state', "N/A")
        try:
            getattr(item, 'task_state')
        except AttributeError:
            setattr(item, 'task_state', "N/A")
        item.set_info('power_state', item.power_state)
        item.set_info('task_state', item.task_state)


def _translate_flavor_keys(collection):
    _translate_keys(collection, [('ram', 'memory_mb')])


def _print_flavor_extra_specs(flavor):
    try:
        return flavor.get_keys()
    except exceptions.NotFound:
        return "N/A"


def _print_flavor_list(cs, flavors, show_extra_specs=False):
    _translate_flavor_keys(flavors)

    headers = [
        'ID',
        'Name',
        'Memory_MB',
        'Disk',
        'Ephemeral',
        'Swap',
        'VCPUs',
        'RXTX_Factor',
        'Is_Public',
    ]

    formatters = {}
    if show_extra_specs:
        # Starting with microversion 2.61, extra specs are included
        # in the flavor details response.
        if cs.api_version < api_versions.APIVersion('2.61'):
            formatters = {'extra_specs': _print_flavor_extra_specs}
        headers.append('extra_specs')

    if cs.api_version >= api_versions.APIVersion('2.55'):
        headers.append('Description')

    utils.print_list(flavors, headers, formatters)


@utils.arg(
    '--extra-specs',
    dest='extra_specs',
    action='store_true',
    default=False,
    help=_('Get extra-specs of each flavor.'))
@utils.arg(
    '--all',
    dest='all',
    action='store_true',
    default=False,
    help=_('Display all flavors (Admin only).'))
@utils.arg(
    '--marker',
    dest='marker',
    metavar='<marker>',
    default=None,
    help=_('The last flavor ID of the previous page; displays list of flavors'
           ' after "marker".'))
@utils.arg(
    '--min-disk',
    dest='min_disk',
    metavar='<min-disk>',
    default=None,
    help=_('Filters the flavors by a minimum disk space, in GiB.'))
@utils.arg(
    '--min-ram',
    dest='min_ram',
    metavar='<min-ram>',
    default=None,
    help=_('Filters the flavors by a minimum RAM, in MB.'))
@utils.arg(
    '--limit',
    dest='limit',
    metavar='<limit>',
    type=int,
    default=None,
    help=_("Maximum number of flavors to display. If limit is bigger than "
           "'CONF.api.max_limit' option of Nova API, limit "
           "'CONF.api.max_limit' will be used instead."))
@utils.arg(
    '--sort-key',
    dest='sort_key',
    metavar='<sort-key>',
    default=None,
    help=_('Flavors list sort key.'))
@utils.arg(
    '--sort-dir',
    dest='sort_dir',
    metavar='<sort-dir>',
    default=None,
    help=_('Flavors list sort direction.'))
def do_flavor_list(cs, args):
    """Print a list of available 'flavors' (sizes of servers)."""
    if args.all:
        flavors = cs.flavors.list(is_public=None, min_disk=args.min_disk,
                                  min_ram=args.min_ram, sort_key=args.sort_key,
                                  sort_dir=args.sort_dir)
    else:
        flavors = cs.flavors.list(marker=args.marker, min_disk=args.min_disk,
                                  min_ram=args.min_ram, sort_key=args.sort_key,
                                  sort_dir=args.sort_dir, limit=args.limit)
    _print_flavor_list(cs, flavors, args.extra_specs)


@utils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Name or ID of the flavor to delete."))
def do_flavor_delete(cs, args):
    """Delete a specific flavor"""
    flavor = _find_flavor(cs, args.flavor)
    cs.flavors.delete(flavor)


@utils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Name or ID of flavor."))
def do_flavor_show(cs, args):
    """Show details about the given flavor."""
    flavor = _find_flavor(cs, args.flavor)
    _print_flavor(flavor)


@utils.arg(
    'name',
    metavar='<name>',
    help=_("Unique name of the new flavor."))
@utils.arg(
    'id',
    metavar='<id>',
    help=_("Unique ID of the new flavor."
           " Specifying 'auto' will generated a UUID for the ID."))
@utils.arg(
    'ram',
    metavar='<ram>',
    help=_("Memory size in MB."))
@utils.arg(
    'disk',
    metavar='<disk>',
    help=_("Disk size in GiB."))
@utils.arg(
    '--ephemeral',
    metavar='<ephemeral>',
    help=_("Ephemeral space size in GiB (default 0)."),
    default=0)
@utils.arg(
    'vcpus',
    metavar='<vcpus>',
    help=_("Number of vcpus"))
@utils.arg(
    '--swap',
    metavar='<swap>',
    help=_("Additional swap space size in MB (default 0)."),
    default=0)
@utils.arg(
    '--rxtx-factor',
    metavar='<factor>',
    help=_("RX/TX factor (default 1)."),
    default=1.0)
@utils.arg(
    '--is-public',
    metavar='<is-public>',
    help=_("Make flavor accessible to the public (default true)."),
    type=lambda v: strutils.bool_from_string(v, True),
    default=True)
@utils.arg(
    '--description',
    metavar='<description>',
    help=_('A free form description of the flavor. Limited to 65535 '
           'characters in length. Only printable characters are allowed.'),
    start_version='2.55')
def do_flavor_create(cs, args):
    """Create a new flavor."""
    if cs.api_version >= api_versions.APIVersion('2.55'):
        description = args.description
    else:
        description = None
    f = cs.flavors.create(args.name, args.ram, args.vcpus, args.disk, args.id,
                          args.ephemeral, args.swap, args.rxtx_factor,
                          args.is_public, description)
    _print_flavor_list(cs, [f])


@api_versions.wraps('2.55')
@utils.arg(
    'flavor',
    metavar='<flavor>',
    help=_('Name or ID of the flavor to update.'))
@utils.arg(
    'description',
    metavar='<description>',
    help=_('A free form description of the flavor. Limited to 65535 '
           'characters in length. Only printable characters are allowed.'))
def do_flavor_update(cs, args):
    """Update the description of an existing flavor."""
    flavorid = _find_flavor(cs, args.flavor)
    flavor = cs.flavors.update(flavorid, args.description)
    _print_flavor_list(cs, [flavor])


@utils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Name or ID of flavor."))
@utils.arg(
    'action',
    metavar='<action>',
    choices=['set', 'unset'],
    help=_("Actions: 'set' or 'unset'."))
@utils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help=_('Extra_specs to set/unset (only key is necessary on unset).'))
def do_flavor_key(cs, args):
    """Set or unset extra_spec for a flavor."""
    flavor = _find_flavor(cs, args.flavor)
    keypair = _extract_metadata(args)

    if args.action == 'set':
        flavor.set_keys(keypair)
    elif args.action == 'unset':
        flavor.unset_keys(keypair.keys())


@utils.arg(
    '--flavor',
    metavar='<flavor>',
    help=_("Filter results by flavor name or ID."))
def do_flavor_access_list(cs, args):
    """Print access information about the given flavor."""
    if args.flavor:
        flavor = _find_flavor(cs, args.flavor)
        if flavor.is_public:
            raise exceptions.CommandError(_("Access list not available "
                                            "for public flavors."))
        kwargs = {'flavor': flavor}
    else:
        raise exceptions.CommandError(_("Unable to get all access lists. "
                                        "Specify --flavor"))

    try:
        access_list = cs.flavor_access.list(**kwargs)
    except NotImplementedError as e:
        raise exceptions.CommandError("%s" % str(e))

    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


@utils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Flavor name or ID to add access for the given tenant."))
@utils.arg(
    'tenant', metavar='<tenant_id>',
    help=_('Tenant ID to add flavor access for.'))
def do_flavor_access_add(cs, args):
    """Add flavor access for the given tenant."""
    flavor = _find_flavor(cs, args.flavor)
    access_list = cs.flavor_access.add_tenant_access(flavor, args.tenant)
    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


@utils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Flavor name or ID to remove access for the given tenant."))
@utils.arg(
    'tenant', metavar='<tenant_id>',
    help=_('Tenant ID to remove flavor access for.'))
def do_flavor_access_remove(cs, args):
    """Remove flavor access for the given tenant."""
    flavor = _find_flavor(cs, args.flavor)
    access_list = cs.flavor_access.remove_tenant_access(flavor, args.tenant)
    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


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
    info = image.to_dict()

    # ignore links, we don't need to present those
    info.pop('links', None)

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


def _print_flavor(flavor):
    info = flavor.to_dict()
    # ignore links, we don't need to present those
    info.pop('links')
    # Starting with microversion 2.61, extra specs are included
    # in the flavor details response.
    if 'extra_specs' not in info:
        info.update({"extra_specs": _print_flavor_extra_specs(flavor)})
    utils.print_dict(info)


@utils.arg(
    '--reservation-id',
    dest='reservation_id',
    metavar='<reservation-id>',
    default=None,
    help=_('Only return servers that match reservation-id.'))
@utils.arg(
    '--ip',
    dest='ip',
    metavar='<ip-regexp>',
    default=None,
    help=_('Search with regular expression match by IP address.'))
@utils.arg(
    '--ip6',
    dest='ip6',
    metavar='<ip6-regexp>',
    default=None,
    help=_('Search with regular expression match by IPv6 address.'))
@utils.arg(
    '--name',
    dest='name',
    metavar='<name-regexp>',
    default=None,
    help=_('Search with regular expression match by name.'))
@utils.arg(
    '--instance-name',
    dest='instance_name',
    metavar='<name-regexp>',
    default=None,
    help=_('Search with regular expression match by server name.'))
@utils.arg(
    '--status',
    dest='status',
    metavar='<status>',
    default=None,
    help=_('Search by server status.'))
@utils.arg(
    '--flavor',
    dest='flavor',
    metavar='<flavor>',
    default=None,
    help=_('Search by flavor name or ID.'))
@utils.arg(
    '--image',
    dest='image',
    metavar='<image>',
    default=None,
    help=_('Search by image name or ID.'))
@utils.arg(
    '--host',
    dest='host',
    metavar='<hostname>',
    default=None,
    help=_('Search servers by hostname to which they are assigned (Admin '
           'only).'))
@utils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=int(strutils.bool_from_string(
        os.environ.get("ALL_TENANTS", 'false'), True)),
    help=_('Display information from all tenants (Admin only).'))
@utils.arg(
    '--tenant',
    # nova db searches by project_id
    dest='tenant',
    metavar='<tenant>',
    nargs='?',
    help=_('Display information from single tenant (Admin only).'))
@utils.arg(
    '--user',
    dest='user',
    metavar='<user>',
    nargs='?',
    help=_('Display information from single user (Admin only).'))
@utils.arg(
    '--deleted',
    dest='deleted',
    action="store_true",
    default=False,
    help=_('Only display deleted servers (Admin only).'))
@utils.arg(
    '--fields',
    default=None,
    metavar='<fields>',
    help=_('Comma-separated list of fields to display. '
           'Use the show command to see which fields are available.'))
@utils.arg(
    '--minimal',
    dest='minimal',
    action="store_true",
    default=False,
    help=_('Get only UUID and name.'))
@utils.arg(
    '--sort',
    dest='sort',
    metavar='<key>[:<direction>]',
    help=_('Comma-separated list of sort keys and directions in the form '
           'of <key>[:<asc|desc>]. The direction defaults to descending if '
           'not specified.'))
@utils.arg(
    '--marker',
    dest='marker',
    metavar='<marker>',
    default=None,
    help=_('The last server UUID of the previous page; displays list of '
           'servers after "marker".'))
@utils.arg(
    '--limit',
    dest='limit',
    metavar='<limit>',
    type=int,
    default=None,
    help=_("Maximum number of servers to display. If limit == -1, all servers "
           "will be displayed. If limit is bigger than 'CONF.api.max_limit' "
           "option of Nova API, multiple requests will be sent and results "
           "will be merged."))
@utils.arg(
    '--changes-since',
    dest='changes_since',
    metavar='<changes_since>',
    default=None,
    help=_("List only servers changed after a certain point of time. "
           "The provided time should be an ISO 8061 formatted time. "
           "ex 2016-03-04T06:27:59Z ."))
@utils.arg(
    '--tags',
    dest='tags',
    metavar='<tags>',
    default=None,
    help=_("The given tags must all be present for a server to be included in "
           "the list result. Boolean expression in this case is 't1 AND t2'. "
           "Tags must be separated by commas: --tags <tag1,tag2>"),
    start_version="2.26")
@utils.arg(
    '--tags-any',
    dest='tags-any',
    metavar='<tags-any>',
    default=None,
    help=_("If one of the given tags is present the server will be included "
           "in the list result. Boolean expression in this case is "
           "'t1 OR t2'. Tags must be separated by commas: "
           "--tags-any <tag1,tag2>"),
    start_version="2.26")
@utils.arg(
    '--not-tags',
    dest='not-tags',
    metavar='<not-tags>',
    default=None,
    help=_("Only the servers that do not have any of the given tags will "
           "be included in the list results. Boolean expression in this case "
           "is 'NOT(t1 AND t2)'. Tags must be separated by commas: "
           "--not-tags <tag1,tag2>"),
    start_version="2.26")
@utils.arg(
    '--not-tags-any',
    dest='not-tags-any',
    metavar='<not-tags-any>',
    default=None,
    help=_("Only the servers that do not have at least one of the given tags "
           "will be included in the list result. Boolean expression in this "
           "case is 'NOT(t1 OR t2)'. Tags must be separated by commas: "
           "--not-tags-any <tag1,tag2>"),
    start_version="2.26")
def do_list(cs, args):
    """List servers."""
    imageid = None
    flavorid = None
    if args.image:
        imageid = _find_image(cs, args.image).id
    if args.flavor:
        flavorid = _find_flavor(cs, args.flavor).id
    # search by tenant or user only works with all_tenants
    if args.tenant or args.user:
        args.all_tenants = 1
    search_opts = {
        'all_tenants': args.all_tenants,
        'reservation_id': args.reservation_id,
        'ip': args.ip,
        'ip6': args.ip6,
        'name': args.name,
        'image': imageid,
        'flavor': flavorid,
        'status': args.status,
        'tenant_id': args.tenant,
        'user_id': args.user,
        'host': args.host,
        'deleted': args.deleted,
        'instance_name': args.instance_name,
        'changes-since': args.changes_since}

    for arg in ('tags', "tags-any", 'not-tags', 'not-tags-any'):
        if arg in args:
            search_opts[arg] = getattr(args, arg)

    filters = {'security_groups': utils.format_security_groups}

    # In microversion 2.47 we started embedding flavor info in server details.
    have_embedded_flavor_info = (
        cs.api_version >= api_versions.APIVersion('2.47'))
    # If we don't have embedded flavor info then we only report the flavor id
    # rather than looking up the rest of the information.
    if not have_embedded_flavor_info:
        filters['flavor'] = lambda f: f['id']

    id_col = 'ID'

    detailed = not args.minimal

    sort_keys = []
    sort_dirs = []
    if args.sort:
        for sort in args.sort.split(','):
            sort_key, _sep, sort_dir = sort.partition(':')
            if not sort_dir:
                sort_dir = 'desc'
            elif sort_dir not in ('asc', 'desc'):
                raise exceptions.CommandError(_(
                    'Unknown sort direction: %s') % sort_dir)
            sort_keys.append(sort_key)
            sort_dirs.append(sort_dir)

    if search_opts['changes-since']:
        try:
            timeutils.parse_isotime(search_opts['changes-since'])
        except ValueError:
            raise exceptions.CommandError(_('Invalid changes-since value: %s')
                                          % search_opts['changes-since'])

    servers = cs.servers.list(detailed=detailed,
                              search_opts=search_opts,
                              sort_keys=sort_keys,
                              sort_dirs=sort_dirs,
                              marker=args.marker,
                              limit=args.limit)
    convert = [('OS-EXT-SRV-ATTR:host', 'host'),
               ('OS-EXT-STS:task_state', 'task_state'),
               ('OS-EXT-SRV-ATTR:instance_name', 'instance_name'),
               ('OS-EXT-STS:power_state', 'power_state'),
               ('hostId', 'host_id')]
    _translate_keys(servers, convert)
    _translate_extended_states(servers)

    formatters = {}
    cols = []
    fmts = {}

    # For detailed lists, if we have embedded flavor information then replace
    # the "flavor" attribute with more detailed information.
    if detailed and have_embedded_flavor_info:
        _expand_dict_attr(servers, 'flavor')

    if servers:
        cols, fmts = _get_list_table_columns_and_formatters(
            args.fields, servers, exclude_fields=('id',), filters=filters)

    if args.minimal:
        columns = [
            id_col,
            'Name']
    elif cols:
        columns = [id_col] + cols
        formatters.update(fmts)
    else:
        columns = [
            id_col,
            'Name',
            'Status',
            'Task State',
            'Power State',
            'Networks'
        ]
        # If getting the data for all tenants, print
        # Tenant ID as well
        if search_opts['all_tenants']:
            columns.insert(2, 'Tenant ID')
        if search_opts['changes-since']:
            columns.append('Updated')
    formatters['Networks'] = utils.format_servers_list_networks
    sortby_index = 1
    if args.sort:
        sortby_index = None
    utils.print_list(servers, columns,
                     formatters, sortby_index=sortby_index)


def _get_list_table_columns_and_formatters(fields, objs, exclude_fields=(),
                                           filters=None):
    """Check and add fields to output columns.

    If there is any value in fields that not an attribute of obj,
    CommandError will be raised.

    If fields has duplicate values (case sensitive), we will make them unique
    and ignore duplicate ones.

    If exclude_fields is specified, any field both in fields and
    exclude_fields will be ignored.

    :param fields: A list of string contains the fields to be printed.
    :param objs: An list of object which will be used to check if field is
                 valid or not. Note, we don't check fields if obj is None or
                 empty.
    :param exclude_fields: A tuple of string which contains the fields to be
                           excluded.
    :param filters: A dictionary defines how to get value from fields, this
                    is useful when field's value is a complex object such as
                    dictionary.

    :return: columns, formatters.
             columns is a list of string which will be used as table header.
             formatters is a dictionary specifies how to display the value
             of the field.
             They can be [], {}.
    :raise: novaclient.exceptions.CommandError
    """
    if not fields:
        return [], {}

    if not objs:
        obj = None
    elif isinstance(objs, list):
        obj = objs[0]
    else:
        obj = objs

    columns = []
    formatters = {}
    existing_fields = set()

    non_existent_fields = []
    exclude_fields = set(exclude_fields)

    # NOTE(ttsiouts): Bug #1733917. Validating the fields using the keys of
    # the Resource.to_dict(). Adding also the 'networks' field.
    if obj:
        obj_dict = obj.to_dict()
        existing_fields = set(['networks']) | set(obj_dict.keys())

    for field in fields.split(','):
        if field not in existing_fields:
            non_existent_fields.append(field)
            continue
        if field in exclude_fields:
            continue
        field_title, formatter = utils.make_field_formatter(field,
                                                            filters)
        columns.append(field_title)
        formatters[field_title] = formatter
        exclude_fields.add(field)

    if non_existent_fields:
        raise exceptions.CommandError(
            _("Non-existent fields are specified: %s") % non_existent_fields)

    return columns, formatters


@utils.arg(
    '--hard',
    dest='reboot_type',
    action='store_const',
    const=servers.REBOOT_HARD,
    default=servers.REBOOT_SOFT,
    help=_('Perform a hard reboot (instead of a soft one). '
           'Note: Ironic does not currently support soft reboot; '
           'consequently, bare metal nodes will always do a hard '
           'reboot, regardless of the use of this option.'))
@utils.arg(
    'server',
    metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
@utils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Poll until reboot is complete.'))
def do_reboot(cs, args):
    """Reboot a server."""
    servers = [_find_server(cs, s) for s in args.server]
    utils.do_action_on_many(
        lambda s: s.reboot(args.reboot_type),
        servers,
        _("Request to reboot server %s has been accepted."),
        _("Unable to reboot the specified server(s)."))

    if args.poll:
        utils.do_action_on_many(
            lambda s: _poll_for_status(cs.servers.get, s.id, 'rebooting',
                                       ['active'], show_progress=False),
            servers,
            _("Wait for server %s reboot."),
            _("Wait for specified server(s) failed."))


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('image', metavar='<image>', help=_("Name or ID of new image."))
@utils.arg(
    '--rebuild-password',
    dest='rebuild_password',
    metavar='<rebuild-password>',
    default=False,
    help=_("Set the provided admin password on the rebuilt server."))
@utils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the server rebuild progress until it completes.'))
@utils.arg(
    '--minimal',
    dest='minimal',
    action="store_true",
    default=False,
    help=_('Skips flavor/image lookups when showing servers.'))
@utils.arg(
    '--preserve-ephemeral',
    action="store_true",
    default=False,
    help=_('Preserve the default ephemeral storage partition on rebuild.'))
@utils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help=_('Name for the new server.'))
@utils.arg(
    '--description',
    metavar='<description>',
    dest='description',
    default=None,
    help=_('New description for the server.'),
    start_version="2.19")
@utils.arg(
    '--meta',
    metavar="<key=value>",
    action='append',
    default=[],
    help=_("Record arbitrary key/value metadata to /meta_data.json "
           "on the metadata server. Can be specified multiple times."))
@utils.arg(
    '--file',
    metavar="<dst-path=src-path>",
    action='append',
    dest='files',
    default=[],
    help=_("Store arbitrary files from <src-path> locally to <dst-path> "
           "on the new server. More files can be injected using multiple "
           "'--file' options. You may store up to 5 files by default. "
           "The maximum number of files is specified by the 'Personality' "
           "limit reported by the 'nova limits' command."),
    start_version='2.0', end_version='2.56')
@utils.arg(
    '--key-name',
    metavar='<key-name>',
    default=None,
    help=_("Keypair name to set in the server. "
           "Cannot be specified with the '--key-unset' option."),
    start_version='2.54')
@utils.arg(
    '--key-unset',
    action='store_true',
    default=False,
    help=_("Unset keypair in the server. "
           "Cannot be specified with the '--key-name' option."),
    start_version='2.54')
@utils.arg(
    '--user-data',
    default=None,
    metavar='<user-data>',
    help=_("User data file to pass to be exposed by the metadata server."),
    start_version='2.57')
@utils.arg(
    '--user-data-unset',
    action='store_true',
    default=False,
    help=_("Unset user_data in the server. Cannot be specified with the "
           "'--user-data' option."),
    start_version='2.57')
def do_rebuild(cs, args):
    """Shutdown, re-image, and re-boot a server."""
    server = _find_server(cs, args.server)
    image = _find_image(cs, args.image)

    if args.rebuild_password is not False:
        _password = args.rebuild_password
    else:
        _password = None

    kwargs = {'preserve_ephemeral': args.preserve_ephemeral,
              'name': args.name,
              'meta': _meta_parsing(args.meta)}
    if 'description' in args:
        kwargs['description'] = args.description

    # 2.57 deprecates the --file option and adds the --user-data and
    # --user-data-unset options.
    if cs.api_version < api_versions.APIVersion('2.57'):
        files = {}
        for f in args.files:
            try:
                dst, src = f.split('=', 1)
                with open(src, 'r') as s:
                    files[dst] = s.read()
            except IOError as e:
                raise exceptions.CommandError(
                    _("Can't open '%(src)s': %(exc)s") %
                    {'src': src, 'exc': e})
            except ValueError:
                raise exceptions.CommandError(
                    _("Invalid file argument '%s'. "
                      "File arguments must be of the "
                      "form '--file <dst-path=src-path>'") % f)
        kwargs['files'] = files
    else:
        if args.user_data_unset:
            kwargs['userdata'] = None
            if args.user_data:
                raise exceptions.CommandError(
                    _("Cannot specify '--user-data-unset' with "
                      "'--user-data'."))
        elif args.user_data:
            kwargs['userdata'] = args.user_data

    if cs.api_version >= api_versions.APIVersion('2.54'):
        if args.key_unset:
            kwargs['key_name'] = None
            if args.key_name:
                raise exceptions.CommandError(
                    _("Cannot specify '--key-unset' with '--key-name'."))
        elif args.key_name:
            kwargs['key_name'] = args.key_name

    server = server.rebuild(image, _password, **kwargs)
    _print_server(cs, args, server)

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'rebuilding', ['active'])


@utils.arg(
    'server', metavar='<server>',
    help=_('Name (old name) or ID of server.'))
@utils.arg(
    '--name',
    metavar='<name>',
    dest='name',
    default=None,
    help=_('New name for the server.'))
@utils.arg(
    '--description',
    metavar='<description>',
    dest='description',
    default=None,
    help=_('New description for the server. If it equals to empty string '
           '(i.g. ""), the server description will be removed.'),
    start_version="2.19")
def do_update(cs, args):
    """Update the name or the description for a server."""
    update_kwargs = {}
    if args.name:
        update_kwargs["name"] = args.name
    if "description" in args and args.description is not None:
        update_kwargs["description"] = args.description
    _find_server(cs, args.server).update(**update_kwargs)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Name or ID of new flavor."))
@utils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the server resize progress until it completes.'))
def do_resize(cs, args):
    """Resize a server."""
    server = _find_server(cs, args.server)
    flavor = _find_flavor(cs, args.flavor)
    server.resize(flavor)
    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'resizing',
                         ['active', 'verify_resize'])


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_resize_confirm(cs, args):
    """Confirm a previous resize."""
    _find_server(cs, args.server).confirm_resize()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_resize_revert(cs, args):
    """Revert a previous resize (and return to the previous VM)."""
    _find_server(cs, args.server).revert_resize()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    '--host',
    metavar='<host>',
    default=None,
    help=_('Destination host name.'),
    start_version='2.56')
@utils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the server migration progress until it completes.'))
def do_migrate(cs, args):
    """Migrate a server."""
    update_kwargs = {}
    if 'host' in args and args.host:
        update_kwargs['host'] = args.host

    server = _find_server(cs, args.server)
    server.migrate(**update_kwargs)

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'migrating',
                         ['active', 'verify_resize'])


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_pause(cs, args):
    """Pause a server."""
    _find_server(cs, args.server).pause()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_unpause(cs, args):
    """Unpause a server."""
    _find_server(cs, args.server).unpause()


@utils.arg(
    '--all-tenants',
    action='store_const',
    const=1,
    default=0,
    help=_('Stop server(s) in another tenant by name (Admin only).'))
@utils.arg(
    'server',
    metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
def do_stop(cs, args):
    """Stop the server(s)."""
    find_args = {'all_tenants': args.all_tenants}
    utils.do_action_on_many(
        lambda s: _find_server(cs, s, **find_args).stop(),
        args.server,
        _("Request to stop server %s has been accepted."),
        _("Unable to stop the specified server(s)."))


@utils.arg(
    '--all-tenants',
    action='store_const',
    const=1,
    default=0,
    help=_('Start server(s) in another tenant by name (Admin only).'))
@utils.arg(
    'server',
    metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
def do_start(cs, args):
    """Start the server(s)."""
    find_args = {'all_tenants': args.all_tenants}
    utils.do_action_on_many(
        lambda s: _find_server(cs, s, **find_args).start(),
        args.server,
        _("Request to start server %s has been accepted."),
        _("Unable to start the specified server(s)."))


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_lock(cs, args):
    """Lock a server. A normal (non-admin) user will not be able to execute
    actions on a locked server.
    """
    _find_server(cs, args.server).lock()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_unlock(cs, args):
    """Unlock a server."""
    _find_server(cs, args.server).unlock()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_suspend(cs, args):
    """Suspend a server."""
    _find_server(cs, args.server).suspend()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_resume(cs, args):
    """Resume a server."""
    _find_server(cs, args.server).resume()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    '--password',
    metavar='<password>',
    dest='password',
    help=_('The admin password to be set in the rescue environment.'))
@utils.arg(
    '--image',
    metavar='<image>',
    dest='image',
    help=_('The image to rescue with.'))
def do_rescue(cs, args):
    """Reboots a server into rescue mode, which starts the machine
    from either the initial image or a specified image, attaching the current
    boot disk as secondary.
    """
    kwargs = {}
    if args.image:
        kwargs['image'] = _find_image(cs, args.image)
    if args.password:
        kwargs['password'] = args.password
    utils.print_dict(_find_server(cs, args.server).rescue(**kwargs)[1])


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_unrescue(cs, args):
    """Restart the server from normal boot disk again."""
    _find_server(cs, args.server).unrescue()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_shelve(cs, args):
    """Shelve a server."""
    _find_server(cs, args.server).shelve()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_shelve_offload(cs, args):
    """Remove a shelved server from the compute node."""
    _find_server(cs, args.server).shelve_offload()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_unshelve(cs, args):
    """Unshelve a server."""
    _find_server(cs, args.server).unshelve()


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_diagnostics(cs, args):
    """Retrieve server diagnostics."""
    server = _find_server(cs, args.server)
    utils.print_dict(cs.servers.diagnostics(server)[1], wrap=80)


@utils.arg(
    'server', metavar='<server>',
    help=_('Name or ID of a server for which the network cache should '
           'be refreshed from neutron (Admin only).'))
def do_refresh_network(cs, args):
    """Refresh server network information."""
    server = _find_server(cs, args.server)
    cs.server_external_events.create([{'server_uuid': server.id,
                                       'name': 'network-changed'}])


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_set_password(cs, args):
    """
    Change the admin password for a server.
    """
    server = _find_server(cs, args.server)
    p1 = getpass.getpass('New password: ')
    p2 = getpass.getpass('Again: ')
    if p1 != p2:
        raise exceptions.CommandError(_("Passwords do not match."))
    server.change_password(p1)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('name', metavar='<name>', help=_('Name of snapshot.'))
@utils.arg(
    '--metadata',
    metavar="<key=value>",
    action='append',
    default=[],
    help=_("Record arbitrary key/value metadata to /meta_data.json "
           "on the metadata server. Can be specified multiple times."))
@utils.arg(
    '--show',
    dest='show',
    action="store_true",
    default=False,
    help=_('Print image info.'))
@utils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the snapshot progress and poll until image creation is '
           'complete.'))
def do_image_create(cs, args):
    """Create a new image by taking a snapshot of a running server."""
    server = _find_server(cs, args.server)
    meta = _meta_parsing(args.metadata) or None
    image_uuid = cs.servers.create_image(server, args.name, meta)

    if args.poll:
        _poll_for_status(cs.glance.find_image, image_uuid, 'snapshotting',
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

    if args.show:
        _print_image(_find_image(cs, image_uuid))


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('name', metavar='<name>', help=_('Name of the backup image.'))
@utils.arg(
    'backup_type', metavar='<backup-type>',
    help=_('The backup type, like "daily" or "weekly".'))
@utils.arg(
    'rotation', metavar='<rotation>',
    help=_('Int parameter representing how many backups to keep '
           'around.'))
def do_backup(cs, args):
    """Backup a server by creating a 'backup' type snapshot."""
    result = _find_server(cs, args.server).backup(args.name,
                                                  args.backup_type,
                                                  args.rotation)
    # Microversion >= 2.45 will return a DictWithMeta that has the image_id
    # in it for the backup snapshot image.
    if cs.api_version >= api_versions.APIVersion('2.45'):
        _print_image(_find_image(cs, result['image_id']))


@utils.arg(
    'server',
    metavar='<server>',
    help=_("Name or ID of server."))
@utils.arg(
    'action',
    metavar='<action>',
    choices=['set', 'delete'],
    help=_("Actions: 'set' or 'delete'."))
@utils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help=_('Metadata to set or delete (only key is necessary on delete).'))
def do_meta(cs, args):
    """Set or delete metadata on a server."""
    server = _find_server(cs, args.server)
    metadata = _extract_metadata(args)

    if args.action == 'set':
        cs.servers.set_meta(server, metadata)
    elif args.action == 'delete':
        cs.servers.delete_meta(server, sorted(metadata.keys(), reverse=True))


def _print_server(cs, args, server=None, wrap=0):
    # By default when searching via name we will do a
    # findall(name=blah) and due a REST /details which is not the same
    # as a .get() and doesn't get the information about flavors and
    # images. This fix it as we redo the call with the id which does a
    # .get() to get all information.
    if not server:
        server = _find_server(cs, args.server)

    minimal = getattr(args, "minimal", False)

    networks = server.networks
    info = server.to_dict()
    for network_label, address_list in networks.items():
        info['%s network' % network_label] = ', '.join(address_list)

    flavor = info.get('flavor', {})
    if cs.api_version >= api_versions.APIVersion('2.47'):
        # The "flavor" field is a JSON representation of a dict containing the
        # flavor information used at boot.
        if minimal:
            # To retain something similar to the previous behaviour, keep the
            # 'flavor' field name but just output the original name.
            info['flavor'] = flavor['original_name']
        else:
            # Replace the "flavor" field with individual namespaced fields.
            del info['flavor']
            for key in flavor.keys():
                info['flavor:' + key] = flavor[key]
    else:
        # Prior to microversion 2.47 we just have the ID of the flavor so we
        # need to retrieve the flavor information (which may have changed
        # since the instance was booted).
        flavor_id = flavor.get('id', '')
        if minimal:
            info['flavor'] = flavor_id
        else:
            try:
                info['flavor'] = '%s (%s)' % (_find_flavor(cs, flavor_id).name,
                                              flavor_id)
            except Exception:
                info['flavor'] = '%s (%s)' % (_("Flavor not found"), flavor_id)

    if 'security_groups' in info:
        # when we have multiple nics the info will include the
        # security groups N times where N == number of nics. Be nice
        # and only display it once.
        info['security_groups'] = ', '.join(
            sorted(set(group['name'] for group in info['security_groups'])))

    image = info.get('image', {})
    if image:
        image_id = image.get('id', '')
        if minimal:
            info['image'] = image_id
        else:
            try:
                info['image'] = '%s (%s)' % (_find_image(cs, image_id).name,
                                             image_id)
            except Exception:
                info['image'] = '%s (%s)' % (_("Image not found"), image_id)
    else:  # Booted from volume
        info['image'] = _("Attempt to boot from volume - no image supplied")

    info.pop('links', None)
    info.pop('addresses', None)

    utils.print_dict(info, wrap=wrap)


@utils.arg(
    '--minimal',
    dest='minimal',
    action="store_true",
    default=False,
    help=_('Skips flavor/image lookups when showing servers.'))
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    '--wrap', dest='wrap', metavar='<integer>', type=int, default=0,
    help=_('Wrap the output to a specified length, or 0 to disable.'))
def do_show(cs, args):
    """Show details about the given server."""
    _print_server(cs, args, wrap=args.wrap)


@utils.arg(
    '--all-tenants',
    action='store_const',
    const=1,
    default=0,
    help=_('Delete server(s) in another tenant by name (Admin only).'))
@utils.arg(
    'server', metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
def do_delete(cs, args):
    """Immediately shut down and delete specified server(s)."""
    find_args = {'all_tenants': args.all_tenants}
    utils.do_action_on_many(
        lambda s: _find_server(cs, s, **find_args).delete(),
        args.server,
        _("Request to delete server %s has been accepted."),
        _("Unable to delete the specified server(s)."))


def _find_server(cs, server, raise_if_notfound=True, **find_args):
    """Get a server by name or ID.

    :param cs: NovaClient's instance
    :param server: identifier of server
    :param raise_if_notfound: raise an exception if server is not found
    :param find_args: argument to search server
    """
    if raise_if_notfound:
        return utils.find_resource(cs.servers, server, **find_args)
    else:
        try:
            return utils.find_resource(cs.servers, server,
                                       wrap_exception=False)
        except exceptions.NoUniqueMatch as e:
            raise exceptions.CommandError(six.text_type(e))
        except exceptions.NotFound:
            # The server can be deleted
            return server


def _find_image(cs, image):
    """Get an image by name or ID."""
    try:
        return cs.glance.find_image(image)
    except (exceptions.NotFound, exceptions.NoUniqueMatch) as e:
        raise exceptions.CommandError(six.text_type(e))


def _find_flavor(cs, flavor):
    """Get a flavor by name, ID, or RAM size."""
    try:
        return utils.find_resource(cs.flavors, flavor, is_public=None)
    except exceptions.NotFound:
        return cs.flavors.find(ram=flavor)


def _find_network_id(cs, net_name):
    """Get unique network ID from network name from neutron"""
    try:
        return cs.neutron.find_network(net_name).id
    except (exceptions.NotFound, exceptions.NoUniqueMatch) as e:
        raise exceptions.CommandError(six.text_type(e))


def _print_volume(volume):
    utils.print_dict(volume.to_dict())


def _translate_availability_zone_keys(collection):
    _translate_keys(collection,
                    [('zoneName', 'name'), ('zoneState', 'status')])


def _translate_volume_attachments_keys(collection):
    _translate_keys(collection,
                    [('serverId', 'server_id'),
                     ('volumeId', 'volume_id')])


@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or ID of server.'))
@utils.arg(
    'volume',
    metavar='<volume>',
    help=_('ID of the volume to attach.'))
@utils.arg(
    'device', metavar='<device>', default=None, nargs='?',
    help=_('Name of the device e.g. /dev/vdb. '
           'Use "auto" for autoassign (if supported). '
           'Libvirt driver will use default device name.'))
@utils.arg(
    '--tag',
    metavar='<tag>',
    default=None,
    help=_('Tag for the attached volume.'),
    start_version="2.49")
def do_volume_attach(cs, args):
    """Attach a volume to a server."""
    if args.device == 'auto':
        args.device = None

    update_kwargs = {}
    if 'tag' in args and args.tag:
        update_kwargs['tag'] = args.tag

    volume = cs.volumes.create_server_volume(_find_server(cs, args.server).id,
                                             args.volume,
                                             args.device,
                                             **update_kwargs)
    _print_volume(volume)


@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or ID of server.'))
@utils.arg(
    'src_volume',
    metavar='<src_volid>',
    help=_('ID of the source (original) volume.'))
@utils.arg(
    'dest_volume',
    metavar='<dest_volid>',
    help=_('ID of the destination volume.'))
def do_volume_update(cs, args):
    """Update the attachment on the server.

    Migrates the data from an attached volume to the
    specified available volume and swaps out the active
    attachment to the new volume.
    """
    cs.volumes.update_server_volume(_find_server(cs, args.server).id,
                                    args.src_volume,
                                    args.dest_volume)


@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or ID of server.'))
@utils.arg(
    'attachment_id',
    metavar='<volume>',
    help=_('ID of the volume to detach.'))
def do_volume_detach(cs, args):
    """Detach a volume from a server."""
    cs.volumes.delete_server_volume(_find_server(cs, args.server).id,
                                    args.attachment_id)


@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or ID of server.'))
def do_volume_attachments(cs, args):
    """List all the volumes attached to a server."""
    volumes = cs.volumes.get_server_volumes(_find_server(cs, args.server).id)
    _translate_volume_attachments_keys(volumes)
    utils.print_list(volumes, ['ID', 'DEVICE', 'SERVER ID', 'VOLUME ID'])


@api_versions.wraps('2.0', '2.5')
def console_dict_accessor(cs, data):
    return data['console']


@api_versions.wraps('2.6')
def console_dict_accessor(cs, data):
    return data['remote_console']


class Console(object):
    def __init__(self, console_dict):
        self.type = console_dict['type']
        self.url = console_dict['url']


def print_console(cs, data):
    utils.print_list([Console(console_dict_accessor(cs, data))],
                     ['Type', 'Url'])


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'console_type',
    metavar='<console-type>',
    help=_('Type of vnc console ("novnc" or "xvpvnc").'))
def do_get_vnc_console(cs, args):
    """Get a vnc console to a server."""
    server = _find_server(cs, args.server)
    data = server.get_vnc_console(args.console_type)

    print_console(cs, data)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'console_type',
    metavar='<console-type>',
    help=_('Type of spice console ("spice-html5").'))
def do_get_spice_console(cs, args):
    """Get a spice console to a server."""
    server = _find_server(cs, args.server)
    data = server.get_spice_console(args.console_type)

    print_console(cs, data)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'console_type',
    metavar='<console-type>',
    help=_('Type of rdp console ("rdp-html5").'))
def do_get_rdp_console(cs, args):
    """Get a rdp console to a server."""
    server = _find_server(cs, args.server)
    data = server.get_rdp_console(args.console_type)

    print_console(cs, data)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    '--console-type',
    default='serial',
    help=_('Type of serial console, default="serial".'))
def do_get_serial_console(cs, args):
    """Get a serial console to a server."""
    if args.console_type not in ('serial',):
        raise exceptions.CommandError(
            _("Invalid parameter value for 'console_type', "
              "currently supported 'serial'."))

    server = _find_server(cs, args.server)
    data = server.get_serial_console(args.console_type)

    print_console(cs, data)


@api_versions.wraps('2.8')
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_get_mks_console(cs, args):
    """Get an MKS console to a server."""
    server = _find_server(cs, args.server)
    data = server.get_mks_console()

    print_console(cs, data)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'private_key',
    metavar='<private-key>',
    help=_('Private key (used locally to decrypt password) (Optional). '
           'When specified, the command displays the clear (decrypted) VM '
           'password. When not specified, the ciphered VM password is '
           'displayed.'),
    nargs='?',
    default=None)
def do_get_password(cs, args):
    """Get the admin password for a server. This operation calls the metadata
    service to query metadata information and does not read password
    information from the server itself.
    """
    server = _find_server(cs, args.server)
    data = server.get_password(args.private_key)
    print(data)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_clear_password(cs, args):
    """Clear the admin password for a server from the metadata server.
    This action does not actually change the instance server password.
    """
    server = _find_server(cs, args.server)
    server.clear_password()


def _print_floating_ip_list(floating_ips):
    convert = [('instance_id', 'server_id')]
    _translate_keys(floating_ips, convert)

    utils.print_list(floating_ips,
                     ['Id', 'IP', 'Server Id', 'Fixed IP', 'Pool'])


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    '--length',
    metavar='<length>',
    default=None,
    help=_('Length in lines to tail.'))
def do_console_log(cs, args):
    """Get console log output of a server."""
    server = _find_server(cs, args.server)
    data = server.get_console_output(length=args.length)

    if data and data[-1] != '\n':
        data += '\n'
    codecs.getwriter('utf-8')(sys.stdout).write(data)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('Name or ID of Security Group.'))
def do_add_secgroup(cs, args):
    """Add a Security Group to a server."""
    server = _find_server(cs, args.server)
    server.add_security_group(args.secgroup)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('Name of Security Group.'))
def do_remove_secgroup(cs, args):
    """Remove a Security Group from a server."""
    server = _find_server(cs, args.server)
    server.remove_security_group(args.secgroup)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_list_secgroup(cs, args):
    """List Security Group(s) of a server."""
    server = _find_server(cs, args.server)
    groups = server.list_security_group()
    _print_secgroups(groups)


def _print_secgroups(secgroups):
    utils.print_list(secgroups, ['Id', 'Name', 'Description'])


@api_versions.wraps("2.0", "2.1")
def _keypair_create(cs, args, name, pub_key):
    return cs.keypairs.create(name, pub_key)


@api_versions.wraps("2.2", "2.9")
def _keypair_create(cs, args, name, pub_key):
    return cs.keypairs.create(name, pub_key, key_type=args.key_type)


@api_versions.wraps("2.10")
def _keypair_create(cs, args, name, pub_key):
    return cs.keypairs.create(name, pub_key, key_type=args.key_type,
                              user_id=args.user)


@utils.arg('name', metavar='<name>', help=_('Name of key.'))
@utils.arg(
    '--pub-key',
    metavar='<pub-key>',
    default=None,
    help=_('Path to a public ssh key.'))
@utils.arg(
    '--key-type',
    metavar='<key-type>',
    default='ssh',
    help=_('Keypair type. Can be ssh or x509.'),
    start_version="2.2")
@utils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('ID of user to whom to add key-pair (Admin only).'),
    start_version="2.10")
def do_keypair_add(cs, args):
    """Create a new key pair for use with servers."""
    name = args.name
    pub_key = args.pub_key
    if pub_key:
        if pub_key == '-':
            pub_key = sys.stdin.read()
        else:
            try:
                with open(os.path.expanduser(pub_key)) as f:
                    pub_key = f.read()
            except IOError as e:
                raise exceptions.CommandError(
                    _("Can't open or read '%(key)s': %(exc)s")
                    % {'key': pub_key, 'exc': e}
                )

    keypair = _keypair_create(cs, args, name, pub_key)

    if not pub_key:
        private_key = keypair.private_key
        print(private_key)


@api_versions.wraps("2.0", "2.9")
@utils.arg('name', metavar='<name>', help=_('Keypair name to delete.'))
def do_keypair_delete(cs, args):
    """Delete keypair given by its name."""
    name = _find_keypair(cs, args.name)
    cs.keypairs.delete(name)


@api_versions.wraps("2.10")
@utils.arg('name', metavar='<name>', help=_('Keypair name to delete.'))
@utils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('ID of key-pair owner (Admin only).'))
def do_keypair_delete(cs, args):
    """Delete keypair given by its name."""
    cs.keypairs.delete(args.name, args.user)


@api_versions.wraps("2.0", "2.1")
def _get_keypairs_list_columns(cs, args):
    return ['Name', 'Fingerprint']


@api_versions.wraps("2.2")
def _get_keypairs_list_columns(cs, args):
    return ['Name', 'Type', 'Fingerprint']


@api_versions.wraps("2.0", "2.9")
def do_keypair_list(cs, args):
    """Print a list of keypairs for a user"""
    keypairs = cs.keypairs.list()
    columns = _get_keypairs_list_columns(cs, args)
    utils.print_list(keypairs, columns)


@api_versions.wraps("2.10", "2.34")
@utils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('List key-pairs of specified user ID (Admin only).'))
def do_keypair_list(cs, args):
    """Print a list of keypairs for a user"""
    keypairs = cs.keypairs.list(args.user)
    columns = _get_keypairs_list_columns(cs, args)
    utils.print_list(keypairs, columns)


@api_versions.wraps("2.35")
@utils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('List key-pairs of specified user ID (Admin only).'))
@utils.arg(
    '--marker',
    dest='marker',
    metavar='<marker>',
    default=None,
    help=_('The last keypair of the previous page; displays list of keypairs '
           'after "marker".'))
@utils.arg(
    '--limit',
    dest='limit',
    metavar='<limit>',
    type=int,
    default=None,
    help=_("Maximum number of keypairs to display. If limit is bigger than "
           "'CONF.api.max_limit' option of Nova API, limit "
           "'CONF.api.max_limit' will be used instead."))
def do_keypair_list(cs, args):
    """Print a list of keypairs for a user"""
    keypairs = cs.keypairs.list(args.user, args.marker, args.limit)
    columns = _get_keypairs_list_columns(cs, args)
    utils.print_list(keypairs, columns)


def _print_keypair(keypair):
    kp = keypair.to_dict()
    pk = kp.pop('public_key')
    utils.print_dict(kp)
    print(_("Public key: %s") % pk)


@api_versions.wraps("2.0", "2.9")
@utils.arg(
    'keypair',
    metavar='<keypair>',
    help=_("Name of keypair."))
def do_keypair_show(cs, args):
    """Show details about the given keypair."""
    keypair = _find_keypair(cs, args.keypair)
    _print_keypair(keypair)


@api_versions.wraps("2.10")
@utils.arg(
    'keypair',
    metavar='<keypair>',
    help=_("Name of keypair."))
@utils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('ID of key-pair owner (Admin only).'))
def do_keypair_show(cs, args):
    """Show details about the given keypair."""
    keypair = cs.keypairs.get(args.keypair, args.user)
    _print_keypair(keypair)


def _find_keypair(cs, keypair):
    """Get a keypair by name."""
    return utils.find_resource(cs.keypairs, keypair)


def _print_absolute_limits(limits):
    """Prints absolute limits."""
    class Limit(object):
        def __init__(self, name, used, max, other):
            self.name = name
            self.used = used
            self.max = max
            self.other = other

    limit_map = {
        'maxServerMeta': {'name': 'Server Meta', 'type': 'max'},
        'maxPersonality': {'name': 'Personality', 'type': 'max'},
        'maxPersonalitySize': {'name': 'Personality Size', 'type': 'max'},
        'maxImageMeta': {'name': 'ImageMeta', 'type': 'max'},
        'maxTotalKeypairs': {'name': 'Keypairs', 'type': 'max'},
        'totalCoresUsed': {'name': 'Cores', 'type': 'used'},
        'maxTotalCores': {'name': 'Cores', 'type': 'max'},
        'totalRAMUsed': {'name': 'RAM', 'type': 'used'},
        'maxTotalRAMSize': {'name': 'RAM', 'type': 'max'},
        'totalInstancesUsed': {'name': 'Instances', 'type': 'used'},
        'maxTotalInstances': {'name': 'Instances', 'type': 'max'},
        'totalFloatingIpsUsed': {'name': 'FloatingIps', 'type': 'used'},
        'maxTotalFloatingIps': {'name': 'FloatingIps', 'type': 'max'},
        'totalSecurityGroupsUsed': {'name': 'SecurityGroups', 'type': 'used'},
        'maxSecurityGroups': {'name': 'SecurityGroups', 'type': 'max'},
        'maxSecurityGroupRules': {'name': 'SecurityGroupRules', 'type': 'max'},
        'maxServerGroups': {'name': 'ServerGroups', 'type': 'max'},
        'totalServerGroupsUsed': {'name': 'ServerGroups', 'type': 'used'},
        'maxServerGroupMembers': {'name': 'ServerGroupMembers', 'type': 'max'},
    }

    max = {}
    used = {}
    other = {}
    limit_names = []
    columns = ['Name', 'Used', 'Max']
    for l in limits:
        map = limit_map.get(l.name, {'name': l.name, 'type': 'other'})
        name = map['name']
        if map['type'] == 'max':
            max[name] = l.value
        elif map['type'] == 'used':
            used[name] = l.value
        else:
            other[name] = l.value
            if 'Other' not in columns:
                columns.append('Other')
        if name not in limit_names:
            limit_names.append(name)

    limit_names.sort()

    limit_list = []
    for name in limit_names:
        l = Limit(name,
                  used.get(name, "-"),
                  max.get(name, "-"),
                  other.get(name, "-"))
        limit_list.append(l)

    utils.print_list(limit_list, columns)


def _print_rate_limits(limits):
    """print rate limits."""
    columns = ['Verb', 'URI', 'Value', 'Remain', 'Unit', 'Next_Available']
    utils.print_list(limits, columns)


@utils.arg(
    '--tenant',
    # nova db searches by project_id
    dest='tenant',
    metavar='<tenant>',
    nargs='?',
    help=_('Display information from single tenant (Admin only).'))
@utils.arg(
    '--reserved',
    dest='reserved',
    action='store_true',
    default=False,
    help=_('Include reservations count.'))
def do_limits(cs, args):
    """Print rate and absolute limits."""
    limits = cs.limits.get(args.reserved, args.tenant)
    _print_rate_limits(limits.rate)
    _print_absolute_limits(limits.absolute)


def _get_usage_marker(usage):
    marker = None
    if hasattr(usage, 'server_usages') and usage.server_usages:
        marker = usage.server_usages[-1]['instance_id']
    return marker


def _get_usage_list_marker(usage_list):
    marker = None
    if usage_list:
        marker = _get_usage_marker(usage_list[-1])
    return marker


def _merge_usage(usage, next_usage):
    usage.server_usages.extend(next_usage.server_usages)
    usage.total_hours += next_usage.total_hours
    usage.total_memory_mb_usage += next_usage.total_memory_mb_usage
    usage.total_vcpus_usage += next_usage.total_vcpus_usage
    usage.total_local_gb_usage += next_usage.total_local_gb_usage


def _merge_usage_list(usages, next_usage_list):
    for next_usage in next_usage_list:
        if next_usage.tenant_id in usages:
            _merge_usage(usages[next_usage.tenant_id], next_usage)
        else:
            usages[next_usage.tenant_id] = next_usage


@utils.arg(
    '--start',
    metavar='<start>',
    help=_('Usage range start date ex 2012-01-20. (default: 4 weeks ago)'),
    default=None)
@utils.arg(
    '--end',
    metavar='<end>',
    help=_('Usage range end date, ex 2012-01-20. (default: tomorrow)'),
    default=None)
def do_usage_list(cs, args):
    """List usage data for all tenants."""
    dateformat = "%Y-%m-%d"
    rows = ["Tenant ID", "Servers", "RAM MB-Hours", "CPU Hours",
            "Disk GiB-Hours"]

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
        simplerows = [x.lower().replace(" ", "_") for x in rows]

        setattr(u, simplerows[0], u.tenant_id)
        setattr(u, simplerows[1], "%d" % len(u.server_usages))
        setattr(u, simplerows[2], "%.2f" % u.total_memory_mb_usage)
        setattr(u, simplerows[3], "%.2f" % u.total_vcpus_usage)
        setattr(u, simplerows[4], "%.2f" % u.total_local_gb_usage)

    if cs.api_version < api_versions.APIVersion('2.40'):
        usage_list = cs.usage.list(start, end, detailed=True)
    else:
        # If the number of instances used to calculate the usage is greater
        # than CONF.api.max_limit, the usage will be split across multiple
        # requests and the responses will need to be merged back together.
        usages = collections.OrderedDict()
        usage_list = cs.usage.list(start, end, detailed=True)
        _merge_usage_list(usages, usage_list)
        marker = _get_usage_list_marker(usage_list)
        while marker:
            next_usage_list = cs.usage.list(
                start, end, detailed=True, marker=marker)
            marker = _get_usage_list_marker(next_usage_list)
            if marker:
                _merge_usage_list(usages, next_usage_list)
        usage_list = list(usages.values())

    print(_("Usage from %(start)s to %(end)s:") %
          {'start': start.strftime(dateformat),
           'end': end.strftime(dateformat)})

    for usage in usage_list:
        simplify_usage(usage)

    utils.print_list(usage_list, rows)


@utils.arg(
    '--start',
    metavar='<start>',
    help=_('Usage range start date ex 2012-01-20. (default: 4 weeks ago)'),
    default=None)
@utils.arg(
    '--end', metavar='<end>',
    help=_('Usage range end date, ex 2012-01-20. (default: tomorrow)'),
    default=None)
@utils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help=_('UUID of tenant to get usage for.'))
def do_usage(cs, args):
    """Show usage data for a single tenant."""
    dateformat = "%Y-%m-%d"
    rows = ["Servers", "RAM MB-Hours", "CPU Hours", "Disk GiB-Hours"]

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
        simplerows = [x.lower().replace(" ", "_") for x in rows]

        setattr(u, simplerows[0], "%d" % len(u.server_usages))
        setattr(u, simplerows[1], "%.2f" % u.total_memory_mb_usage)
        setattr(u, simplerows[2], "%.2f" % u.total_vcpus_usage)
        setattr(u, simplerows[3], "%.2f" % u.total_local_gb_usage)

    if args.tenant:
        tenant_id = args.tenant
    else:
        if isinstance(cs.client, client.SessionClient):
            auth = cs.client.auth
            tenant_id = auth.get_auth_ref(cs.client.session).project_id
        else:
            tenant_id = cs.client.tenant_id

    if cs.api_version < api_versions.APIVersion('2.40'):
        usage = cs.usage.get(tenant_id, start, end)
    else:
        # If the number of instances used to calculate the usage is greater
        # than CONF.api.max_limit, the usage will be split across multiple
        # requests and the responses will need to be merged back together.
        usage = cs.usage.get(tenant_id, start, end)
        marker = _get_usage_marker(usage)
        while marker:
            next_usage = cs.usage.get(tenant_id, start, end, marker=marker)
            marker = _get_usage_marker(next_usage)
            if marker:
                _merge_usage(usage, next_usage)

    print(_("Usage from %(start)s to %(end)s:") %
          {'start': start.strftime(dateformat),
           'end': end.strftime(dateformat)})

    if getattr(usage, 'total_vcpus_usage', None):
        simplify_usage(usage)
        utils.print_list([usage], rows)
    else:
        print(_('None'))


@utils.arg(
    '--hypervisor',
    metavar='<hypervisor>',
    default=None,
    help=_('Type of hypervisor.'))
def do_agent_list(cs, args):
    """List all builds."""
    result = cs.agents.list(args.hypervisor)
    columns = ["Agent_id", "Hypervisor", "OS", "Architecture", "Version",
               'Md5hash', 'Url']
    utils.print_list(result, columns)


@utils.arg('os', metavar='<os>', help=_('Type of OS.'))
@utils.arg(
    'architecture',
    metavar='<architecture>',
    help=_('Type of architecture.'))
@utils.arg('version', metavar='<version>', help=_('Version.'))
@utils.arg('url', metavar='<url>', help=_('URL.'))
@utils.arg('md5hash', metavar='<md5hash>', help=_('MD5 hash.'))
@utils.arg(
    'hypervisor',
    metavar='<hypervisor>',
    default='xen',
    help=_('Type of hypervisor.'))
def do_agent_create(cs, args):
    """Create new agent build."""
    result = cs.agents.create(args.os, args.architecture,
                              args.version, args.url,
                              args.md5hash, args.hypervisor)
    utils.print_dict(result.to_dict())


@utils.arg('id', metavar='<id>', help=_('ID of the agent-build.'))
def do_agent_delete(cs, args):
    """Delete existing agent build."""
    cs.agents.delete(args.id)


@utils.arg('id', metavar='<id>', help=_('ID of the agent-build.'))
@utils.arg('version', metavar='<version>', help=_('Version.'))
@utils.arg('url', metavar='<url>', help=_('URL'))
@utils.arg('md5hash', metavar='<md5hash>', help=_('MD5 hash.'))
def do_agent_modify(cs, args):
    """Modify existing agent build."""
    result = cs.agents.update(args.id, args.version,
                              args.url, args.md5hash)
    utils.print_dict(result.to_dict())


def _find_aggregate(cs, aggregate):
    """Get an aggregate by name or ID."""
    return utils.find_resource(cs.aggregates, aggregate)


def do_aggregate_list(cs, args):
    """Print a list of all aggregates."""
    aggregates = cs.aggregates.list()
    columns = ['Id', 'Name', 'Availability Zone']
    if cs.api_version >= api_versions.APIVersion('2.41'):
        columns.append('UUID')
    utils.print_list(aggregates, columns)


@utils.arg('name', metavar='<name>', help=_('Name of aggregate.'))
@utils.arg(
    'availability_zone',
    metavar='<availability-zone>',
    default=None,
    nargs='?',
    help=_('The availability zone of the aggregate (optional).'))
def do_aggregate_create(cs, args):
    """Create a new aggregate with the specified details."""
    aggregate = cs.aggregates.create(args.name, args.availability_zone)
    _print_aggregate_details(cs, aggregate)


@utils.arg(
    'aggregate',
    metavar='<aggregate>',
    help=_('Name or ID of aggregate to delete.'))
def do_aggregate_delete(cs, args):
    """Delete the aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    cs.aggregates.delete(aggregate)
    print(_("Aggregate %s has been successfully deleted.") % aggregate.id)


@utils.arg(
    'aggregate',
    metavar='<aggregate>',
    help=_('Name or ID of aggregate to update.'))
@utils.arg(
    '--name',
    metavar='<name>',
    dest='name',
    help=_('New name for aggregate.'))
@utils.arg(
    '--availability-zone',
    metavar='<availability-zone>',
    dest='availability_zone',
    help=_('New availability zone for aggregate.'))
def do_aggregate_update(cs, args):
    """Update the aggregate's name and optionally availability zone."""
    aggregate = _find_aggregate(cs, args.aggregate)
    updates = {}
    if args.name:
        updates["name"] = args.name
    if args.availability_zone:
        updates["availability_zone"] = args.availability_zone

    if not updates:
        raise exceptions.CommandError(_(
            "Either '--name <name>' or '--availability-zone "
            "<availability-zone>' must be specified."))

    aggregate = cs.aggregates.update(aggregate.id, updates)
    print(_("Aggregate %s has been successfully updated.") % aggregate.id)
    _print_aggregate_details(cs, aggregate)


@utils.arg(
    'aggregate', metavar='<aggregate>',
    help=_('Name or ID of aggregate to update.'))
@utils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help=_('Metadata to add/update to aggregate. '
           'Specify only the key to delete a metadata item.'))
def do_aggregate_set_metadata(cs, args):
    """Update the metadata associated with the aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    metadata = _extract_metadata(args)
    currentmetadata = getattr(aggregate, 'metadata', {})
    if set(metadata.items()) & set(currentmetadata.items()):
        raise exceptions.CommandError(_("metadata already exists"))
    for key, value in metadata.items():
        if value is None and key not in currentmetadata:
            raise exceptions.CommandError(_("metadata key %s does not exist"
                                          " hence can not be deleted")
                                          % key)
    aggregate = cs.aggregates.set_metadata(aggregate.id, metadata)
    print(_("Metadata has been successfully updated for aggregate %s.") %
          aggregate.id)
    _print_aggregate_details(cs, aggregate)


@utils.arg(
    'aggregate', metavar='<aggregate>',
    help=_('Name or ID of aggregate.'))
@utils.arg(
    'host', metavar='<host>',
    help=_('The host to add to the aggregate.'))
def do_aggregate_add_host(cs, args):
    """Add the host to the specified aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    aggregate = cs.aggregates.add_host(aggregate.id, args.host)
    print(_("Host %(host)s has been successfully added for aggregate "
            "%(aggregate_id)s ") % {'host': args.host,
                                    'aggregate_id': aggregate.id})
    _print_aggregate_details(cs, aggregate)


@utils.arg(
    'aggregate', metavar='<aggregate>',
    help=_('Name or ID of aggregate.'))
@utils.arg(
    'host', metavar='<host>',
    help=_('The host to remove from the aggregate.'))
def do_aggregate_remove_host(cs, args):
    """Remove the specified host from the specified aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    aggregate = cs.aggregates.remove_host(aggregate.id, args.host)
    print(_("Host %(host)s has been successfully removed from aggregate "
            "%(aggregate_id)s ") % {'host': args.host,
                                    'aggregate_id': aggregate.id})
    _print_aggregate_details(cs, aggregate)


@utils.arg(
    'aggregate', metavar='<aggregate>',
    help=_('Name or ID of aggregate.'))
def do_aggregate_show(cs, args):
    """Show details of the specified aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    _print_aggregate_details(cs, aggregate)


def _print_aggregate_details(cs, aggregate):
    columns = ['Id', 'Name', 'Availability Zone', 'Hosts', 'Metadata']
    if cs.api_version >= api_versions.APIVersion('2.41'):
        columns.append('UUID')

    def parser_metadata(fields):
        return utils.pretty_choice_dict(getattr(fields, 'metadata', {}) or {})

    def parser_hosts(fields):
        return utils.pretty_choice_list(getattr(fields, 'hosts', []))

    formatters = {
        'Metadata': parser_metadata,
        'Hosts': parser_hosts,
    }
    utils.print_list([aggregate], columns, formatters=formatters)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'host', metavar='<host>', default=None, nargs='?',
    help=_('Destination host name.'))
@utils.arg(
    '--block-migrate',
    action='store_true',
    dest='block_migrate',
    default=False,
    help=_('True in case of block_migration. (Default=False:live_migration)'),
    start_version="2.0", end_version="2.24")
@utils.arg(
    '--block-migrate',
    action='store_true',
    dest='block_migrate',
    default="auto",
    help=_('True in case of block_migration. (Default=auto:live_migration)'),
    start_version="2.25")
@utils.arg(
    '--disk-over-commit',
    action='store_true',
    dest='disk_over_commit',
    default=False,
    help=_('Allow overcommit. (Default=False)'),
    start_version="2.0", end_version="2.24")
@utils.arg(
    '--force',
    dest='force',
    action='store_true',
    default=False,
    help=_('Force to not verify the scheduler if a host is provided.'),
    start_version='2.30')
def do_live_migration(cs, args):
    """Migrate running server to a new machine."""

    update_kwargs = {}
    if 'disk_over_commit' in args:
        update_kwargs['disk_over_commit'] = args.disk_over_commit
    if 'force' in args and args.force:
        update_kwargs['force'] = args.force

    _find_server(cs, args.server).live_migrate(args.host, args.block_migrate,
                                               **update_kwargs)


@api_versions.wraps("2.22")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('migration', metavar='<migration>', help=_('ID of migration.'))
def do_live_migration_force_complete(cs, args):
    """Force on-going live migration to complete."""
    server = _find_server(cs, args.server)
    cs.server_migrations.live_migrate_force_complete(server, args.migration)


@api_versions.wraps("2.23")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_server_migration_list(cs, args):
    """Get the migrations list of specified server."""
    server = _find_server(cs, args.server)
    migrations = cs.server_migrations.list(server)

    fields = ['Id', 'Source Node', 'Dest Node', 'Source Compute',
              'Dest Compute', 'Dest Host', 'Status', 'Server UUID',
              'Created At', 'Updated At']

    format_name = ["Total Memory Bytes", "Processed Memory Bytes",
                   "Remaining Memory Bytes", "Total Disk Bytes",
                   "Processed Disk Bytes", "Remaining Disk Bytes"]

    format_key = ["memory_total_bytes", "memory_processed_bytes",
                  "memory_remaining_bytes", "disk_total_bytes",
                  "disk_processed_bytes", "disk_remaining_bytes"]

    formatters = map(lambda field: utils.make_field_formatter(field)[1],
                     format_key)
    formatters = dict(zip(format_name, formatters))

    utils.print_list(migrations, fields + format_name, formatters)


@api_versions.wraps("2.23")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('migration', metavar='<migration>', help=_('ID of migration.'))
def do_server_migration_show(cs, args):
    """Get the migration of specified server."""
    server = _find_server(cs, args.server)
    migration = cs.server_migrations.get(server, args.migration)
    utils.print_dict(migration.to_dict())


@api_versions.wraps("2.24")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('migration', metavar='<migration>', help=_('ID of migration.'))
def do_live_migration_abort(cs, args):
    """Abort an on-going live migration."""
    server = _find_server(cs, args.server)
    cs.server_migrations.live_migration_abort(server, args.migration)


@utils.arg(
    '--all-tenants',
    action='store_const',
    const=1,
    default=0,
    help=_('Reset state server(s) in another tenant by name (Admin only).'))
@utils.arg(
    'server', metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
@utils.arg(
    '--active', action='store_const', dest='state',
    default='error', const='active',
    help=_('Request the server be reset to "active" state instead '
           'of "error" state (the default).'))
def do_reset_state(cs, args):
    """Reset the state of a server."""
    failure_flag = False
    find_args = {'all_tenants': args.all_tenants}

    for server in args.server:
        try:
            _find_server(cs, server, **find_args).reset_state(args.state)
            msg = "Reset state for server %s succeeded; new state is %s"
            print(msg % (server, args.state))
        except Exception as e:
            failure_flag = True
            msg = "Reset state for server %s failed: %s" % (server, e)
            print(msg)

    if failure_flag:
        msg = "Unable to reset the state for the specified server(s)."
        raise exceptions.CommandError(msg)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_reset_network(cs, args):
    """Reset network of a server."""
    _find_server(cs, args.server).reset_network()


@utils.arg(
    '--host',
    metavar='<hostname>',
    default=None,
    help=_('Name of host.'))
@utils.arg(
    '--binary',
    metavar='<binary>',
    default=None,
    help=_('Service binary.'))
def do_service_list(cs, args):
    """Show a list of all running services. Filter by host & binary."""
    result = cs.services.list(host=args.host, binary=args.binary)
    columns = ["Id", "Binary", "Host", "Zone", "Status",
               "State", "Updated_at", "Disabled Reason"]
    if cs.api_version >= api_versions.APIVersion('2.11'):
        columns.append("Forced down")

    utils.print_list(result, columns)


# Before microversion 2.53, the service was identified using it's host/binary
# values.
@api_versions.wraps('2.0', '2.52')
@utils.arg('host', metavar='<hostname>', help=_('Name of host.'))
def do_service_enable(cs, args):
    """Enable the service."""
    result = cs.services.enable(args.host, 'nova-compute')
    utils.print_list([result], ['Host', 'Binary', 'Status'])


# Starting in microversion 2.53, the service is identified by UUID ID.
@api_versions.wraps('2.53')
@utils.arg('id', metavar='<id>', help=_('ID of the service as a UUID.'))
def do_service_enable(cs, args):
    """Enable the service."""
    result = cs.services.enable(args.id)
    utils.print_list([result], ['ID', 'Host', 'Binary', 'Status'])


# Before microversion 2.53, the service was identified using it's host/binary
# values.
@api_versions.wraps('2.0', '2.52')
@utils.arg('host', metavar='<hostname>', help=_('Name of host.'))
@utils.arg(
    '--reason',
    metavar='<reason>',
    help=_('Reason for disabling service.'))
def do_service_disable(cs, args):
    """Disable the service."""
    if args.reason:
        result = cs.services.disable_log_reason(args.host, 'nova-compute',
                                                args.reason)
        utils.print_list([result], ['Host', 'Binary', 'Status',
                         'Disabled Reason'])
    else:
        result = cs.services.disable(args.host, 'nova-compute')
        utils.print_list([result], ['Host', 'Binary', 'Status'])


# Starting in microversion 2.53, the service is identified by UUID ID.
@api_versions.wraps('2.53')
@utils.arg('id', metavar='<id>', help=_('ID of the service as a UUID.'))
@utils.arg(
    '--reason',
    metavar='<reason>',
    help=_('Reason for disabling the service.'))
def do_service_disable(cs, args):
    """Disable the service."""
    if args.reason:
        result = cs.services.disable_log_reason(args.id, args.reason)
        utils.print_list(
            [result], ['ID', 'Host', 'Binary', 'Status', 'Disabled Reason'])
    else:
        result = cs.services.disable(args.id)
        utils.print_list([result], ['ID', 'Host', 'Binary', 'Status'])


# Before microversion 2.53, the service was identified using it's host/binary
# values.
@api_versions.wraps("2.11", "2.52")
@utils.arg('host', metavar='<hostname>', help=_('Name of host.'))
@utils.arg(
    '--unset',
    dest='force_down',
    help=_("Unset the force state down of service."),
    action='store_false',
    default=True)
def do_service_force_down(cs, args):
    """Force service to down."""
    result = cs.services.force_down(args.host, 'nova-compute', args.force_down)
    utils.print_list([result], ['Host', 'Binary', 'Forced down'])


# Starting in microversion 2.53, the service is identified by UUID ID.
@api_versions.wraps('2.53')
@utils.arg('id', metavar='<id>', help=_('ID of the service as a UUID.'))
@utils.arg(
    '--unset',
    dest='force_down',
    help=_("Unset the forced_down state of the service."),
    action='store_false',
    default=True)
def do_service_force_down(cs, args):
    """Force service to down."""
    result = cs.services.force_down(args.id, args.force_down)
    utils.print_list([result], ['ID', 'Host', 'Binary', 'Forced down'])


# Before microversion 2.53, the service was identified using it's host/binary
# values.
@api_versions.wraps('2.0', '2.52')
@utils.arg('id', metavar='<id>',
           help=_('ID of service as an integer. Note that this may not '
                  'uniquely identify a service in a multi-cell deployment.'))
def do_service_delete(cs, args):
    """Delete the service by integer ID."""
    cs.services.delete(args.id)


# Starting in microversion 2.53, the service is identified by UUID ID.
@api_versions.wraps('2.53')
@utils.arg('id', metavar='<id>', help=_('ID of service as a UUID.'))
def do_service_delete(cs, args):
    """Delete the service by UUID ID."""
    cs.services.delete(args.id)


def _find_hypervisor(cs, hypervisor):
    """Get a hypervisor by name or ID."""
    return utils.find_resource(cs.hypervisors, hypervisor)


def _do_hypervisor_list(cs, matching=None, limit=None, marker=None):
    columns = ['ID', 'Hypervisor hostname', 'State', 'Status']
    if matching:
        utils.print_list(cs.hypervisors.search(matching), columns)
    else:
        params = {}
        if limit is not None:
            params['limit'] = limit
        if marker is not None:
            params['marker'] = marker
        # Since we're not outputting detail data, choose
        # detailed=False for server-side efficiency
        utils.print_list(cs.hypervisors.list(False, **params), columns)


@api_versions.wraps("2.0", "2.32")
@utils.arg(
    '--matching',
    metavar='<hostname>',
    default=None,
    help=_('List hypervisors matching the given <hostname> (or pattern).'))
def do_hypervisor_list(cs, args):
    """List hypervisors."""
    _do_hypervisor_list(cs, matching=args.matching)


@api_versions.wraps("2.33")
@utils.arg(
    '--matching',
    metavar='<hostname>',
    default=None,
    help=_('List hypervisors matching the given <hostname> (or pattern). '
           'If matching is used limit and marker options will be ignored.'))
@utils.arg(
    '--marker',
    dest='marker',
    metavar='<marker>',
    default=None,
    help=_('The last hypervisor of the previous page; displays list of '
           'hypervisors after "marker".'))
@utils.arg(
    '--limit',
    dest='limit',
    metavar='<limit>',
    type=int,
    default=None,
    help=_("Maximum number of hypervisors to display. If limit is bigger than "
           "'CONF.api.max_limit' option of Nova API, limit "
           "'CONF.api.max_limit' will be used instead."))
def do_hypervisor_list(cs, args):
    """List hypervisors."""
    _do_hypervisor_list(
        cs, matching=args.matching, limit=args.limit, marker=args.marker)


@utils.arg(
    'hostname',
    metavar='<hostname>',
    help=_('The hypervisor hostname (or pattern) to search for.'))
def do_hypervisor_servers(cs, args):
    """List servers belonging to specific hypervisors."""
    hypers = cs.hypervisors.search(args.hostname, servers=True)

    class InstanceOnHyper(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    # Massage the result into a list to be displayed
    instances = []
    for hyper in hypers:
        hyper_host = hyper.hypervisor_hostname
        hyper_id = hyper.id
        if hasattr(hyper, 'servers'):
            instances.extend([InstanceOnHyper(id=serv['uuid'],
                                              name=serv['name'],
                                              hypervisor_hostname=hyper_host,
                                              hypervisor_id=hyper_id)
                              for serv in hyper.servers])

    # Output the data
    utils.print_list(instances, ['ID', 'Name', 'Hypervisor ID',
                                 'Hypervisor Hostname'])


@utils.arg(
    'hypervisor',
    metavar='<hypervisor>',
    help=_('Name or ID of the hypervisor. Starting with microversion 2.53 '
           'the ID must be a UUID.'))
@utils.arg(
    '--wrap', dest='wrap', metavar='<integer>', default=40,
    help=_('Wrap the output to a specified length. '
           'Default is 40 or 0 to disable'))
def do_hypervisor_show(cs, args):
    """Display the details of the specified hypervisor."""
    hyper = _find_hypervisor(cs, args.hypervisor)
    utils.print_dict(utils.flatten_dict(hyper.to_dict()), wrap=int(args.wrap))


@utils.arg(
    'hypervisor',
    metavar='<hypervisor>',
    help=_('Name or ID of the hypervisor. Starting with microversion 2.53 '
           'the ID must be a UUID.'))
def do_hypervisor_uptime(cs, args):
    """Display the uptime of the specified hypervisor."""
    hyper = _find_hypervisor(cs, args.hypervisor)
    hyper = cs.hypervisors.uptime(hyper)

    # Output the uptime information
    utils.print_dict(hyper.to_dict())


def do_hypervisor_stats(cs, args):
    """Get hypervisor statistics over all compute nodes."""
    stats = cs.hypervisor_stats.statistics()
    utils.print_dict(stats.to_dict())


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    '--port',
    dest='port',
    action='store',
    type=int,
    default=22,
    help=_('Optional flag to indicate which port to use for ssh. '
           '(Default=22)'))
@utils.arg(
    '--private',
    dest='private',
    action='store_true',
    default=False,
    help=argparse.SUPPRESS)
@utils.arg(
    '--address-type',
    dest='address_type',
    action='store',
    type=str,
    default='floating',
    help=_('Optional flag to indicate which IP type to use. Possible values  '
           'includes fixed and floating (the Default).'))
@utils.arg(
    '--network', metavar='<network>',
    help=_('Network to use for the ssh.'), default=None)
@utils.arg(
    '--ipv6',
    dest='ipv6',
    action='store_true',
    default=False,
    help=_('Optional flag to indicate whether to use an IPv6 address '
           'attached to a server. (Defaults to IPv4 address)'))
@utils.arg(
    '--login', metavar='<login>', help=_('Login to use.'),
    default="root")
@utils.arg(
    '-i', '--identity',
    dest='identity',
    help=_('Private key file, same as the -i option to the ssh command.'),
    default='')
@utils.arg(
    '--extra-opts',
    dest='extra',
    help=_('Extra options to pass to ssh. see: man ssh.'),
    default='')
def do_ssh(cs, args):
    """SSH into a server."""
    if '@' in args.server:
        user, server = args.server.split('@', 1)
        args.login = user
        args.server = server

    addresses = _find_server(cs, args.server).addresses
    address_type = "fixed" if args.private else args.address_type
    version = 6 if args.ipv6 else 4
    pretty_version = 'IPv%d' % version

    # Select the network to use.
    if args.network:
        network_addresses = addresses.get(args.network)
        if not network_addresses:
            msg = _("Server '%(server)s' is not attached to network "
                    "'%(network)s'")
            raise exceptions.ResourceNotFound(
                msg % {'server': args.server, 'network': args.network})
    else:
        if len(addresses) > 1:
            msg = _("Server '%(server)s' is attached to more than one network."
                    " Please pick the network to use.")
            raise exceptions.CommandError(msg % {'server': args.server})
        elif not addresses:
            msg = _("Server '%(server)s' is not attached to any network.")
            raise exceptions.CommandError(msg % {'server': args.server})
        else:
            network_addresses = list(addresses.values())[0]

    # Select the address in the selected network.
    # If the extension is not present, we assume the address to be floating.
    match = lambda addr: all((
        addr.get('version') == version,
        addr.get('OS-EXT-IPS:type', 'floating') == address_type))
    matching_addresses = [address.get('addr')
                          for address in network_addresses if match(address)]
    if not any(matching_addresses):
        msg = _("No address that would match network '%(network)s'"
                " and type '%(address_type)s' of version %(pretty_version)s "
                "has been found for server '%(server)s'.")
        raise exceptions.ResourceNotFound(msg % {
            'network': args.network, 'address_type': address_type,
            'pretty_version': pretty_version, 'server': args.server})
    elif len(matching_addresses) > 1:
        msg = _("More than one %(pretty_version)s %(address_type)s address "
                "found.")
        raise exceptions.CommandError(msg % {'pretty_version': pretty_version,
                                             'address_type': address_type})
    else:
        ip_address = matching_addresses[0]

    identity = '-i %s' % args.identity if len(args.identity) else ''

    cmd = "ssh -%d -p%d %s %s@%s %s" % (version, args.port, identity,
                                        args.login, ip_address, args.extra)
    logger.debug("Executing cmd '%s'", cmd)
    os.system(cmd)


# NOTE(mriedem): In the 2.50 microversion, the os-quota-class-sets API
# will return the server_groups and server_group_members, but no longer
# return floating_ips, fixed_ips, security_groups or security_group_members
# as those are deprecated as networking service proxies and/or because
# nova-network is deprecated. Similar to the 2.36 microversion.
# NOTE(mriedem): In the 2.57 microversion, the os-quota-sets and
# os-quota-class-sets APIs will no longer return injected_files,
# injected_file_content_bytes or injected_file_content_bytes since personality
# files (file injection) is deprecated starting with v2.57.
_quota_resources = ['instances', 'cores', 'ram',
                    'floating_ips', 'fixed_ips', 'metadata_items',
                    'injected_files', 'injected_file_content_bytes',
                    'injected_file_path_bytes', 'key_pairs',
                    'security_groups', 'security_group_rules',
                    'server_groups', 'server_group_members']


def _quota_show(quotas):
    class FormattedQuota(object):
        def __init__(self, key, value):
            setattr(self, 'quota', key)
            setattr(self, 'limit', value)

    quota_list = []
    for resource in _quota_resources:
        try:
            quota = FormattedQuota(resource, getattr(quotas, resource))
            quota_list.append(quota)
        except AttributeError:
            pass
    columns = ['Quota', 'Limit']
    utils.print_list(quota_list, columns)


def _quota_update(manager, identifier, args):
    updates = {}
    for resource in _quota_resources:
        val = getattr(args, resource, None)
        if val is not None:
            updates[resource] = val

    if updates:
        # default value of force is None to make sure this client
        # will be compatible with old nova server
        force_update = getattr(args, 'force', None)
        user_id = getattr(args, 'user', None)
        if isinstance(manager, quotas.QuotaSetManager):
            manager.update(identifier, force=force_update, user_id=user_id,
                           **updates)
        else:
            manager.update(identifier, **updates)


@utils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help=_('ID of tenant to list the quotas for.'))
@utils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('ID of user to list the quotas for.'))
@utils.arg(
    '--detail',
    action='store_true',
    default=False,
    help=_('Show detailed info (limit, reserved, in-use).'))
def do_quota_show(cs, args):
    """List the quotas for a tenant/user."""

    if args.tenant:
        project_id = args.tenant
    elif isinstance(cs.client, client.SessionClient):
        auth = cs.client.auth
        project_id = auth.get_auth_ref(cs.client.session).project_id
    else:
        project_id = cs.client.tenant_id

    _quota_show(cs.quotas.get(project_id, user_id=args.user,
                              detail=args.detail))


@utils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help=_('ID of tenant to list the default quotas for.'))
def do_quota_defaults(cs, args):
    """List the default quotas for a tenant."""

    if args.tenant:
        project_id = args.tenant
    elif isinstance(cs.client, client.SessionClient):
        auth = cs.client.auth
        project_id = auth.get_auth_ref(cs.client.session).project_id
    else:
        project_id = cs.client.tenant_id

    _quota_show(cs.quotas.defaults(project_id))


@api_versions.wraps("2.0", "2.35")
@utils.arg(
    'tenant',
    metavar='<tenant-id>',
    help=_('ID of tenant to set the quotas for.'))
@utils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('ID of user to set the quotas for.'))
@utils.arg(
    '--instances',
    metavar='<instances>',
    type=int, default=None,
    help=_('New value for the "instances" quota.'))
@utils.arg(
    '--cores',
    metavar='<cores>',
    type=int, default=None,
    help=_('New value for the "cores" quota.'))
@utils.arg(
    '--ram',
    metavar='<ram>',
    type=int, default=None,
    help=_('New value for the "ram" quota.'))
@utils.arg(
    '--floating-ips',
    metavar='<floating-ips>',
    type=int,
    default=None,
    action=shell.DeprecatedAction,
    help=_('New value for the "floating-ips" quota.'))
@utils.arg(
    '--fixed-ips',
    metavar='<fixed-ips>',
    type=int,
    default=None,
    action=shell.DeprecatedAction,
    help=_('New value for the "fixed-ips" quota.'))
@utils.arg(
    '--metadata-items',
    metavar='<metadata-items>',
    type=int,
    default=None,
    help=_('New value for the "metadata-items" quota.'))
@utils.arg(
    '--injected-files',
    metavar='<injected-files>',
    type=int,
    default=None,
    help=_('New value for the "injected-files" quota.'))
@utils.arg(
    '--injected-file-content-bytes',
    metavar='<injected-file-content-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-content-bytes" quota.'))
@utils.arg(
    '--injected-file-path-bytes',
    metavar='<injected-file-path-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-path-bytes" quota.'))
@utils.arg(
    '--key-pairs',
    metavar='<key-pairs>',
    type=int,
    default=None,
    help=_('New value for the "key-pairs" quota.'))
@utils.arg(
    '--security-groups',
    metavar='<security-groups>',
    type=int,
    default=None,
    action=shell.DeprecatedAction,
    help=_('New value for the "security-groups" quota.'))
@utils.arg(
    '--security-group-rules',
    metavar='<security-group-rules>',
    type=int,
    default=None,
    action=shell.DeprecatedAction,
    help=_('New value for the "security-group-rules" quota.'))
@utils.arg(
    '--server-groups',
    metavar='<server-groups>',
    type=int,
    default=None,
    help=_('New value for the "server-groups" quota.'))
@utils.arg(
    '--server-group-members',
    metavar='<server-group-members>',
    type=int,
    default=None,
    help=_('New value for the "server-group-members" quota.'))
@utils.arg(
    '--force',
    dest='force',
    action="store_true",
    default=None,
    help=_('Whether force update the quota even if the already used and '
           'reserved exceeds the new quota.'))
def do_quota_update(cs, args):
    """Update the quotas for a tenant/user."""

    _quota_update(cs.quotas, args.tenant, args)


# 2.36 does not support updating quota for floating IPs, fixed IPs, security
# groups or security group rules.
# 2.57 does not support updating injected_file* quotas.
@api_versions.wraps("2.36")
@utils.arg(
    'tenant',
    metavar='<tenant-id>',
    help=_('ID of tenant to set the quotas for.'))
@utils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('ID of user to set the quotas for.'))
@utils.arg(
    '--instances',
    metavar='<instances>',
    type=int, default=None,
    help=_('New value for the "instances" quota.'))
@utils.arg(
    '--cores',
    metavar='<cores>',
    type=int, default=None,
    help=_('New value for the "cores" quota.'))
@utils.arg(
    '--ram',
    metavar='<ram>',
    type=int, default=None,
    help=_('New value for the "ram" quota.'))
@utils.arg(
    '--metadata-items',
    metavar='<metadata-items>',
    type=int,
    default=None,
    help=_('New value for the "metadata-items" quota.'))
@utils.arg(
    '--injected-files',
    metavar='<injected-files>',
    type=int,
    default=None,
    help=_('New value for the "injected-files" quota.'),
    start_version='2.36', end_version='2.56')
@utils.arg(
    '--injected-file-content-bytes',
    metavar='<injected-file-content-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-content-bytes" quota.'),
    start_version='2.36', end_version='2.56')
@utils.arg(
    '--injected-file-path-bytes',
    metavar='<injected-file-path-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-path-bytes" quota.'),
    start_version='2.36', end_version='2.56')
@utils.arg(
    '--key-pairs',
    metavar='<key-pairs>',
    type=int,
    default=None,
    help=_('New value for the "key-pairs" quota.'))
@utils.arg(
    '--server-groups',
    metavar='<server-groups>',
    type=int,
    default=None,
    help=_('New value for the "server-groups" quota.'))
@utils.arg(
    '--server-group-members',
    metavar='<server-group-members>',
    type=int,
    default=None,
    help=_('New value for the "server-group-members" quota.'))
@utils.arg(
    '--force',
    dest='force',
    action="store_true",
    default=None,
    help=_('Whether force update the quota even if the already used and '
           'reserved exceeds the new quota.'))
def do_quota_update(cs, args):
    """Update the quotas for a tenant/user."""

    _quota_update(cs.quotas, args.tenant, args)


@utils.arg(
    '--tenant',
    metavar='<tenant-id>',
    required=True,
    help=_('ID of tenant to delete quota for.'))
@utils.arg(
    '--user',
    metavar='<user-id>',
    help=_('ID of user to delete quota for.'))
def do_quota_delete(cs, args):
    """Delete quota for a tenant/user so their quota will Revert
       back to default.
    """

    cs.quotas.delete(args.tenant, user_id=args.user)


@utils.arg(
    'class_name',
    metavar='<class>',
    help=_('Name of quota class to list the quotas for.'))
def do_quota_class_show(cs, args):
    """List the quotas for a quota class."""

    _quota_show(cs.quota_classes.get(args.class_name))


@api_versions.wraps("2.0", "2.49")
@utils.arg(
    'class_name',
    metavar='<class>',
    help=_('Name of quota class to set the quotas for.'))
@utils.arg(
    '--instances',
    metavar='<instances>',
    type=int, default=None,
    help=_('New value for the "instances" quota.'))
@utils.arg(
    '--cores',
    metavar='<cores>',
    type=int, default=None,
    help=_('New value for the "cores" quota.'))
@utils.arg(
    '--ram',
    metavar='<ram>',
    type=int, default=None,
    help=_('New value for the "ram" quota.'))
@utils.arg(
    '--floating-ips',
    metavar='<floating-ips>',
    type=int,
    default=None,
    action=shell.DeprecatedAction,
    help=_('New value for the "floating-ips" quota.'))
@utils.arg(
    '--fixed-ips',
    metavar='<fixed-ips>',
    type=int,
    default=None,
    action=shell.DeprecatedAction,
    help=_('New value for the "fixed-ips" quota.'))
@utils.arg(
    '--metadata-items',
    metavar='<metadata-items>',
    type=int,
    default=None,
    help=_('New value for the "metadata-items" quota.'))
@utils.arg(
    '--injected-files',
    metavar='<injected-files>',
    type=int,
    default=None,
    help=_('New value for the "injected-files" quota.'))
@utils.arg(
    '--injected-file-content-bytes',
    metavar='<injected-file-content-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-content-bytes" quota.'))
@utils.arg(
    '--injected-file-path-bytes',
    metavar='<injected-file-path-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-path-bytes" quota.'))
@utils.arg(
    '--key-pairs',
    metavar='<key-pairs>',
    type=int,
    default=None,
    help=_('New value for the "key-pairs" quota.'))
@utils.arg(
    '--security-groups',
    metavar='<security-groups>',
    type=int,
    default=None,
    action=shell.DeprecatedAction,
    help=_('New value for the "security-groups" quota.'))
@utils.arg(
    '--security-group-rules',
    metavar='<security-group-rules>',
    type=int,
    default=None,
    action=shell.DeprecatedAction,
    help=_('New value for the "security-group-rules" quota.'))
@utils.arg(
    '--server-groups',
    metavar='<server-groups>',
    type=int,
    default=None,
    help=_('New value for the "server-groups" quota.'))
@utils.arg(
    '--server-group-members',
    metavar='<server-group-members>',
    type=int,
    default=None,
    help=_('New value for the "server-group-members" quota.'))
def do_quota_class_update(cs, args):
    """Update the quotas for a quota class."""

    _quota_update(cs.quota_classes, args.class_name, args)


# 2.50 does not support updating quota class values for floating IPs,
# fixed IPs, security groups or security group rules.
# 2.57 does not support updating injected_file* quotas.
@api_versions.wraps("2.50")
@utils.arg(
    'class_name',
    metavar='<class>',
    help=_('Name of quota class to set the quotas for.'))
@utils.arg(
    '--instances',
    metavar='<instances>',
    type=int, default=None,
    help=_('New value for the "instances" quota.'))
@utils.arg(
    '--cores',
    metavar='<cores>',
    type=int, default=None,
    help=_('New value for the "cores" quota.'))
@utils.arg(
    '--ram',
    metavar='<ram>',
    type=int, default=None,
    help=_('New value for the "ram" quota.'))
@utils.arg(
    '--metadata-items',
    metavar='<metadata-items>',
    type=int,
    default=None,
    help=_('New value for the "metadata-items" quota.'))
@utils.arg(
    '--injected-files',
    metavar='<injected-files>',
    type=int,
    default=None,
    help=_('New value for the "injected-files" quota.'),
    start_version='2.50', end_version='2.56')
@utils.arg(
    '--injected-file-content-bytes',
    metavar='<injected-file-content-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-content-bytes" quota.'),
    start_version='2.50', end_version='2.56')
@utils.arg(
    '--injected-file-path-bytes',
    metavar='<injected-file-path-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-path-bytes" quota.'),
    start_version='2.50', end_version='2.56')
@utils.arg(
    '--key-pairs',
    metavar='<key-pairs>',
    type=int,
    default=None,
    help=_('New value for the "key-pairs" quota.'))
@utils.arg(
    '--server-groups',
    metavar='<server-groups>',
    type=int,
    default=None,
    help=_('New value for the "server-groups" quota.'))
@utils.arg(
    '--server-group-members',
    metavar='<server-group-members>',
    type=int,
    default=None,
    help=_('New value for the "server-group-members" quota.'))
def do_quota_class_update(cs, args):
    """Update the quotas for a quota class."""

    _quota_update(cs.quota_classes, args.class_name, args)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    'host', metavar='<host>', nargs='?',
    help=_("Name or ID of the target host.  "
           "If no host is specified, the scheduler will choose one."))
@utils.arg(
    '--password',
    dest='password',
    metavar='<password>',
    help=_("Set the provided admin password on the evacuated server. Not"
            " applicable if the server is on shared storage."))
@utils.arg(
    '--on-shared-storage',
    dest='on_shared_storage',
    action="store_true",
    default=False,
    help=_('Specifies whether server files are located on shared storage.'),
    start_version='2.0',
    end_version='2.13')
@utils.arg(
    '--force',
    dest='force',
    action='store_true',
    default=False,
    help=_('Force to not verify the scheduler if a host is provided.'),
    start_version='2.29')
def do_evacuate(cs, args):
    """Evacuate server from failed host."""

    server = _find_server(cs, args.server)
    on_shared_storage = getattr(args, 'on_shared_storage', None)
    force = getattr(args, 'force', None)
    update_kwargs = {}
    if on_shared_storage is not None:
        update_kwargs['on_shared_storage'] = on_shared_storage
    if force:
        update_kwargs['force'] = force
    res = server.evacuate(host=args.host, password=args.password,
                          **update_kwargs)[1]
    if isinstance(res, dict):
        utils.print_dict(res)


def _print_interfaces(interfaces):
    columns = ['Port State', 'Port ID', 'Net ID', 'IP addresses',
               'MAC Addr']

    class FormattedInterface(object):
        def __init__(self, interface):
            for col in columns:
                key = col.lower().replace(" ", "_")
                if hasattr(interface, key):
                    setattr(self, key, getattr(interface, key))
            self.ip_addresses = ",".join([fip['ip_address']
                                          for fip in interface.fixed_ips])
    utils.print_list([FormattedInterface(i) for i in interfaces], columns)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_interface_list(cs, args):
    """List interfaces attached to a server."""
    server = _find_server(cs, args.server)

    res = server.interface_list()
    if isinstance(res, list):
        _print_interfaces(res)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg(
    '--port-id',
    metavar='<port_id>',
    help=_('Port ID.'),
    dest="port_id")
@utils.arg(
    '--net-id',
    metavar='<net_id>',
    help=_('Network ID'),
    default=None, dest="net_id")
@utils.arg(
    '--fixed-ip',
    metavar='<fixed_ip>',
    help=_('Requested fixed IP.'),
    default=None, dest="fixed_ip")
@utils.arg(
    '--tag',
    metavar='<tag>',
    default=None,
    dest="tag",
    help=_('Tag for the attached interface.'),
    start_version="2.49")
def do_interface_attach(cs, args):
    """Attach a network interface to a server."""
    server = _find_server(cs, args.server)

    update_kwargs = {}
    if 'tag' in args and args.tag:
        update_kwargs['tag'] = args.tag

    res = server.interface_attach(args.port_id, args.net_id, args.fixed_ip,
                                  **update_kwargs)
    if isinstance(res, dict):
        utils.print_dict(res)


@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('port_id', metavar='<port_id>', help=_('Port ID.'))
def do_interface_detach(cs, args):
    """Detach a network interface from a server."""
    server = _find_server(cs, args.server)

    res = server.interface_detach(args.port_id)
    if isinstance(res, dict):
        utils.print_dict(res)


@api_versions.wraps("2.17")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_trigger_crash_dump(cs, args):
    """Trigger crash dump in an instance."""
    server = _find_server(cs, args.server)

    server.trigger_crash_dump()


def _treeizeAvailabilityZone(zone):
    """Build a tree view for availability zones."""
    AvailabilityZone = availability_zones.AvailabilityZone

    az = AvailabilityZone(zone.manager, zone.to_dict(), zone._loaded)
    result = []

    # Zone tree view item
    az.zoneName = zone.zoneName
    az.zoneState = ('available'
                    if zone.zoneState['available'] else 'not available')
    az.set_info('zoneName', az.zoneName)
    az.set_info('zoneState', az.zoneState)
    result.append(az)

    if zone.hosts is not None:
        zone_hosts = sorted(zone.hosts.items(), key=lambda x: x[0])
        for (host, services) in zone_hosts:
            # Host tree view item
            az = AvailabilityZone(zone.manager, zone.to_dict(), zone._loaded)
            az.zoneName = '|- %s' % host
            az.zoneState = ''
            az.set_info('zoneName', az.zoneName)
            az.set_info('zoneState', az.zoneState)
            result.append(az)

            for (svc, state) in services.items():
                # Service tree view item
                az = AvailabilityZone(zone.manager, zone.to_dict(),
                                      zone._loaded)
                az.zoneName = '| |- %s' % svc
                az.zoneState = '%s %s %s' % (
                               'enabled' if state['active'] else 'disabled',
                               ':-)' if state['available'] else 'XXX',
                               state['updated_at'])
                az.set_info('zoneName', az.zoneName)
                az.set_info('zoneState', az.zoneState)
                result.append(az)
    return result


@utils.service_type('compute')
def do_availability_zone_list(cs, _args):
    """List all the availability zones."""
    try:
        availability_zones = cs.availability_zones.list()
    except exceptions.Forbidden as e:  # policy doesn't allow probably
        try:
            availability_zones = cs.availability_zones.list(detailed=False)
        except Exception:
            raise e

    result = []
    for zone in availability_zones:
        result += _treeizeAvailabilityZone(zone)
    _translate_availability_zone_keys(result)
    utils.print_list(result, ['Name', 'Status'],
                     sortby_index=None)


@api_versions.wraps("2.0", "2.12")
def _print_server_group_details(cs, server_group):
    columns = ['Id', 'Name', 'Policies', 'Members', 'Metadata']
    utils.print_list(server_group, columns)


@api_versions.wraps("2.13")
def _print_server_group_details(cs, server_group):    # noqa
    columns = ['Id', 'Name', 'Project Id', 'User Id',
               'Policies', 'Members', 'Metadata']
    utils.print_list(server_group, columns)


@utils.arg(
    '--limit',
    dest='limit',
    metavar='<limit>',
    type=int,
    default=None,
    help=_("Maximum number of server groups to display. If limit is bigger "
           "than 'CONF.api.max_limit' option of Nova API, limit "
           "'CONF.api.max_limit' will be used instead."))
@utils.arg(
    '--offset',
    dest='offset',
    metavar='<offset>',
    type=int,
    default=None,
    help=_('The offset of groups list to display; use with limit to '
           'return a slice of server groups.'))
@utils.arg(
    '--all-projects',
    dest='all_projects',
    action='store_true',
    default=False,
    help=_('Display server groups from all projects (Admin only).'))
def do_server_group_list(cs, args):
    """Print a list of all server groups."""
    server_groups = cs.server_groups.list(all_projects=args.all_projects,
                                          limit=args.limit,
                                          offset=args.offset)
    _print_server_group_details(cs, server_groups)


@utils.arg('name', metavar='<name>', help=_('Server group name.'))
@utils.arg(
    'policy',
    metavar='<policy>',
    nargs='+',
    help=_('Policies for the server groups.'))
def do_server_group_create(cs, args):
    """Create a new server group with the specified details."""
    server_group = cs.server_groups.create(name=args.name,
                                           policies=args.policy)
    _print_server_group_details(cs, [server_group])


@utils.arg(
    'id',
    metavar='<id>',
    nargs='+',
    help=_("Unique ID(s) of the server group to delete."))
def do_server_group_delete(cs, args):
    """Delete specific server group(s)."""
    failure_count = 0

    for sg in args.id:
        try:
            cs.server_groups.delete(sg)
            print(_("Server group %s has been successfully deleted.") % sg)
        except Exception as e:
            failure_count += 1
            print(_("Delete for server group %(sg)s failed: %(e)s") %
                  {'sg': sg, 'e': e})
    if failure_count == len(args.id):
        raise exceptions.CommandError(_("Unable to delete any of the "
                                        "specified server groups."))


@utils.arg(
    'id',
    metavar='<id>',
    help=_("Unique ID of the server group to get."))
def do_server_group_get(cs, args):
    """Get a specific server group."""
    server_group = cs.server_groups.get(args.id)
    _print_server_group_details(cs, [server_group])


def do_version_list(cs, args):
    """List all API versions."""
    result = cs.versions.list()
    if 'min_version' in dir(result[0]):
        columns = ["Id", "Status", "Updated", "Min Version", "Version"]
    else:
        columns = ["Id", "Status", "Updated"]

    print(_("Client supported API versions:"))
    print(_("Minimum version %(v)s") %
          {'v': novaclient.API_MIN_VERSION.get_string()})
    print(_("Maximum version %(v)s") %
          {'v': novaclient.API_MAX_VERSION.get_string()})

    print(_("\nServer supported API versions:"))
    utils.print_list(result, columns)


@api_versions.wraps("2.26")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_server_tag_list(cs, args):
    """Get list of tags from a server."""
    server = _find_server(cs, args.server)
    tags = server.tag_list()
    formatters = {'Tag': lambda o: o}
    utils.print_list(tags, ['Tag'], formatters=formatters)


@api_versions.wraps("2.26")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('tag', metavar='<tag>', nargs='+', help=_('Tag(s) to add.'))
def do_server_tag_add(cs, args):
    """Add one or more tags to a server."""
    server = _find_server(cs, args.server)
    utils.do_action_on_many(
        lambda t: server.add_tag(t),
        args.tag,
        _("Request to add tag %s to specified server has been accepted."),
        _("Unable to add the specified tag to the server."))


@api_versions.wraps("2.26")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('tags', metavar='<tags>', nargs='+', help=_('Tag(s) to set.'))
def do_server_tag_set(cs, args):
    """Set list of tags to a server."""
    server = _find_server(cs, args.server)
    server.set_tags(args.tags)


@api_versions.wraps("2.26")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@utils.arg('tag', metavar='<tag>', nargs='+', help=_('Tag(s) to delete.'))
def do_server_tag_delete(cs, args):
    """Delete one or more tags from a server."""
    server = _find_server(cs, args.server)
    utils.do_action_on_many(
        lambda t: server.delete_tag(t),
        args.tag,
        _("Request to delete tag %s from specified server has been accepted."),
        _("Unable to delete the specified tag from the server."))


@api_versions.wraps("2.26")
@utils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_server_tag_delete_all(cs, args):
    """Delete all tags from a server."""
    server = _find_server(cs, args.server)
    server.delete_all_tags()


@utils.arg(
    'cell',
    metavar='<cell-name>',
    help=_('Name of the cell.'))
def do_cell_show(cs, args):
    """Show details of a given cell."""
    cell = cs.cells.get(args.cell)
    utils.print_dict(cell.to_dict())


@utils.arg(
    '--cell',
    metavar='<cell-name>',
    help=_("Name of the cell to get the capacities."),
    default=None)
def do_cell_capacities(cs, args):
    """Get cell capacities for all cells or a given cell."""
    cell = cs.cells.capacities(args.cell)
    print(_("Ram Available: %s MB") % cell.capacities['ram_free']['total_mb'])
    utils.print_dict(cell.capacities['ram_free']['units_by_mb'],
                     dict_property='Ram(MB)', dict_value="Units")
    print(_("\nDisk Available: %s MB") %
          cell.capacities['disk_free']['total_mb'])
    utils.print_dict(cell.capacities['disk_free']['units_by_mb'],
                     dict_property='Disk(MB)', dict_value="Units")


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_force_delete(cs, args):
    """Force delete a server."""
    utils.find_resource(cs.servers, args.server).force_delete()


@utils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_restore(cs, args):
    """Restore a soft-deleted server."""
    utils.find_resource(cs.servers, args.server, deleted=True).restore()


class EvacuateHostResponse(base.Resource):
    pass


def _server_evacuate(cs, server, args):
    success = True
    error_message = ""
    try:
        if api_versions.APIVersion("2.29") <= cs.api_version:
            # if microversion >= 2.29
            force = getattr(args, 'force', None)
            cs.servers.evacuate(server=server['uuid'], host=args.target_host,
                                force=force)
        elif api_versions.APIVersion("2.14") <= cs.api_version:
            # if microversion 2.14 - 2.28
            cs.servers.evacuate(server=server['uuid'], host=args.target_host)
        else:
            # else microversion 2.0 - 2.13
            on_shared_storage = getattr(args, 'on_shared_storage', None)
            cs.servers.evacuate(server=server['uuid'],
                                host=args.target_host,
                                on_shared_storage=on_shared_storage)
    except Exception as e:
        success = False
        error_message = _("Error while evacuating instance: %s") % e
    return EvacuateHostResponse(base.Manager, {"server_uuid": server['uuid'],
                                               "evacuate_accepted": success,
                                               "error_message": error_message})


def _hyper_servers(cs, host, strict):
    hypervisors = cs.hypervisors.search(host, servers=True)
    for hyper in hypervisors:
        if strict and hyper.hypervisor_hostname != host:
            continue
        if hasattr(hyper, 'servers'):
            for server in hyper.servers:
                yield server
        if strict:
            break
    else:
        if strict:
            msg = (_("No hypervisor matching '%s' could be found.") %
                   host)
            raise exceptions.NotFound(404, msg)


@utils.arg('host', metavar='<host>',
           help='The hypervisor hostname (or pattern) to search for. '
                'WARNING: Use a fully qualified domain name if you only '
                'want to evacuate from a specific host.')
@utils.arg(
    '--target_host',
    metavar='<target_host>',
    default=None,
    help=_('Name of target host. If no host is specified the scheduler will '
           'select a target.'))
@utils.arg(
    '--on-shared-storage',
    dest='on_shared_storage',
    action="store_true",
    default=False,
    help=_('Specifies whether all instances files are on shared storage'),
    start_version='2.0',
    end_version='2.13')
@utils.arg(
    '--force',
    dest='force',
    action='store_true',
    default=False,
    help=_('Force to not verify the scheduler if a host is provided.'),
    start_version='2.29')
@utils.arg(
    '--strict',
    dest='strict',
    action='store_true',
    default=False,
    help=_('Evacuate host with exact hypervisor hostname match'))
def do_host_evacuate(cs, args):
    """Evacuate all instances from failed host."""
    response = []
    for server in _hyper_servers(cs, args.host, args.strict):
        response.append(_server_evacuate(cs, server, args))
    utils.print_list(response, [
        "Server UUID",
        "Evacuate Accepted",
        "Error Message",
    ])


def _server_live_migrate(cs, server, args):
    class HostEvacuateLiveResponse(object):
        def __init__(self, server_uuid, live_migration_accepted,
                     error_message):
            self.server_uuid = server_uuid
            self.live_migration_accepted = live_migration_accepted
            self.error_message = error_message
    success = True
    error_message = ""
    update_kwargs = {}
    try:
        # API >= 2.30
        if 'force' in args and args.force:
            update_kwargs['force'] = args.force
        # API 2.0->2.24
        if 'disk_over_commit' in args:
            update_kwargs['disk_over_commit'] = args.disk_over_commit
        cs.servers.live_migrate(server['uuid'], args.target_host,
                                args.block_migrate, **update_kwargs)
    except Exception as e:
        success = False
        error_message = _("Error while live migrating instance: %s") % e
    return HostEvacuateLiveResponse(server['uuid'],
                                    success,
                                    error_message)


@utils.arg('host', metavar='<host>',
           help='The hypervisor hostname (or pattern) to search for. '
                'WARNING: Use a fully qualified domain name if you only '
                'want to live migrate from a specific host.')
@utils.arg(
    '--target-host',
    metavar='<target_host>',
    default=None,
    help=_('Name of target host.'))
@utils.arg(
    '--block-migrate',
    action='store_true',
    default=False,
    help=_('Enable block migration. (Default=False)'),
    start_version="2.0", end_version="2.24")
@utils.arg(
    '--block-migrate',
    action='store_true',
    default="auto",
    help=_('Enable block migration. (Default=auto)'),
    start_version="2.25")
@utils.arg(
    '--disk-over-commit',
    action='store_true',
    default=False,
    help=_('Enable disk overcommit.'),
    start_version="2.0", end_version="2.24")
@utils.arg(
    '--max-servers',
    type=int,
    dest='max_servers',
    metavar='<max_servers>',
    help='Maximum number of servers to live migrate simultaneously')
@utils.arg(
    '--force',
    dest='force',
    action='store_true',
    default=False,
    help=_('Force to not verify the scheduler if a host is provided.'),
    start_version='2.30')
@utils.arg(
    '--strict',
    dest='strict',
    action='store_true',
    default=False,
    help=_('live Evacuate host with exact hypervisor hostname match'))
def do_host_evacuate_live(cs, args):
    """Live migrate all instances of the specified host
    to other available hosts.
    """
    response = []
    migrating = 0
    for server in _hyper_servers(cs, args.host, args.strict):
        response.append(_server_live_migrate(cs, server, args))
        migrating = migrating + 1
        if (args.max_servers is not None and
                migrating >= args.max_servers):
            break
    utils.print_list(response, [
        "Server UUID",
        "Live Migration Accepted",
        "Error Message",
    ])


class HostServersMigrateResponse(base.Resource):
    pass


def _server_migrate(cs, server):
    success = True
    error_message = ""
    try:
        cs.servers.migrate(server['uuid'])
    except Exception as e:
        success = False
        error_message = _("Error while migrating instance: %s") % e
    return HostServersMigrateResponse(base.Manager,
                                      {"server_uuid": server['uuid'],
                                       "migration_accepted": success,
                                       "error_message": error_message})


@utils.arg('host', metavar='<host>',
           help='The hypervisor hostname (or pattern) to search for. '
                'WARNING: Use a fully qualified domain name if you only '
                'want to cold migrate from a specific host.')
@utils.arg(
    '--strict',
    dest='strict',
    action='store_true',
    default=False,
    help=_('Migrate host with exact hypervisor hostname match'))
def do_host_servers_migrate(cs, args):
    """Cold migrate all instances off the specified host to other available
    hosts.
    """
    response = []
    for server in _hyper_servers(cs, args.host, args.strict):
        response.append(_server_migrate(cs, server))
    utils.print_list(response, [
        "Server UUID",
        "Migration Accepted",
        "Error Message",
    ])


@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or UUID of the server to show actions for.'),
    start_version="2.0", end_version="2.20")
@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or UUID of the server to show actions for. Only UUID can be '
           'used to show actions for a deleted server.'),
    start_version="2.21")
@utils.arg(
    'request_id',
    metavar='<request_id>',
    help=_('Request ID of the action to get.'))
def do_instance_action(cs, args):
    """Show an action."""
    if cs.api_version < api_versions.APIVersion("2.21"):
        server = _find_server(cs, args.server)
    else:
        server = _find_server(cs, args.server, raise_if_notfound=False)
    action_resource = cs.instance_action.get(server, args.request_id)
    action = action_resource.to_dict()
    if 'events' in action:
        action['events'] = pprint.pformat(action['events'])
    utils.print_dict(action)


@api_versions.wraps("2.0", "2.57")
@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or UUID of the server to list actions for.'),
    start_version="2.0", end_version="2.20")
@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or UUID of the server to list actions for. Only UUID can be '
           'used to list actions on a deleted server.'),
    start_version="2.21")
def do_instance_action_list(cs, args):
    """List actions on a server."""
    if cs.api_version < api_versions.APIVersion("2.21"):
        server = _find_server(cs, args.server)
    else:
        server = _find_server(cs, args.server, raise_if_notfound=False)
    actions = cs.instance_action.list(server)
    utils.print_list(actions,
                     ['Action', 'Request_ID', 'Message', 'Start_Time'],
                     sortby_index=3)


@api_versions.wraps("2.58")
@utils.arg(
    'server',
    metavar='<server>',
    help=_('Name or UUID of the server to list actions for. Only UUID can be '
           'used to list actions on a deleted server.'))
@utils.arg(
    '--marker',
    dest='marker',
    metavar='<marker>',
    default=None,
    help=_('The last instance action of the previous page; displays list of '
           'actions after "marker".'))
@utils.arg(
    '--limit',
    dest='limit',
    metavar='<limit>',
    type=int,
    default=None,
    help=_('Maximum number of instance actions to display. Note that there '
           'is a configurable max limit on the server, and the limit that is '
           'used will be the minimum between what is requested here and what '
           'is configured in the server.'))
@utils.arg(
    '--changes-since',
    dest='changes_since',
    metavar='<changes_since>',
    default=None,
    help=_('List only instance actions changed after a certain point of '
           'time. The provided time should be an ISO 8061 formatted time. '
           'ex 2016-03-04T06:27:59Z.'))
def do_instance_action_list(cs, args):
    """List actions on a server."""
    server = _find_server(cs, args.server, raise_if_notfound=False)
    if args.changes_since:
        try:
            timeutils.parse_isotime(args.changes_since)
        except ValueError:
            raise exceptions.CommandError(_('Invalid changes-since value: %s')
                                          % args.changes_since)
    actions = cs.instance_action.list(server, marker=args.marker,
                                      limit=args.limit,
                                      changes_since=args.changes_since)
    # TODO(yikun): Output a "Marker" column if there is a next link?
    utils.print_list(actions,
                     ['Action', 'Request_ID', 'Message', 'Start_Time',
                      'Updated_At'],
                     sortby_index=3)


def do_list_extensions(cs, _args):
    """
    List all the os-api extensions that are available.
    """
    extensions = cs.list_extensions.show_all()
    fields = ["Name", "Summary", "Alias", "Updated"]
    utils.print_list(extensions, fields)


@utils.arg('host', metavar='<host>',
           help='The hypervisor hostname (or pattern) to search for. '
                'WARNING: Use a fully qualified domain name if you only '
                'want to update metadata for servers on a specific host.')
@utils.arg(
    'action',
    metavar='<action>',
    choices=['set', 'delete'],
    help=_("Actions: 'set' or 'delete'"))
@utils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help=_('Metadata to set or delete (only key is necessary on delete)'))
@utils.arg(
    '--strict',
    dest='strict',
    action='store_true',
    default=False,
    help=_('Set host-meta to the hypervisor with exact hostname match'))
def do_host_meta(cs, args):
    """Set or Delete metadata on all instances of a host."""
    for server in _hyper_servers(cs, args.host, args.strict):
        metadata = _extract_metadata(args)
        if args.action == 'set':
            cs.servers.set_meta(server['uuid'], metadata)
        elif args.action == 'delete':
            cs.servers.delete_meta(server['uuid'], metadata.keys())


def _print_migrations(cs, migrations):
    fields = ['Source Node', 'Dest Node', 'Source Compute', 'Dest Compute',
              'Dest Host', 'Status', 'Instance UUID', 'Old Flavor',
              'New Flavor', 'Created At', 'Updated At']

    def old_flavor(migration):
        return migration.old_instance_type_id

    def new_flavor(migration):
        return migration.new_instance_type_id

    def migration_type(migration):
        return migration.migration_type

    formatters = {'Old Flavor': old_flavor, 'New Flavor': new_flavor}

    # Insert migrations UUID after ID
    if cs.api_version >= api_versions.APIVersion("2.59"):
        fields.insert(0, "UUID")

    if cs.api_version >= api_versions.APIVersion("2.23"):
        fields.insert(0, "Id")
        fields.append("Type")
        formatters.update({"Type": migration_type})

    utils.print_list(migrations, fields, formatters)


@api_versions.wraps("2.0", "2.58")
@utils.arg(
    '--instance-uuid',
    dest='instance_uuid',
    metavar='<instance_uuid>',
    help=_('Fetch migrations for the given instance.'))
@utils.arg(
    '--host',
    dest='host',
    metavar='<host>',
    help=_('Fetch migrations for the given host.'))
@utils.arg(
    '--status',
    dest='status',
    metavar='<status>',
    help=_('Fetch migrations for the given status.'))
def do_migration_list(cs, args):
    """Print a list of migrations."""
    migrations = cs.migrations.list(args.host, args.status,
                                    instance_uuid=args.instance_uuid)
    _print_migrations(cs, migrations)


@api_versions.wraps("2.59")
@utils.arg(
    '--instance-uuid',
    dest='instance_uuid',
    metavar='<instance_uuid>',
    help=_('Fetch migrations for the given instance.'))
@utils.arg(
    '--host',
    dest='host',
    metavar='<host>',
    help=_('Fetch migrations for the given host.'))
@utils.arg(
    '--status',
    dest='status',
    metavar='<status>',
    help=_('Fetch migrations for the given status.'))
@utils.arg(
    '--marker',
    dest='marker',
    metavar='<marker>',
    default=None,
    help=_('The last migration of the previous page; displays list of '
           'migrations after "marker". Note that the marker is the '
           'migration UUID.'))
@utils.arg(
    '--limit',
    dest='limit',
    metavar='<limit>',
    type=int,
    default=None,
    help=_('Maximum number of migrations to display. Note that there is a '
           'configurable max limit on the server, and the limit that is used '
           'will be the minimum between what is requested here and what '
           'is configured in the server.'))
@utils.arg(
    '--changes-since',
    dest='changes_since',
    metavar='<changes_since>',
    default=None,
    help=_('List only migrations changed after a certain point of time. '
           'The provided time should be an ISO 8061 formatted time. '
           'ex 2016-03-04T06:27:59Z .'))
def do_migration_list(cs, args):
    """Print a list of migrations."""
    if args.changes_since:
        try:
            timeutils.parse_isotime(args.changes_since)
        except ValueError:
            raise exceptions.CommandError(_('Invalid changes-since value: %s')
                                          % args.changes_since)

    migrations = cs.migrations.list(args.host, args.status,
                                    instance_uuid=args.instance_uuid,
                                    marker=args.marker, limit=args.limit,
                                    changes_since=args.changes_since)
    # TODO(yikun): Output a "Marker" column if there is a next link?
    _print_migrations(cs, migrations)


@utils.arg(
    '--before',
    dest='before',
    metavar='<before>',
    default=None,
    help=_("Filters the response by the date and time before which to list "
           "usage audits. The date and time stamp format is as follows: "
           "CCYY-MM-DD hh:mm:ss.NNNNNN ex 2015-08-27 09:49:58 or "
           "2015-08-27 09:49:58.123456."))
def do_instance_usage_audit_log(cs, args):
    """List/Get server usage audits."""
    audit_log = cs.instance_usage_audit_log.get(before=args.before).to_dict()
    if 'hosts_not_run' in audit_log:
        audit_log['hosts_not_run'] = pprint.pformat(audit_log['hosts_not_run'])
    utils.print_dict(audit_log)

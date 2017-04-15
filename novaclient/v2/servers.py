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
Server interface.
"""

import base64
import warnings

from oslo_utils import encodeutils
import six
from six.moves.urllib import parse

from novaclient import api_versions
from novaclient import base
from novaclient import crypto
from novaclient import exceptions
from novaclient.i18n import _


REBOOT_SOFT, REBOOT_HARD = 'SOFT', 'HARD'

CONSOLE_TYPE_ACTION_MAPPING = {
    'novnc': 'os-getVNCConsole',
    'xvpvnc': 'os-getVNCConsole',
    'spice-html5': 'os-getSPICEConsole',
    'rdp-html5': 'os-getRDPConsole',
    'serial': 'os-getSerialConsole'
}

CONSOLE_TYPE_PROTOCOL_MAPPING = {
    'novnc': 'vnc',
    'xvpvnc': 'vnc',
    'spice-html5': 'spice',
    'rdp-html5': 'rdp',
    'serial': 'serial',
    'webmks': 'mks'
}

ADD_REMOVE_FIXED_FLOATING_DEPRECATION_WARNING = _(
    'The %s server action API is deprecated as of the 2.44 microversion. This '
    'API binding will be removed in the first major release after the Nova '
    '16.0.0 Pike release. Use python-neutronclient or openstacksdk instead.'
)


class Server(base.Resource):
    HUMAN_ID = True

    def __repr__(self):
        return '<Server: %s>' % getattr(self, 'name', 'unknown-name')

    def delete(self):
        """
        Delete (i.e. shut down and delete the image) this server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(self)

    @api_versions.wraps("2.0", "2.18")
    def update(self, name=None):
        """
        Update the name and the description for this server.

        :param name: Update the server's name.
        :returns: :class:`Server`
        """
        return self.manager.update(self, name=name)

    @api_versions.wraps("2.19")
    def update(self, name=None, description=None):
        """
        Update the name and the description for this server.

        :param name: Update the server's name.
        :param description: Update the server's description.
        :returns: :class:`Server`
        """
        update_kwargs = {"name": name}
        if description is not None:
            update_kwargs["description"] = description
        return self.manager.update(self, **update_kwargs)

    def get_console_output(self, length=None):
        """
        Get text console log output from Server.

        :param length: The number of lines you would like to retrieve (as int)
        """
        return self.manager.get_console_output(self, length)

    def get_vnc_console(self, console_type):
        """
        Get vnc console for a Server.

        :param console_type: Type of console ('novnc' or 'xvpvnc')
        """
        return self.manager.get_vnc_console(self, console_type)

    def get_spice_console(self, console_type):
        """
        Get spice console for a Server.

        :param console_type: Type of console ('spice-html5')
        """
        return self.manager.get_spice_console(self, console_type)

    def get_rdp_console(self, console_type):
        """
        Get rdp console for a Server.

        :param console_type: Type of console ('rdp-html5')
        """
        return self.manager.get_rdp_console(self, console_type)

    def get_serial_console(self, console_type):
        """
        Get serial console for a Server.

        :param console_type: Type of console ('serial')
        """
        return self.manager.get_serial_console(self, console_type)

    def get_mks_console(self):
        """
        Get mks console for a Server.

        """
        return self.manager.get_mks_console(self)

    def get_console_url(self, console_type):
        """
        Retrieve a console of a particular protocol and console_type

        :param console_type: Type of console
        """

        return self.manager.get_console_url(self, console_type)

    def get_password(self, private_key=None):
        """
        Get password for a Server.

        Returns the clear password of an instance if private_key is
        provided, returns the ciphered password otherwise.

        :param private_key: Path to private key file for decryption
                            (optional)
        """
        return self.manager.get_password(self, private_key)

    def clear_password(self):
        """
        Get password for a Server.

        """
        return self.manager.clear_password(self)

    def add_fixed_ip(self, network_id):
        """
        Add an IP address on a network.

        :param network_id: The ID of the network the IP should be on.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.add_fixed_ip(self, network_id)

    def add_floating_ip(self, address, fixed_address=None):
        """
        Add floating IP to an instance

        :param address: The IP address or FloatingIP to add to the instance
        :param fixed_address: The fixedIP address the FloatingIP is to be
               associated with (optional)
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.add_floating_ip(self, address, fixed_address)

    def remove_floating_ip(self, address):
        """
        Remove floating IP from an instance

        :param address: The IP address or FloatingIP to remove
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.remove_floating_ip(self, address)

    def stop(self):
        """
        Stop -- Stop the running server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.stop(self)

    def force_delete(self):
        """
        Force delete -- Force delete a server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.force_delete(self)

    def restore(self):
        """
        Restore -- Restore a server in 'soft-deleted' state.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.restore(self)

    def start(self):
        """
        Start -- Start the paused server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.start(self)

    def pause(self):
        """
        Pause -- Pause the running server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.pause(self)

    def unpause(self):
        """
        Unpause -- Unpause the paused server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.unpause(self)

    def lock(self):
        """
        Lock -- Lock the instance from certain operations.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.lock(self)

    def unlock(self):
        """
        Unlock -- Remove instance lock.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.unlock(self)

    def suspend(self):
        """
        Suspend -- Suspend the running server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.suspend(self)

    def resume(self):
        """
        Resume -- Resume the suspended server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.resume(self)

    def rescue(self, password=None, image=None):
        """
        Rescue -- Rescue the problematic server.

        :param password: The admin password to be set in the rescue instance.
        :param image: The :class:`Image` to rescue with.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.rescue(self, password, image)

    def unrescue(self):
        """
        Unrescue -- Unrescue the rescued server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.unrescue(self)

    def shelve(self):
        """
        Shelve -- Shelve the server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.shelve(self)

    def shelve_offload(self):
        """
        Shelve_offload -- Remove a shelved server from the compute node.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.shelve_offload(self)

    def unshelve(self):
        """
        Unshelve -- Unshelve the server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.unshelve(self)

    def diagnostics(self):
        """Diagnostics -- Retrieve server diagnostics."""
        return self.manager.diagnostics(self)

    def migrate(self):
        """
        Migrate a server to a new host.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.migrate(self)

    def remove_fixed_ip(self, address):
        """
        Remove an IP address.

        :param address: The IP address to remove.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.remove_fixed_ip(self, address)

    def change_password(self, password):
        """
        Update the admin password for a server.

        :param password: string to set as the admin password on the server
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.change_password(self, password)

    def reboot(self, reboot_type=REBOOT_SOFT):
        """
        Reboot the server.

        :param reboot_type: either :data:`REBOOT_SOFT` for a software-level
                reboot, or `REBOOT_HARD` for a virtual power cycle hard reboot.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.reboot(self, reboot_type)

    def rebuild(self, image, password=None, preserve_ephemeral=False,
                **kwargs):
        """
        Rebuild -- shut down and then re-image -- this server.

        :param image: the :class:`Image` (or its ID) to re-image with.
        :param password: string to set as the admin password on the rebuilt
                         server.
        :param preserve_ephemeral: If True, request that any ephemeral device
            be preserved when rebuilding the instance. Defaults to False.
        """
        return self.manager.rebuild(self, image, password=password,
                                    preserve_ephemeral=preserve_ephemeral,
                                    **kwargs)

    def resize(self, flavor, **kwargs):
        """
        Resize the server's resources.

        :param flavor: the :class:`Flavor` (or its ID) to resize to.
        :returns: An instance of novaclient.base.TupleWithMeta

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        return self.manager.resize(self, flavor, **kwargs)

    def create_image(self, image_name, metadata=None):
        """
        Create an image based on this server.

        :param image_name: The name to assign the newly create image.
        :param metadata: Metadata to assign to the image.
        """
        return self.manager.create_image(self, image_name, metadata)

    def backup(self, backup_name, backup_type, rotation):
        """
        Backup a server instance.

        :param backup_name: Name of the backup image
        :param backup_type: The backup type, like 'daily' or 'weekly'
        :param rotation: Int parameter representing how many backups to
                        keep around.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.backup(self, backup_name, backup_type, rotation)

    def confirm_resize(self):
        """
        Confirm that the resize worked, thus removing the original server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.confirm_resize(self)

    def revert_resize(self):
        """
        Revert a previous resize, switching back to the old server.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.revert_resize(self)

    @property
    def networks(self):
        """
        Generate a simplified list of addresses
        """
        networks = {}
        try:
            for network_label, address_list in self.addresses.items():
                networks[network_label] = [a['addr'] for a in address_list]
            return networks
        except Exception:
            return {}

    @api_versions.wraps("2.0", "2.24")
    def live_migrate(self, host=None,
                     block_migration=False,
                     disk_over_commit=None):
        """
        Migrates a running instance to a new machine.

        :param host: destination host name.
        :param block_migration: if True, do block_migration, the default
                                value is False and None will be mapped to False
        :param disk_over_commit: if True, allow disk over commit, the default
                                 value is None which is mapped to False
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        if block_migration is None:
            block_migration = False
        if disk_over_commit is None:
            disk_over_commit = False
        return self.manager.live_migrate(self, host,
                                         block_migration,
                                         disk_over_commit)

    @api_versions.wraps("2.25", "2.29")
    def live_migrate(self, host=None, block_migration=None):
        """
        Migrates a running instance to a new machine.

        :param host: destination host name.
        :param block_migration: if True, do block_migration, the default
                                value is None which is mapped to 'auto'.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        if block_migration is None:
            block_migration = "auto"
        return self.manager.live_migrate(self, host, block_migration)

    @api_versions.wraps("2.30")
    def live_migrate(self, host=None, block_migration=None, force=None):
        """
        Migrates a running instance to a new machine.

        :param host: destination host name.
        :param block_migration: if True, do block_migration, the default
                                value is None which is mapped to 'auto'.
        :param force: force to bypass the scheduler if host is provided.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        if block_migration is None:
            block_migration = "auto"
        return self.manager.live_migrate(self, host, block_migration, force)

    def reset_state(self, state='error'):
        """
        Reset the state of an instance to active or error.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.reset_state(self, state)

    def reset_network(self):
        """
        Reset network of an instance.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.reset_network(self)

    def add_security_group(self, security_group):
        """
        Add a security group to an instance.

        :param security_group: The name of security group to add
        :returns: An instance of novaclient.base.DictWithMeta
        """
        return self.manager.add_security_group(self, security_group)

    def remove_security_group(self, security_group):
        """
        Remove a security group from an instance.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.remove_security_group(self, security_group)

    def list_security_group(self):
        """
        List security group(s) of an instance.
        """
        return self.manager.list_security_group(self)

    @api_versions.wraps("2.0", "2.13")
    def evacuate(self, host=None, on_shared_storage=True, password=None):
        """
        Evacuate an instance from failed host to specified host.

        :param host: Name of the target host
        :param on_shared_storage: Specifies whether instance files located
                        on shared storage.
        :param password: string to set as admin password on the evacuated
                         server.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.evacuate(self, host, on_shared_storage, password)

    @api_versions.wraps("2.14", "2.28")
    def evacuate(self, host=None, password=None):
        """
        Evacuate an instance from failed host to specified host.

        :param host: Name of the target host
        :param password: string to set as admin password on the evacuated
                         server.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.evacuate(self, host, password)

    @api_versions.wraps("2.29")
    def evacuate(self, host=None, password=None, force=None):
        """
        Evacuate an instance from failed host to specified host.

        :param host: Name of the target host
        :param password: string to set as admin password on the evacuated
                         server.
        :param force: forces to bypass the scheduler if host is provided.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.evacuate(self, host, password, force)

    def interface_list(self):
        """
        List interfaces attached to an instance.
        """
        return self.manager.interface_list(self)

    def interface_attach(self, port_id, net_id, fixed_ip):
        """
        Attach a network interface to an instance.
        """
        return self.manager.interface_attach(self, port_id, net_id, fixed_ip)

    def interface_detach(self, port_id):
        """
        Detach a network interface from an instance.
        """
        return self.manager.interface_detach(self, port_id)

    def trigger_crash_dump(self):
        """Trigger crash dump in an instance"""
        return self.manager.trigger_crash_dump(self)

    @api_versions.wraps('2.26')
    def tag_list(self):
        """
        Get list of tags from an instance.
        """
        return self.manager.tag_list(self)

    @api_versions.wraps('2.26')
    def delete_tag(self, tag):
        """
        Remove single tag from an instance.
        """
        return self.manager.delete_tag(self, tag)

    @api_versions.wraps('2.26')
    def delete_all_tags(self):
        """
        Remove all tags from an instance.
        """
        return self.manager.delete_all_tags(self)

    @api_versions.wraps('2.26')
    def set_tags(self, tags):
        """
        Set list of tags to an instance.
        """
        return self.manager.set_tags(self, tags)

    @api_versions.wraps('2.26')
    def add_tag(self, tag):
        """
        Add single tag to an instance.
        """
        return self.manager.add_tag(self, tag)


class NetworkInterface(base.Resource):
    @property
    def id(self):
        return self.port_id

    def __repr__(self):
        return '<NetworkInterface: %s>' % self.id


class SecurityGroup(base.Resource):
    def __str__(self):
        return str(self.id)


class ServerManager(base.BootingManagerWithFind):
    resource_class = Server

    def _boot(self, resource_url, response_key, name, image, flavor,
              meta=None, files=None, userdata=None,
              reservation_id=None, return_raw=False, min_count=None,
              max_count=None, security_groups=None, key_name=None,
              availability_zone=None, block_device_mapping=None,
              block_device_mapping_v2=None, nics=None, scheduler_hints=None,
              config_drive=None, admin_pass=None, disk_config=None,
              access_ip_v4=None, access_ip_v6=None, description=None,
              **kwargs):
        """
        Create (boot) a new server.
        """
        body = {"server": {
            "name": name,
            "imageRef": str(base.getid(image)) if image else '',
            "flavorRef": str(base.getid(flavor)),
        }}
        if userdata:
            if hasattr(userdata, 'read'):
                userdata = userdata.read()

            # NOTE(melwitt): Text file data is converted to bytes prior to
            # base64 encoding. The utf-8 encoding will fail for binary files.
            if six.PY3:
                try:
                    userdata = userdata.encode("utf-8")
                except AttributeError:
                    # In python 3, 'bytes' object has no attribute 'encode'
                    pass
            else:
                try:
                    userdata = encodeutils.safe_encode(userdata)
                except UnicodeDecodeError:
                    pass

            userdata_b64 = base64.b64encode(userdata).decode('utf-8')
            body["server"]["user_data"] = userdata_b64
        if meta:
            body["server"]["metadata"] = meta
        if reservation_id:
            body["server"]["reservation_id"] = reservation_id
        if key_name:
            body["server"]["key_name"] = key_name
        if scheduler_hints:
            body['os:scheduler_hints'] = scheduler_hints
        if config_drive:
            body["server"]["config_drive"] = config_drive
        if admin_pass:
            body["server"]["adminPass"] = admin_pass
        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        body["server"]["min_count"] = min_count
        body["server"]["max_count"] = max_count

        if security_groups:
            body["server"]["security_groups"] = [{'name': sg}
                                                 for sg in security_groups]

        # Files are a slight bit tricky. They're passed in a "personality"
        # list to the POST. Each item is a dict giving a file name and the
        # base64-encoded contents of the file. We want to allow passing
        # either an open file *or* some contents as files here.
        if files:
            personality = body['server']['personality'] = []
            for filepath, file_or_string in sorted(files.items(),
                                                   key=lambda x: x[0]):
                if hasattr(file_or_string, 'read'):
                    data = file_or_string.read()
                else:
                    data = file_or_string

                if six.PY3 and isinstance(data, str):
                    data = data.encode('utf-8')
                cont = base64.b64encode(data).decode('utf-8')
                personality.append({
                    'path': filepath,
                    'contents': cont,
                })

        if availability_zone:
            body["server"]["availability_zone"] = availability_zone

        # Block device mappings are passed as a list of dictionaries
        if block_device_mapping:
            body['server']['block_device_mapping'] = \
                self._parse_block_device_mapping(block_device_mapping)
        elif block_device_mapping_v2:
            # Following logic can't be removed because it will leaves
            # a valid boot with both --image and --block-device
            # failed , see bug 1433609 for more info
            if image:
                bdm_dict = {'uuid': base.getid(image), 'source_type': 'image',
                            'destination_type': 'local', 'boot_index': 0,
                            'delete_on_termination': True}
                block_device_mapping_v2.insert(0, bdm_dict)
            body['server']['block_device_mapping_v2'] = block_device_mapping_v2

        if nics is not None:
            # With microversion 2.37+ nics can be an enum of 'auto' or 'none'
            # or a list of dicts.
            if isinstance(nics, six.string_types):
                all_net_data = nics
            else:
                # NOTE(tr3buchet): nics can be an empty list
                all_net_data = []
                for nic_info in nics:
                    net_data = {}
                    # if value is empty string, do not send value in body
                    if nic_info.get('net-id'):
                        net_data['uuid'] = nic_info['net-id']
                    if (nic_info.get('v4-fixed-ip') and
                            nic_info.get('v6-fixed-ip')):
                        raise base.exceptions.CommandError(_(
                            "Only one of 'v4-fixed-ip' and 'v6-fixed-ip' "
                            "may be provided."))
                    elif nic_info.get('v4-fixed-ip'):
                        net_data['fixed_ip'] = nic_info['v4-fixed-ip']
                    elif nic_info.get('v6-fixed-ip'):
                        net_data['fixed_ip'] = nic_info['v6-fixed-ip']
                    if nic_info.get('port-id'):
                        net_data['port'] = nic_info['port-id']
                    if nic_info.get('tag'):
                        net_data['tag'] = nic_info['tag']
                    all_net_data.append(net_data)
            body['server']['networks'] = all_net_data

        if disk_config is not None:
            body['server']['OS-DCF:diskConfig'] = disk_config

        if access_ip_v4 is not None:
            body['server']['accessIPv4'] = access_ip_v4

        if access_ip_v6 is not None:
            body['server']['accessIPv6'] = access_ip_v6

        if description:
            body['server']['description'] = description

        return self._create(resource_url, body, response_key,
                            return_raw=return_raw, **kwargs)

    def get(self, server):
        """
        Get a server.

        :param server: ID of the :class:`Server` to get.
        :rtype: :class:`Server`
        """
        return self._get("/servers/%s" % base.getid(server), "server")

    def list(self, detailed=True, search_opts=None, marker=None, limit=None,
             sort_keys=None, sort_dirs=None):
        """
        Get a list of servers.

        :param detailed: Whether to return detailed server info (optional).
        :param search_opts: Search options to filter out servers which don't
            match the search_opts (optional). The search opts format is a
            dictionary of key / value pairs that will be appended to the query
            string.  For a complete list of keys see:
            http://developer.openstack.org/api-ref-compute-v2.1.html#listServers
        :param marker: Begin returning servers that appear later in the server
                       list than that represented by this server id (optional).
        :param limit: Maximum number of servers to return (optional).
        :param sort_keys: List of sort keys
        :param sort_dirs: List of sort directions

        :rtype: list of :class:`Server`

        Examples:

        client.servers.list() - returns detailed list of servers

        client.servers.list(search_opts={'status': 'ERROR'}) -
        returns list of servers in error state.

        client.servers.list(limit=10) - returns only 10 servers

        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.items():
            if val:
                if isinstance(val, six.text_type):
                    val = val.encode('utf-8')
                qparams[opt] = val

        detail = ""
        if detailed:
            detail = "/detail"

        result = base.ListWithMeta([], None)
        while True:
            if marker:
                qparams['marker'] = marker

            if limit and limit != -1:
                qparams['limit'] = limit

            # Transform the dict to a sequence of two-element tuples in fixed
            # order, then the encoded string will be consistent in Python 2&3.
            if qparams or sort_keys or sort_dirs:
                # sort keys and directions are unique since the same parameter
                # key is repeated for each associated value
                # (ie, &sort_key=key1&sort_key=key2&sort_key=key3)
                items = list(qparams.items())
                if sort_keys:
                    items.extend(('sort_key', sort_key)
                                 for sort_key in sort_keys)
                if sort_dirs:
                    items.extend(('sort_dir', sort_dir)
                                 for sort_dir in sort_dirs)
                new_qparams = sorted(items, key=lambda x: x[0])
                query_string = "?%s" % parse.urlencode(new_qparams)
            else:
                query_string = ""

            servers = self._list("/servers%s%s" % (detail, query_string),
                                 "servers")
            result.extend(servers)
            result.append_request_ids(servers.request_ids)

            if not servers or limit != -1:
                break
            marker = result[-1].id
        return result

    @api_versions.wraps('2.0', '2.43')
    def add_fixed_ip(self, server, network_id):
        """
        DEPRECATED Add an IP address on a network.

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param network_id: The ID of the network the IP should be on.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        warnings.warn(ADD_REMOVE_FIXED_FLOATING_DEPRECATION_WARNING %
                      'addFixedIP', DeprecationWarning)
        return self._action('addFixedIp', server, {'networkId': network_id})

    @api_versions.wraps('2.0', '2.43')
    def remove_fixed_ip(self, server, address):
        """
        DEPRECATED Remove an IP address.

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param address: The IP address to remove.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        warnings.warn(ADD_REMOVE_FIXED_FLOATING_DEPRECATION_WARNING %
                      'removeFixedIP', DeprecationWarning)
        return self._action('removeFixedIp', server, {'address': address})

    @api_versions.wraps('2.0', '2.43')
    def add_floating_ip(self, server, address, fixed_address=None):
        """
        DEPRECATED Add a floating IP to an instance

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param address: The FloatingIP or string floating address to add.
        :param fixed_address: The FixedIP the floatingIP should be
                              associated with (optional)
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        warnings.warn(ADD_REMOVE_FIXED_FLOATING_DEPRECATION_WARNING %
                      'addFloatingIP', DeprecationWarning)
        address = address.ip if hasattr(address, 'ip') else address
        if fixed_address:
            if hasattr(fixed_address, 'ip'):
                fixed_address = fixed_address.ip
            return self._action('addFloatingIp', server,
                                {'address': address,
                                 'fixed_address': fixed_address})
        else:
            return self._action('addFloatingIp', server, {'address': address})

    @api_versions.wraps('2.0', '2.43')
    def remove_floating_ip(self, server, address):
        """
        DEPRECATED Remove a floating IP address.

        :param server: The :class:`Server` (or its ID) to remove an IP from.
        :param address: The FloatingIP or string floating address to remove.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        warnings.warn(ADD_REMOVE_FIXED_FLOATING_DEPRECATION_WARNING %
                      'removeFloatingIP', DeprecationWarning)
        address = address.ip if hasattr(address, 'ip') else address
        return self._action('removeFloatingIp', server, {'address': address})

    @api_versions.wraps('2.0', '2.5')
    def get_vnc_console(self, server, console_type):
        """
        Get a vnc console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :param console_type: Type of vnc console to get ('novnc' or 'xvpvnc')
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, console_type)

    @api_versions.wraps('2.0', '2.5')
    def get_spice_console(self, server, console_type):
        """
        Get a spice console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :param console_type: Type of spice console to get ('spice-html5')
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, console_type)

    @api_versions.wraps('2.0', '2.5')
    def get_rdp_console(self, server, console_type):
        """
        Get a rdp console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :param console_type: Type of rdp console to get ('rdp-html5')
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, console_type)

    @api_versions.wraps('2.0', '2.5')
    def get_serial_console(self, server, console_type):
        """
        Get a serial console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :param console_type: Type of serial console to get ('serial')
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, console_type)

    def _get_protocol(self, console_type):
        protocol = CONSOLE_TYPE_PROTOCOL_MAPPING.get(console_type)
        if not protocol:
            raise exceptions.UnsupportedConsoleType(console_type)

        return protocol

    @api_versions.wraps('2.0', '2.5')
    def get_console_url(self, server, console_type):
        """
        Retrieve a console url of a server.

        :param server: server to get console url for
        :param console_type: type can be novnc, xvpvnc, spice-html5,
                             rdp-html5 and serial.
        """

        action = CONSOLE_TYPE_ACTION_MAPPING.get(console_type)
        if not action:
            raise exceptions.UnsupportedConsoleType(console_type)
        return self._action(action, server, {'type': console_type})

    @api_versions.wraps('2.6')
    def get_vnc_console(self, server, console_type):
        """
        Get a vnc console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :param console_type: Type of vnc console to get ('novnc' or 'xvpvnc')
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, console_type)

    @api_versions.wraps('2.6')
    def get_spice_console(self, server, console_type):
        """
        Get a spice console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :param console_type: Type of spice console to get ('spice-html5')
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, console_type)

    @api_versions.wraps('2.6')
    def get_rdp_console(self, server, console_type):
        """
        Get a rdp console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :param console_type: Type of rdp console to get ('rdp-html5')
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, console_type)

    @api_versions.wraps('2.6')
    def get_serial_console(self, server, console_type):
        """
        Get a serial console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :param console_type: Type of serial console to get ('serial')
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, console_type)

    @api_versions.wraps('2.8')
    def get_mks_console(self, server):
        """
        Get a mks console for an instance

        :param server: The :class:`Server` (or its ID) to get console for.
        :returns: An instance of novaclient.base.DictWithMeta
        """

        return self.get_console_url(server, 'webmks')

    @api_versions.wraps('2.6')
    def get_console_url(self, server, console_type):
        """
        Retrieve a console url of a server.

        :param server: server to get console url for
        :param console_type: type can be novnc/xvpvnc for protocol vnc;
                             spice-html5 for protocol spice; rdp-html5 for
                             protocol rdp; serial for protocol serial.
                             webmks for protocol mks (since version 2.8).
        """

        if self.api_version < api_versions.APIVersion('2.8'):
            if console_type == 'webmks':
                raise exceptions.UnsupportedConsoleType(console_type)

        protocol = self._get_protocol(console_type)
        body = {'remote_console': {'protocol': protocol,
                                   'type': console_type}}
        url = '/servers/%s/remote-consoles' % base.getid(server)
        resp, body = self.api.client.post(url, body=body)
        return self.convert_into_with_meta(body, resp)

    def get_password(self, server, private_key=None):
        """
        Get admin password of an instance

        Returns the admin password of an instance in the clear if private_key
        is provided, returns the ciphered password otherwise.

        Requires that openssl is installed and in the path

        :param server: The :class:`Server` (or its ID) for which the admin
                       password is to be returned
        :param private_key: The private key to decrypt password
                            (optional)
        :returns: An instance of novaclient.base.StrWithMeta or
                  novaclient.base.BytesWithMeta or
                  novaclient.base.UnicodeWithMeta
        """

        resp, body = self.api.client.get("/servers/%s/os-server-password"
                                         % base.getid(server))
        ciphered_pw = body.get('password', '') if body else ''
        if private_key and ciphered_pw:
            try:
                ciphered_pw = crypto.decrypt_password(private_key, ciphered_pw)
            except Exception as exc:
                ciphered_pw = '%sFailed to decrypt:\n%s' % (exc, ciphered_pw)
        return self.convert_into_with_meta(ciphered_pw, resp)

    def clear_password(self, server):
        """
        Clear the admin password of an instance

        Remove the admin password for an instance from the metadata server.

        :param server: The :class:`Server` (or its ID) for which the admin
                       password is to be cleared
        """

        return self._delete("/servers/%s/os-server-password"
                            % base.getid(server))

    def stop(self, server):
        """
        Stop the server.

        :param server: The :class:`Server` (or its ID) to stop
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        resp, body = self._action_return_resp_and_body('os-stop', server, None)
        return base.TupleWithMeta((resp, body), resp)

    def force_delete(self, server):
        """
        Force delete the server.

        :param server: The :class:`Server` (or its ID) to force delete
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        resp, body = self._action_return_resp_and_body('forceDelete', server,
                                                       None)
        return base.TupleWithMeta((resp, body), resp)

    def restore(self, server):
        """
        Restore soft-deleted server.

        :param server: The :class:`Server` (or its ID) to restore
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        resp, body = self._action_return_resp_and_body('restore', server, None)
        return base.TupleWithMeta((resp, body), resp)

    def start(self, server):
        """
        Start the server.

        :param server: The :class:`Server` (or its ID) to start
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('os-start', server, None)

    def pause(self, server):
        """
        Pause the server.

        :param server: The :class:`Server` (or its ID) to pause
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('pause', server, None)

    def unpause(self, server):
        """
        Unpause the server.

        :param server: The :class:`Server` (or its ID) to unpause
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('unpause', server, None)

    def lock(self, server):
        """
        Lock the server.

        :param server: The :class:`Server` (or its ID) to lock
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('lock', server, None)

    def unlock(self, server):
        """
        Unlock the server.

        :param server: The :class:`Server` (or its ID) to unlock
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('unlock', server, None)

    def suspend(self, server):
        """
        Suspend the server.

        :param server: The :class:`Server` (or its ID) to suspend
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('suspend', server, None)

    def resume(self, server):
        """
        Resume the server.

        :param server: The :class:`Server` (or its ID) to resume
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('resume', server, None)

    def rescue(self, server, password=None, image=None):
        """
        Rescue the server.

        :param server: The :class:`Server` to rescue.
        :param password: The admin password to be set in the rescue instance.
        :param image: The :class:`Image` to rescue with.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        info = {}
        if password:
            info['adminPass'] = password
        if image:
            info['rescue_image_ref'] = base.getid(image)
        resp, body = self._action_return_resp_and_body('rescue', server,
                                                       info or None)
        return base.TupleWithMeta((resp, body), resp)

    def unrescue(self, server):
        """
        Unrescue the server.

        :param server: The :class:`Server` (or its ID) to unrescue
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('unrescue', server, None)

    def shelve(self, server):
        """
        Shelve the server.

        :param server: The :class:`Server` (or its ID) to shelve
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('shelve', server, None)

    def shelve_offload(self, server):
        """
        Remove a shelved instance from the compute node.

        :param server: The :class:`Server` (or its ID) to shelve offload
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('shelveOffload', server, None)

    def unshelve(self, server):
        """
        Unshelve the server.

        :param server: The :class:`Server` (or its ID) to unshelve
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('unshelve', server, None)

    def ips(self, server):
        """
        Return IP Addresses associated with the server.

        Often a cheaper call then getting all the details for a server.

        :param server: The :class:`Server` (or its ID) for which
                       the IP adresses are to be returned
        :returns: An instance of novaclient.base.DictWithMeta
        """
        resp, body = self.api.client.get("/servers/%s/ips" %
                                         base.getid(server))
        return base.DictWithMeta(body['addresses'], resp)

    def diagnostics(self, server):
        """
        Retrieve server diagnostics.

        :param server: The :class:`Server` (or its ID) for which
                       diagnostics to be returned
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        resp, body = self.api.client.get("/servers/%s/diagnostics" %
                                         base.getid(server))
        return base.TupleWithMeta((resp, body), resp)

    def _validate_create_nics(self, nics):
        # nics are required with microversion 2.37+ and can be a string or list
        if self.api_version > api_versions.APIVersion('2.36'):
            if not nics:
                raise ValueError('nics are required after microversion 2.36')
        elif nics and not isinstance(nics, list):
            raise ValueError('nics must be a list')

    def create(self, name, image, flavor, meta=None, files=None,
               reservation_id=None, min_count=None,
               max_count=None, security_groups=None, userdata=None,
               key_name=None, availability_zone=None,
               block_device_mapping=None, block_device_mapping_v2=None,
               nics=None, scheduler_hints=None,
               config_drive=None, disk_config=None, admin_pass=None,
               access_ip_v4=None, access_ip_v6=None, **kwargs):
        # TODO(anthony): indicate in doc string if param is an extension
        # and/or optional
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. Both keys and values must be <=255 characters.
        :param files: A dict of files to overwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.
        :param reservation_id: a UUID for the set of servers being requested.
        :param min_count: (optional extension) The minimum number of
                          servers to launch.
        :param max_count: (optional extension) The maximum number of
                          servers to launch.
        :param security_groups: A list of security group names
        :param userdata: user data to pass to be exposed by the metadata
                      server this can be a file type object as well or a
                      string.
        :param key_name: (optional extension) name of previously created
                      keypair to inject into the instance.
        :param availability_zone: Name of the availability zone for instance
                                  placement.
        :param block_device_mapping: (optional extension) A dict of block
                      device mappings for this server.
        :param block_device_mapping_v2: (optional extension) A dict of block
                      device mappings for this server.
        :param nics:  An ordered list of nics (dicts) to be added to this
                      server, with information about connected networks,
                      fixed IPs, port etc.
                      Beginning in microversion 2.37 this field is required and
                      also supports a single string value of 'auto' or 'none'.
                      The 'auto' value means the Compute service will
                      automatically allocate a network for the project if one
                      is not available. This is the same behavior as not
                      passing anything for nics before microversion 2.37. The
                      'none' value tells the Compute service to not allocate
                      any networking for the server.
        :param scheduler_hints: (optional extension) arbitrary key-value pairs
                            specified by the client to help boot an instance
        :param config_drive: (optional extension) value for config drive
                            either boolean, or volume-id
        :param disk_config: (optional extension) control how the disk is
                            partitioned when the server is created.  possible
                            values are 'AUTO' or 'MANUAL'.
        :param admin_pass: (optional extension) add a user supplied admin
                           password.
        :param access_ip_v4: (optional extension) add alternative access ip v4
        :param access_ip_v6: (optional extension) add alternative access ip v6
        :param description: optional description of the server (allowed since
                            microversion 2.19)
        """
        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        if min_count > max_count:
            min_count = max_count

        boot_args = [name, image, flavor]

        descr_microversion = api_versions.APIVersion("2.19")
        if "description" in kwargs and self.api_version < descr_microversion:
            raise exceptions.UnsupportedAttribute("description", "2.19")

        self._validate_create_nics(nics)

        tags_microversion = api_versions.APIVersion("2.32")
        if self.api_version < tags_microversion:
            if nics:
                for nic_info in nics:
                    if nic_info.get("tag"):
                        raise ValueError("Setting interface tags is "
                                         "unsupported before microversion "
                                         "2.32")

            if block_device_mapping_v2:
                for bdm in block_device_mapping_v2:
                    if bdm.get("tag"):
                        raise ValueError("Setting block device tags is "
                                         "unsupported before microversion "
                                         "2.32")

        boot_kwargs = dict(
            meta=meta, files=files, userdata=userdata,
            reservation_id=reservation_id, min_count=min_count,
            max_count=max_count, security_groups=security_groups,
            key_name=key_name, availability_zone=availability_zone,
            scheduler_hints=scheduler_hints, config_drive=config_drive,
            disk_config=disk_config, admin_pass=admin_pass,
            access_ip_v4=access_ip_v4, access_ip_v6=access_ip_v6, **kwargs)

        if block_device_mapping:
            resource_url = "/os-volumes_boot"
            boot_kwargs['block_device_mapping'] = block_device_mapping
        elif block_device_mapping_v2:
            resource_url = "/os-volumes_boot"
            boot_kwargs['block_device_mapping_v2'] = block_device_mapping_v2
        else:
            resource_url = "/servers"
        if nics:
            boot_kwargs['nics'] = nics

        response_key = "server"
        return self._boot(resource_url, response_key, *boot_args,
                          **boot_kwargs)

    @api_versions.wraps("2.0", "2.18")
    def update(self, server, name=None):
        """
        Update the name for a server.

        :param server: The :class:`Server` (or its ID) to update.
        :param name: Update the server's name.
        """
        if name is None:
            return

        body = {
            "server": {
                "name": name,
            },
        }

        return self._update("/servers/%s" % base.getid(server), body, "server")

    @api_versions.wraps("2.19")
    def update(self, server, name=None, description=None):
        """
        Update the name or the description for a server.

        :param server: The :class:`Server` (or its ID) to update.
        :param name: Update the server's name.
        :param description: Update the server's description. If it equals to
            empty string(i.g. ""), the server description will be removed.
        """
        if name is None and description is None:
            return

        body = {"server": {}}
        if name:
            body["server"]["name"] = name
        if description == "":
            body["server"]["description"] = None
        elif description:
            body["server"]["description"] = description

        return self._update("/servers/%s" % base.getid(server), body, "server")

    def change_password(self, server, password):
        """
        Update the password for a server.

        :param server: The :class:`Server` (or its ID) for which the admin
                       password is to be changed
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action("changePassword", server, {"adminPass": password})

    def delete(self, server):
        """
        Delete (i.e. shut down and delete the image) this server.

        :param server: The :class:`Server` (or its ID) to delete
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete("/servers/%s" % base.getid(server))

    def reboot(self, server, reboot_type=REBOOT_SOFT):
        """
        Reboot a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param reboot_type: either :data:`REBOOT_SOFT` for a software-level
                reboot, or `REBOOT_HARD` for a virtual power cycle hard reboot.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('reboot', server, {'type': reboot_type})

    def rebuild(self, server, image, password=None, disk_config=None,
                preserve_ephemeral=False, name=None, meta=None, files=None,
                **kwargs):
        """
        Rebuild -- shut down and then re-image -- a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param image: the :class:`Image` (or its ID) to re-image with.
        :param password: string to set as password on the rebuilt server.
        :param disk_config: partitioning mode to use on the rebuilt server.
                            Valid values are 'AUTO' or 'MANUAL'
        :param preserve_ephemeral: If True, request that any ephemeral device
            be preserved when rebuilding the instance. Defaults to False.
        :param name: Something to name the server.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. Both keys and values must be <=255 characters.
        :param files: A dict of files to overwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.
        :param description: optional description of the server (allowed since
                            microversion 2.19)
        :returns: :class:`Server`
        """
        descr_microversion = api_versions.APIVersion("2.19")
        if "description" in kwargs and self.api_version < descr_microversion:
            raise exceptions.UnsupportedAttribute("description", "2.19")

        body = {'imageRef': base.getid(image)}
        if password is not None:
            body['adminPass'] = password
        if disk_config is not None:
            body['OS-DCF:diskConfig'] = disk_config
        if preserve_ephemeral is not False:
            body['preserve_ephemeral'] = True
        if name is not None:
            body['name'] = name
        if "description" in kwargs:
            body["description"] = kwargs["description"]
        if meta:
            body['metadata'] = meta
        if files:
            personality = body['personality'] = []
            for filepath, file_or_string in sorted(files.items(),
                                                   key=lambda x: x[0]):
                if hasattr(file_or_string, 'read'):
                    data = file_or_string.read()
                else:
                    data = file_or_string

                cont = base64.b64encode(data.encode('utf-8')).decode('utf-8')
                personality.append({
                    'path': filepath,
                    'contents': cont,
                })

        resp, body = self._action_return_resp_and_body('rebuild', server,
                                                       body, **kwargs)
        return Server(self, body['server'], resp=resp)

    def migrate(self, server):
        """
        Migrate a server to a new host.

        :param server: The :class:`Server` (or its ID).
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('migrate', server)

    def resize(self, server, flavor, disk_config=None, **kwargs):
        """
        Resize a server's resources.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param flavor: the :class:`Flavor` (or its ID) to resize to.
        :param disk_config: partitioning mode to use on the rebuilt server.
                            Valid values are 'AUTO' or 'MANUAL'
        :returns: An instance of novaclient.base.TupleWithMeta

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        info = {'flavorRef': base.getid(flavor)}
        if disk_config is not None:
            info['OS-DCF:diskConfig'] = disk_config

        return self._action('resize', server, info=info, **kwargs)

    def confirm_resize(self, server):
        """
        Confirm that the resize worked, thus removing the original server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('confirmResize', server)

    def revert_resize(self, server):
        """
        Revert a previous resize, switching back to the old server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('revertResize', server)

    def create_image(self, server, image_name, metadata=None):
        """
        Snapshot a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param image_name: Name to give the snapshot image
        :param metadata: Metadata to give newly-created image entity
        :returns: An instance of novaclient.base.StrWithMeta
                  (The snapshot image's UUID)
        """
        body = {'name': image_name, 'metadata': metadata or {}}
        resp, body = self._action_return_resp_and_body('createImage', server,
                                                       body)
        # The 2.45 microversion returns the image_id in the response body,
        # not as a location header.
        if self.api_version >= api_versions.APIVersion('2.45'):
            image_uuid = body['image_id']
        else:
            location = resp.headers['location']
            image_uuid = location.split('/')[-1]
        return base.StrWithMeta(image_uuid, resp)

    def backup(self, server, backup_name, backup_type, rotation):
        """
        Backup a server instance.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param backup_name: Name of the backup image
        :param backup_type: The backup type, like 'daily' or 'weekly'
        :param rotation: Int parameter representing how many backups to
                        keep around.
        :returns: An instance of novaclient.base.TupleWithMeta if the request
            microversion is < 2.45, otherwise novaclient.base.DictWithMeta.
        """
        body = {'name': backup_name,
                'backup_type': backup_type,
                'rotation': rotation}
        return self._action('createBackup', server, body)

    def set_meta(self, server, metadata):
        """
        Set a server's metadata
        :param server: The :class:`Server` to add metadata to
        :param metadata: A dict of metadata to be added to the server
        """
        body = {'metadata': metadata}
        return self._create("/servers/%s/metadata" % base.getid(server),
                            body, "metadata")

    def set_meta_item(self, server, key, value):
        """
        Updates an item of server metadata
        :param server: The :class:`Server` to add metadata to
        :param key: metadata key to update
        :param value: string value
        """
        body = {'meta': {key: value}}
        return self._update("/servers/%s/metadata/%s" %
                            (base.getid(server), key), body)

    def get_console_output(self, server, length=None):
        """
        Get text console log output from Server.

        :param server: The :class:`Server` (or its ID) whose console output
                        you would like to retrieve.
        :param length: The number of tail loglines you would like to retrieve.
        :returns: An instance of novaclient.base.StrWithMeta or
                  novaclient.base.UnicodeWithMeta
        """
        resp, body = self._action_return_resp_and_body('os-getConsoleOutput',
                                                       server,
                                                       {'length': length})
        return self.convert_into_with_meta(body['output'], resp)

    def delete_meta(self, server, keys):
        """
        Delete metadata from a server

        :param server: The :class:`Server` to add metadata to
        :param keys: A list of metadata keys to delete from the server
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        result = base.TupleWithMeta((), None)
        for k in keys:
            ret = self._delete("/servers/%s/metadata/%s" %
                               (base.getid(server), k))
            result.append_request_ids(ret.request_ids)

        return result

    @api_versions.wraps('2.0', '2.24')
    def live_migrate(self, server, host, block_migration, disk_over_commit):
        """
        Migrates a running instance to a new machine.

        :param server: instance id which comes from nova list.
        :param host: destination host name.
        :param block_migration: if True, do block_migration.
        :param disk_over_commit: if True, allow disk overcommit.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('os-migrateLive', server,
                            {'host': host,
                             'block_migration': block_migration,
                             'disk_over_commit': disk_over_commit})

    @api_versions.wraps('2.25', '2.29')
    def live_migrate(self, server, host, block_migration):
        """
        Migrates a running instance to a new machine.

        :param server: instance id which comes from nova list.
        :param host: destination host name.
        :param block_migration: if True, do block_migration, can be set as
                                'auto'
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('os-migrateLive', server,
                            {'host': host,
                             'block_migration': block_migration})

    @api_versions.wraps('2.30')
    def live_migrate(self, server, host, block_migration, force=None):
        """
        Migrates a running instance to a new machine.

        :param server: instance id which comes from nova list.
        :param host: destination host name.
        :param block_migration: if True, do block_migration, can be set as
                                'auto'
        :param force: forces to bypass the scheduler if host is provided.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        body = {'host': host, 'block_migration': block_migration}
        if force:
            body['force'] = force
        return self._action('os-migrateLive', server, body)

    def reset_state(self, server, state='error'):
        """
        Reset the state of an instance to active or error.

        :param server: ID of the instance to reset the state of.
        :param state: Desired state; either 'active' or 'error'.
                      Defaults to 'error'.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('os-resetState', server, dict(state=state))

    def reset_network(self, server):
        """
        Reset network of an instance.

        :param server: The :class:`Server` for network is to be reset
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('resetNetwork', server)

    def add_security_group(self, server, security_group):
        """
        Add a Security Group to an instance

        :param server: ID of the instance.
        :param security_group: The name of security group to add.
        :returns: An instance of novaclient.base.DictWithMeta
        """
        return self._action('addSecurityGroup', server,
                            {'name': security_group})

    def remove_security_group(self, server, security_group):
        """
        Remove a Security Group to an instance

        :param server: ID of the instance.
        :param security_group: The name of security group to remove.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._action('removeSecurityGroup', server,
                            {'name': security_group})

    def list_security_group(self, server):
        """
        List Security Group(s) of an instance

        :param server: ID of the instance.

        """
        return self._list('/servers/%s/os-security-groups' %
                          base.getid(server), 'security_groups',
                          SecurityGroup)

    @api_versions.wraps("2.0", "2.13")
    def evacuate(self, server, host=None, on_shared_storage=True,
                 password=None):
        """
        Evacuate a server instance.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param host: Name of the target host.
        :param on_shared_storage: Specifies whether instance files located
                        on shared storage
        :param password: string to set as password on the evacuated server.
        :returns: An instance of novaclient.base.TupleWithMeta
        """

        body = {'onSharedStorage': on_shared_storage}
        if host is not None:
            body['host'] = host

        if password is not None:
            body['adminPass'] = password

        resp, body = self._action_return_resp_and_body('evacuate', server,
                                                       body)
        return base.TupleWithMeta((resp, body), resp)

    @api_versions.wraps("2.14", "2.28")
    def evacuate(self, server, host=None, password=None):
        """
        Evacuate a server instance.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param host: Name of the target host.
        :param password: string to set as password on the evacuated server.
        :returns: An instance of novaclient.base.TupleWithMeta
        """

        body = {}
        if host is not None:
            body['host'] = host

        if password is not None:
            body['adminPass'] = password

        resp, body = self._action_return_resp_and_body('evacuate', server,
                                                       body)
        return base.TupleWithMeta((resp, body), resp)

    @api_versions.wraps("2.29")
    def evacuate(self, server, host=None, password=None, force=None):
        """
        Evacuate a server instance.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param host: Name of the target host.
        :param password: string to set as password on the evacuated server.
        :param force: forces to bypass the scheduler if host is provided.
        :returns: An instance of novaclient.base.TupleWithMeta
        """

        body = {}
        if host is not None:
            body['host'] = host

        if password is not None:
            body['adminPass'] = password

        if force:
            body['force'] = force

        resp, body = self._action_return_resp_and_body('evacuate', server,
                                                       body)
        return base.TupleWithMeta((resp, body), resp)

    def interface_list(self, server):
        """
        List attached network interfaces

        :param server: The :class:`Server` (or its ID) to query.
        """
        return self._list('/servers/%s/os-interface' % base.getid(server),
                          'interfaceAttachments', obj_class=NetworkInterface)

    def interface_attach(self, server, port_id, net_id, fixed_ip):
        """
        Attach a network_interface to an instance.

        :param server: The :class:`Server` (or its ID) to attach to.
        :param port_id: The port to attach.
        """

        body = {'interfaceAttachment': {}}
        if port_id:
            body['interfaceAttachment']['port_id'] = port_id
        if net_id:
            body['interfaceAttachment']['net_id'] = net_id
        if fixed_ip:
            body['interfaceAttachment']['fixed_ips'] = [
                {'ip_address': fixed_ip}]

        return self._create('/servers/%s/os-interface' % base.getid(server),
                            body, 'interfaceAttachment')

    def interface_detach(self, server, port_id):
        """
        Detach a network_interface from an instance.

        :param server: The :class:`Server` (or its ID) to detach from.
        :param port_id: The port to detach.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete('/servers/%s/os-interface/%s' %
                            (base.getid(server), port_id))

    @api_versions.wraps("2.17")
    def trigger_crash_dump(self, server):
        """Trigger crash dump in an instance"""
        return self._action("trigger_crash_dump", server)

    def _action(self, action, server, info=None, **kwargs):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        resp, body = self._action_return_resp_and_body(action, server,
                                                       info=info, **kwargs)
        return self.convert_into_with_meta(body, resp)

    def _action_return_resp_and_body(self, action, server, info=None,
                                     **kwargs):
        """
        Perform a server "action" and return response headers and body
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/servers/%s/action' % base.getid(server)
        return self.api.client.post(url, body=body)

    @api_versions.wraps('2.26')
    def tag_list(self, server):
        """
        Get list of tags from an instance.
        """
        resp, body = self.api.client.get(
            "/servers/%s/tags" % base.getid(server))
        return base.ListWithMeta(body['tags'], resp)

    @api_versions.wraps('2.26')
    def delete_tag(self, server, tag):
        """
        Remove single tag from an instance.
        """
        return self._delete("/servers/%s/tags/%s" % (base.getid(server), tag))

    @api_versions.wraps('2.26')
    def delete_all_tags(self, server):
        """
        Remove all tags from an instance.
        """
        return self._delete("/servers/%s/tags" % base.getid(server))

    @api_versions.wraps('2.26')
    def set_tags(self, server, tags):
        """
        Set list of tags to an instance.
        """
        body = {"tags": tags}
        return self._update("/servers/%s/tags" % base.getid(server), body)

    @api_versions.wraps('2.26')
    def add_tag(self, server, tag):
        """
        Add single tag to an instance.
        """
        return self._update(
            "/servers/%s/tags/%s" % (base.getid(server), tag), None)

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
Server interface.
"""

import urllib

from novaclient import base
from novaclient.v1_1 import base as local_base


REBOOT_SOFT, REBOOT_HARD = 'SOFT', 'HARD'


class Server(base.Resource):
    def __repr__(self):
        return "<Server: %s>" % self.name

    def delete(self):
        """
        Delete (i.e. shut down and delete the image) this server.
        """
        self.manager.delete(self)

    def update(self, name=None):
        """
        Update the name or the password for this server.

        :param name: Update the server's name.
        :param password: Update the root password.
        """
        self.manager.update(self, name=name)

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

    def add_fixed_ip(self, network_id):
        """
        Add an IP address on a network.

        :param network_id: The ID of the network the IP should be on.
        """
        self.manager.add_fixed_ip(self, network_id)

    def add_floating_ip(self, address):
        """
        Add floating IP to an instance

        :param address: The ip address or FloatingIP to add to the instance
        """
        self.manager.add_floating_ip(self, address)

    def remove_floating_ip(self, address):
        """
        Add floating IP to an instance

        :param address: The ip address or FloatingIP to add to remove
        """
        self.manager.remove_floating_ip(self, address)

    def pause(self):
        """
        Pause -- Pause the running server.
        """
        self.manager.pause(self)

    def unpause(self):
        """
        Unpause -- Unpause the paused server.
        """
        self.manager.unpause(self)

    def suspend(self):
        """
        Suspend -- Suspend the running server.
        """
        self.manager.suspend(self)

    def resume(self):
        """
        Resume -- Resume the suspended server.
        """
        self.manager.resume(self)

    def rescue(self):
        """
        Rescue -- Rescue the problematic server.
        """
        return self.manager.rescue(self)

    def unrescue(self):
        """
        Unrescue -- Unrescue the rescued server.
        """
        self.manager.unrescue(self)

    def diagnostics(self):
        """Diagnostics -- Retrieve server diagnostics."""
        return self.manager.diagnostics(self)

    def actions(self):
        """Actions -- Retrieve server actions."""
        return self.manager.actions(self)

    def migrate(self):
        """
        Migrate a server to a new host in the same zone.
        """
        self.manager.migrate(self)

    def remove_fixed_ip(self, address):
        """
        Remove an IP address.

        :param address: The IP address to remove.
        """
        self.manager.remove_fixed_ip(self, address)

    def change_password(self, password):
        """
        Update the password for a server.
        """
        self.manager.change_password(self, password)

    def reboot(self, type=REBOOT_SOFT):
        """
        Reboot the server.

        :param type: either :data:`REBOOT_SOFT` for a software-level reboot,
                     or `REBOOT_HARD` for a virtual power cycle hard reboot.
        """
        self.manager.reboot(self, type)

    def rebuild(self, image, password=None, **kwargs):
        """
        Rebuild -- shut down and then re-image -- this server.

        :param image: the :class:`Image` (or its ID) to re-image with.
        :param password: string to set as password on the rebuilt server.
        """
        return self.manager.rebuild(self, image, password=password, **kwargs)

    def resize(self, flavor, **kwargs):
        """
        Resize the server's resources.

        :param flavor: the :class:`Flavor` (or its ID) to resize to.

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        self.manager.resize(self, flavor, **kwargs)

    def create_image(self, image_name, metadata=None):
        """
        Create an image based on this server.

        :param image_name: The name to assign the newly create image.
        :param metadata: Metadata to assign to the image.
        """
        self.manager.create_image(self, image_name, metadata)

    def confirm_resize(self):
        """
        Confirm that the resize worked, thus removing the original server.
        """
        self.manager.confirm_resize(self)

    def revert_resize(self):
        """
        Revert a previous resize, switching back to the old server.
        """
        self.manager.revert_resize(self)

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

    def live_migrate(self, host,
                     block_migration=False,
                     disk_over_commit=False):
        """
        Migrates a running instance to a new machine.
        """
        self.manager.live_migrate(self, host,
                                  block_migration,
                                  disk_over_commit)


class ServerManager(local_base.BootingManagerWithFind):
    resource_class = Server

    def get(self, server):
        """
        Get a server.

        :param server: ID of the :class:`Server` to get.
        :rtype: :class:`Server`
        """
        return self._get("/servers/%s" % base.getid(server), "server")

    def list(self, detailed=True, search_opts=None):
        """
        Get a list of servers.
        Optional detailed returns details server info.
        Optional reservation_id only returns instances with that
        reservation_id.

        :rtype: list of :class:`Server`
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"
        return self._list("/servers%s%s" % (detail, query_string), "servers")

    def add_fixed_ip(self, server, network_id):
        """
        Add an IP address on a network.

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param network_id: The ID of the network the IP should be on.
        """
        self._action('addFixedIp', server, {'networkId': network_id})

    def remove_fixed_ip(self, server, address):
        """
        Remove an IP address.

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param address: The IP address to remove.
        """
        self._action('removeFixedIp', server, {'address': address})

    def add_floating_ip(self, server, address):
        """
        Add a floating ip to an instance

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param address: The FloatingIP or string floating address to add.
        """

        address = address.ip if hasattr(address, 'ip') else address
        self._action('addFloatingIp', server, {'address': address})

    def remove_floating_ip(self, server, address):
        """
        Remove a floating IP address.

        :param server: The :class:`Server` (or its ID) to remove an IP from.
        :param address: The FloatingIP or string floating address to remove.
        """

        address = address.ip if hasattr(address, 'ip') else address
        self._action('removeFloatingIp', server, {'address': address})

    def get_vnc_console(self, server, console_type):
        """
        Get a vnc console for an instance

        :param server: The :class:`Server` (or its ID) to add an IP to.
        :param console_type: Type of vnc console to get ('novnc' or 'xvpvnc')
        """

        return self._action('os-getVNCConsole', server,
                            {'type': console_type})[1]

    def pause(self, server):
        """
        Pause the server.
        """
        self._action('pause', server, None)

    def unpause(self, server):
        """
        Unpause the server.
        """
        self._action('unpause', server, None)

    def suspend(self, server):
        """
        Suspend the server.
        """
        self._action('suspend', server, None)

    def resume(self, server):
        """
        Resume the server.
        """
        self._action('resume', server, None)

    def rescue(self, server):
        """
        Rescue the server.
        """
        return self._action('rescue', server, None)

    def unrescue(self, server):
        """
        Unrescue the server.
        """
        self._action('unrescue', server, None)

    def diagnostics(self, server):
        """Retrieve server diagnostics."""
        return self.api.client.get("/servers/%s/diagnostics" %
                                   base.getid(server))

    def actions(self, server):
        """Retrieve server actions."""
        return self._list("/servers/%s/actions" % base.getid(server),
                          "actions")

    def create(self, name, image, flavor, meta=None, files=None,
               zone_blob=None, reservation_id=None, min_count=None,
               max_count=None, security_groups=None, userdata=None,
               key_name=None, availability_zone=None,
               block_device_mapping=None, nics=None, scheduler_hints=None,
               **kwargs):
        # TODO: (anthony) indicate in doc string if param is an extension
        # and/or optional
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param files: A dict of files to overrwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.
        :param zone_blob: a single (encrypted) string which is used internally
                      by Nova for routing between Zones. Users cannot populate
                      this field.
        :param userdata: user data to pass to be exposed by the metadata
                      server this can be a file type object as well or a
                      string.
        :param reservation_id: a UUID for the set of servers being requested.
        :param key_name: (optional extension) name of previously created
                      keypair to inject into the instance.
        :param availability_zone: The :class:`Zone`.
        :param block_device_mapping: (optional extension) A dict of block
                      device mappings for this server.
        :param nics:  (optional extension) an ordered list of nics to be
                      added to this server, with information about
                      connected networks, fixed ips, etc.
        :param scheduler_hints: (optional extension) arbitrary key-value pairs
                            specified by the client to help boot an instance
        """
        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        if min_count > max_count:
            min_count = max_count

        boot_args = [name, image, flavor]

        boot_kwargs = dict(
            meta=meta, files=files, userdata=userdata, zone_blob=zone_blob,
            reservation_id=reservation_id, min_count=min_count,
            max_count=max_count, security_groups=security_groups,
            key_name=key_name, availability_zone=availability_zone,
            scheduler_hints=scheduler_hints, **kwargs)

        if block_device_mapping:
            resource_url = "/os-volumes_boot"
            boot_kwargs['block_device_mapping'] = block_device_mapping
        else:
            resource_url = "/servers"
            boot_kwargs['nics'] = nics

        response_key = "server"
        return self._boot(resource_url, response_key, *boot_args,
                **boot_kwargs)

    def update(self, server, name=None):
        """
        Update the name or the password for a server.

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

        self._update("/servers/%s" % base.getid(server), body)

    def change_password(self, server, password):
        """
        Update the password for a server.
        """
        self._action("changePassword", server, {"adminPass": password})

    def delete(self, server):
        """
        Delete (i.e. shut down and delete the image) this server.
        """
        self._delete("/servers/%s" % base.getid(server))

    def reboot(self, server, type=REBOOT_SOFT):
        """
        Reboot a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param type: either :data:`REBOOT_SOFT` for a software-level reboot,
                     or `REBOOT_HARD` for a virtual power cycle hard reboot.
        """
        self._action('reboot', server, {'type': type})

    def rebuild(self, server, image, password=None, **kwargs):
        """
        Rebuild -- shut down and then re-image -- a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param image: the :class:`Image` (or its ID) to re-image with.
        :param password: string to set as password on the rebuilt server.
        """
        body = {'imageRef': base.getid(image)}
        if password is not None:
            body['adminPass'] = password
        resp, body = self._action('rebuild', server, body, **kwargs)
        return Server(self, body['server'])

    def migrate(self, server):
        """
        Migrate a server to a new host in the same zone.

        :param server: The :class:`Server` (or its ID).
        """
        self._action('migrate', server)

    def resize(self, server, flavor, **kwargs):
        """
        Resize a server's resources.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param flavor: the :class:`Flavor` (or its ID) to resize to.

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        info = {'flavorRef': base.getid(flavor)}
        self._action('resize', server, info=info, **kwargs)

    def confirm_resize(self, server):
        """
        Confirm that the resize worked, thus removing the original server.

        :param server: The :class:`Server` (or its ID) to share onto.
        """
        self._action('confirmResize', server)

    def revert_resize(self, server):
        """
        Revert a previous resize, switching back to the old server.

        :param server: The :class:`Server` (or its ID) to share onto.
        """
        self._action('revertResize', server)

    def create_image(self, server, image_name, metadata=None):
        """
        Snapshot a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param image_name: Name to give the snapshot image
        :param meta: Metadata to give newly-created image entity
        """
        self._action('createImage', server,
                     {'name': image_name, 'metadata': metadata or {}})

    def set_meta(self, server, metadata):
        """
        Set a servers metadata
        :param server: The :class:`Server` to add metadata to
        :param metadata: A dict of metadata to add to the server
        """
        body = {'metadata': metadata}
        return self._create("/servers/%s/metadata" % base.getid(server),
                             body, "metadata")

    def get_console_output(self, server, length=None):
        """
        Get text console log output from Server.

        :param server: The :class:`Server` (or its ID) whose console output
                        you would like to retrieve.
        :param length: The number of tail loglines you would like to retrieve.
        """
        return self._action('os-getConsoleOutput',
                            server,
                            {'length': length})[1]['output']

    def delete_meta(self, server, keys):
        """
        Delete metadata from an server
        :param server: The :class:`Server` to add metadata to
        :param keys: A list of metadata keys to delete from the server
        """
        for k in keys:
            self._delete("/servers/%s/metadata/%s" % (base.getid(server), k))

    def live_migrate(self, server, host, block_migration, disk_over_commit):
        """
        Migrates a running instance to a new machine.

        :param server: instance id which comes from nova list.
        :param host: destination host name.
        :param block_migration: if True, do block_migration.
        :param disk_over_commit: if True, Allow overcommit.

        """
        self._action('os-migrateLive', server,
                     {'host': host,
                      'block_migration': block_migration,
                      'disk_over_commit': disk_over_commit})

    def _action(self, action, server, info=None, **kwargs):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/servers/%s/action' % base.getid(server)
        return self.api.client.post(url, body=body)

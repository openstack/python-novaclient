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

from novaclient import base

REBOOT_SOFT, REBOOT_HARD = 'SOFT', 'HARD'


class Server(base.Resource):
    def __repr__(self):
        return "<Server: %s>" % self.name

    def delete(self):
        """
        Delete (i.e. shut down and delete the image) this server.
        """
        self.manager.delete(self)

    def update(self, name=None, password=None):
        """
        Update the name or the password for this server.

        :param name: Update the server's name.
        :param password: Update the root password.
        """
        self.manager.update(self, name, password)

    def share_ip(self, ipgroup, address, configure=True):
        """
        Share an IP address from the given IP group onto this server.

        :param ipgroup: The :class:`IPGroup` that the given address belongs to.
        :param address: The IP address to share.
        :param configure: If ``True``, the server will be automatically
                         configured to use this IP. I don't know why you'd
                         want this to be ``False``.
        """
        self.manager.share_ip(self, ipgroup, address, configure)

    def unshare_ip(self, address):
        """
        Stop sharing the given address.

        :param address: The IP address to stop sharing.
        """
        self.manager.unshare_ip(self, address)

    def reboot(self, type=REBOOT_SOFT):
        """
        Reboot the server.

        :param type: either :data:`REBOOT_SOFT` for a software-level reboot,
                     or `REBOOT_HARD` for a virtual power cycle hard reboot.
        """
        self.manager.reboot(self, type)

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
        self.manager.rescue(self)

    def unrescue(self):
        """
        Unrescue -- Unrescue the rescued server.
        """
        self.manager.unrescue(self)

    def diagnostics(self):
        """Diagnostics -- Retrieve server diagnostics."""
        self.manager.diagnostics(self)

    def actions(self):
        """Actions -- Retrieve server actions."""
        self.manager.actions(self)

    def rebuild(self, image):
        """
        Rebuild -- shut down and then re-image -- this server.

        :param image: the :class:`Image` (or its ID) to re-image with.
        """
        self.manager.rebuild(self, image)

    def resize(self, flavor):
        """
        Resize the server's resources.

        :param flavor: the :class:`Flavor` (or its ID) to resize to.

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        self.manager.resize(self, flavor)

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
    def backup_schedule(self):
        """
        This server's :class:`BackupSchedule`.
        """
        return self.manager.api.backup_schedules.get(self)

    @property
    def public_ip(self):
        """
        Shortcut to get this server's primary public IP address.
        """
        if len(self.addresses['public']) == 0:
            return ""
        return self.addresses['public'][0]

    @property
    def private_ip(self):
        """
        Shortcut to get this server's primary private IP address.
        """
        if len(self.addresses['private']) == 0:
            return ""
        return self.addresses['private'][0]


class ServerManager(base.ManagerWithFind):
    resource_class = Server

    def get(self, server):
        """
        Get a server.

        :param server: ID of the :class:`Server` to get.
        :rtype: :class:`Server`
        """
        return self._get("/servers/%s" % base.getid(server), "server")

    def list(self, detailed=True):
        """
        Get a list of servers.
        :rtype: list of :class:`Server`
        """
        detail = ""
        if detailed:
            detail = "/detail"
        return self._list("/servers%s" % detail, "servers")


    def create(self, name, image, flavor, ipgroup=None, meta=None, files=None):
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param ipgroup: An initial :class:`IPGroup` for this server.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param files: A dict of files to overrwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.

        There's a bunch more info about how a server boots in Rackspace's
        official API docs, page 23.
        """
        body = {"server": {
            "name": name,
            "imageId": base.getid(image),
            "flavorId": base.getid(flavor),
        }}
        if ipgroup:
            body["server"]["sharedIpGroupId"] = base.getid(ipgroup)
        if meta:
            body["server"]["metadata"] = meta

        # Files are a slight bit tricky. They're passed in a "personality"
        # list to the POST. Each item is a dict giving a file name and the
        # base64-encoded contents of the file. We want to allow passing
        # either an open file *or* some contents as files here.
        if files:
            personality = body['server']['personality'] = []
            for filepath, file_or_string in files.items():
                if hasattr(file_or_string, 'read'):
                    data = file_or_string.read()
                else:
                    data = file_or_string
                personality.append({
                    'path': filepath,
                    'contents': data.encode('base64'),
                })

        return self._create("/servers", body, "server")

    def update(self, server, name=None, password=None):
        """
        Update the name or the password for a server.

        :param server: The :class:`Server` (or its ID) to update.
        :param name: Update the server's name.
        :param password: Update the root password.
        """

        if name is None and password is None:
            return
        body = {"server": {}}
        if name:
            body["server"]["name"] = name
        if password:
            body["server"]["adminPass"] = password
        self._update("/servers/%s" % base.getid(server), body)

    def delete(self, server):
        """
        Delete (i.e. shut down and delete the image) this server.
        """
        self._delete("/servers/%s" % base.getid(server))

    def share_ip(self, server, ipgroup, address, configure=True):
        """
        Share an IP address from the given IP group onto a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param ipgroup: The :class:`IPGroup` that the given address belongs to.
        :param address: The IP address to share.
        :param configure: If ``True``, the server will be automatically
                         configured to use this IP. I don't know why you'd
                         want this to be ``False``.
        """
        server = base.getid(server)
        ipgroup = base.getid(ipgroup)
        body = {'shareIp': {'sharedIpGroupId': ipgroup,
                            'configureServer': configure}}
        self._update("/servers/%s/ips/public/%s" % (server, address), body)

    def unshare_ip(self, server, address):
        """
        Stop sharing the given address.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param address: The IP address to stop sharing.
        """
        server = base.getid(server)
        self._delete("/servers/%s/ips/public/%s" % (server, address))

    def reboot(self, server, type=REBOOT_SOFT):
        """
        Reboot a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param type: either :data:`REBOOT_SOFT` for a software-level reboot,
                     or `REBOOT_HARD` for a virtual power cycle hard reboot.
        """
        self._action('reboot', server, {'type': type})

    def rebuild(self, server, image):
        """
        Rebuild -- shut down and then re-image -- a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param image: the :class:`Image` (or its ID) to re-image with.
        """
        self._action('rebuild', server, {'imageId': base.getid(image)})

    def resize(self, server, flavor):
        """
        Resize a server's resources.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param flavor: the :class:`Flavor` (or its ID) to resize to.

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        self._action('resize', server, {'flavorId': base.getid(flavor)})

    def pause(self, server):
        """
        Pause the server.
        """
        self.api.client.post('/servers/%s/pause' % base.getid(server), body={})

    def unpause(self, server):
        """
        Unpause the server.
        """
        self.api.client.post('/servers/%s/unpause' % base.getid(server),
                             body={})

    def suspend(self, server):
        """
        Suspend the server.
        """
        self.api.client.post('/servers/%s/suspend' % base.getid(server),
                             body={})

    def resume(self, server):
        """
        Resume the server.
        """
        self.api.client.post('/servers/%s/resume' % base.getid(server),
                             body={})

    def rescue(self, server):
        """
        Rescue the server.
        """
        self.api.client.post('/servers/%s/rescue' % base.getid(server),
                             body={})

    def unrescue(self, server):
        """
        Unrescue the server.
        """
        self.api.client.post('/servers/%s/unrescue' % base.getid(server),
                             body={})

    def diagnostics(self, server):
        """Retrieve server diagnostics."""
        return self.api.client.get("/servers/%s/diagnostics" %
                                   base.getid(server))

    def actions(self, server):
        """Retrieve server actions."""
        return self._list("/servers/%s/actions" % base.getid(server),
                          "actions")

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

    def _action(self, action, server, info=None):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        self.api.client.post('/servers/%s/action' % base.getid(server),
                             body={action: info})

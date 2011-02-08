from novatools import base


class Zone(base.Resource):
    def __repr__(self):
        return "<Zone: %s>" % self.name

    def delete(self):
        """
        Delete a child zone.
        """
        self.manager.delete(self)

    def update(self, name=None):
        """
        Update the name for this child zone.

        :param name: Update the child zone's name.
        """
        self.manager.update(self, name)


class ServerManager(base.ManagerWithFind):
    resource_class = Zone

    def get(self, zone):
        """
        Get a child zone.

        :param server: ID of the :class:`Zone` to get.
        :rtype: :class:`Zone`
        """
        return self._get("/zones/%s" % base.getid(zone), "zone")

    def list(self):
        """
        Get a list of child zones.
        :rtype: list of :class:`Zone`
        """
        return self._list("/zones/detail", "zones")

    def create(self, name, image, flavor, ipgroup=None, meta=None, files=None):
        """
        Create a new child zone.

        :param name: Something to name the zone.
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
        body = {"zone": {
            "name": name,
            "imageId": base.getid(image),
            "flavorId": base.getid(flavor),
        }}
        if ipgroup:
            body["zone"]["sharedIpGroupId"] = base.getid(ipgroup)
        if meta:
            body["zone"]["metadata"] = meta

        # Files are a slight bit tricky. They're passed in a "personality"
        # list to the POST. Each item is a dict giving a file name and the
        # base64-encoded contents of the file. We want to allow passing
        # either an open file *or* some contents as files here.
        if files:
            personality = body['zone']['personality'] = []
            for filepath, file_or_string in files.items():
                if hasattr(file_or_string, 'read'):
                    data = file_or_string.read()
                else:
                    data = file_or_string
                personality.append({
                    'path': filepath,
                    'contents': data.encode('base64'),
                })

        return self._create("/zones", body, "zone")

    def delete(self, zone):
        """
        Delete a child zone.
        """
        self._delete("/zones/%s" % base.getid(zone))


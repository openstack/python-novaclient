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

    def create(self, name, auth_url):
        """
        Create a new child zone.

        :param name: Something to name the zone.
        """
        body = {"zone": {
            "name": name,
            "auth_url": auth_url,
        }}

        return self._create("/zones", body, "zone")

    def delete(self, zone):
        """
        Delete a child zone.
        """
        self._delete("/zones/%s" % base.getid(zone))


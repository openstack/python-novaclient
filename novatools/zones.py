from novatools import base


class Zone(base.Resource):
    def __repr__(self):
        return "<Zone: %s>" % self.api_url

    def delete(self):
        """
        Delete a child zone.
        """
        self.manager.delete(self)

    def update(self, api_url=None, username=None, password=None):
        """
        Update the name for this child zone.

        :param api_url: Update the child zone's API URL.
        :param username: Update the child zone's username.
        :param password: Update the child zone's password.
        """
        self.manager.update(self, api_url, username, password)


class ZoneManager(base.ManagerWithFind):
    resource_class = Zone

    def info(self):
        """
        Get info on this zone.

        :rtype: :class:`Zone`
        """
        return self._get("/zones/info", "zone")

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

    def create(self, api_url, username, password):
        """
        Create a new child zone.

        :param api_url: The child zone's API URL.
        :param username: The child zone's username.
        :param password: The child zone's password.
        """
        body = {"zone": {
            "api_url": api_url,
            "username": username,
            "password": password,
        }}

        return self._create("/zones", body, "zone")

    def delete(self, zone):
        """
        Delete a child zone.
        """
        self._delete("/zones/%s" % base.getid(zone))

    def update(self, zone, api_url=None, username=None, password=None):
        """
        Update the name or the api_url for a zone.

        :param zone: The :class:`Zone` (or its ID) to update.
        :param api_url: Update the API URL.
        :param username: Update the username.
        :param password: Update the password.
        """

        body = {"zone": {}}
        if api_url:
            body["zone"]["api_url"] = api_url
        if username:
            body["zone"]["username"] = username
        if password:
            body["zone"]["password"] = password

        if not len(body["zone"]):
            return
        self._update("/zones/%s" % base.getid(zone), body)

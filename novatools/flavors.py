from novatools import base


class Flavor(base.Resource):
    """
    A flavor is an available hardware configuration for a server.
    """
    def __repr__(self):
        return "<Flavor: %s>" % self.name


class FlavorManager(base.ManagerWithFind):
    """
    Manage :class:`Flavor` resources.
    """
    resource_class = Flavor

    def list(self):
        """
        Get a list of all flavors.

        :rtype: list of :class:`Flavor`.
        """
        return self._list("/flavors/detail", "flavors")

    def get(self, flavor):
        """
        Get a specific flavor.

        :param flavor: The ID of the :class:`Flavor` to get.
        :rtype: :class:`Flavor`
        """
        return self._get("/flavors/%s" % base.getid(flavor), "flavor")

# Copyright 2010 Jacob Kaplan-Moss
"""
Flavor interface.
"""

from novaclient import base
from novaclient import exceptions


class Flavor(base.Resource):
    """
    A flavor is an available hardware configuration for a server.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Flavor: %s>" % self.name

    @property
    def ephemeral(self):
        """
        Provide a user-friendly accessor to OS-FLV-EXT-DATA:ephemeral
        """
        return self._info.get("OS-FLV-EXT-DATA:ephemeral", 'N/A')

    @property
    def is_public(self):
        """
        Provide a user-friendly accessor to os-flavor-access:is_public
        """
        return self._info.get("os-flavor-access:is_public", 'N/A')

    def get_keys(self):
        """
        Get extra specs from a flavor.

        :param flavor: The :class:`Flavor` to get extra specs from
        """
        _resp, body = self.manager.api.client.get(
                            "/flavors/%s/os-extra_specs" %
                            base.getid(self))
        return body["extra_specs"]

    def set_keys(self, metadata):
        """
        Set extra specs on a flavor.

        :param flavor: The :class:`Flavor` to set extra spec on
        :param metadata: A dict of key/value pairs to be set
        """
        body = {'extra_specs': metadata}
        return self.manager._create(
                            "/flavors/%s/os-extra_specs" % base.getid(self),
                            body,
                            "extra_specs",
                            return_raw=True)

    def unset_keys(self, keys):
        """
        Unset extra specs on a flavor.

        :param flavor: The :class:`Flavor` to unset extra spec on
        :param keys: A list of keys to be unset
        """
        for k in keys:
            return self.manager._delete(
                            "/flavors/%s/os-extra_specs/%s" % (
                            base.getid(self), k))


class FlavorManager(base.ManagerWithFind):
    """
    Manage :class:`Flavor` resources.
    """
    resource_class = Flavor

    def list(self, detailed=True):
        """
        Get a list of all flavors.

        :rtype: list of :class:`Flavor`.
        """
        if detailed is True:
            return self._list("/flavors/detail", "flavors")
        else:
            return self._list("/flavors", "flavors")

    def get(self, flavor):
        """
        Get a specific flavor.

        :param flavor: The ID of the :class:`Flavor` to get.
        :rtype: :class:`Flavor`
        """
        return self._get("/flavors/%s" % base.getid(flavor), "flavor")

    def delete(self, flavor):
        """
        Delete a specific flavor.

        :param flavor: The ID of the :class:`Flavor` to get.
        :param purge: Whether to purge record from the database
        """
        self._delete("/flavors/%s" % base.getid(flavor))

    def create(self, name, ram, vcpus, disk, flavorid,
               ephemeral=0, swap=0, rxtx_factor=1, is_public=True):
        """
        Create (allocate) a  floating ip for a tenant

        :param name: Descriptive name of the flavor
        :param ram: Memory in MB for the flavor
        :param vcpu: Number of VCPUs for the flavor
        :param disk: Size of local disk in GB
        :param flavorid: Integer ID for the flavor
        :param swap: Swap space in MB
        :param rxtx_factor: RX/TX factor
        :rtype: :class:`Flavor`
        """

        body = {
            "flavor": {
                "name": name,
                "ram": int(ram),
                "vcpus": int(vcpus),
                "disk": int(disk),
                "id": int(flavorid),
                "swap": int(swap),
                "OS-FLV-EXT-DATA:ephemeral": int(ephemeral),
                "rxtx_factor": int(rxtx_factor),
                "os-flavor-access:is_public": bool(is_public),
            }
        }

        return self._create("/flavors", body, "flavor")

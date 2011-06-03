# Copyright 2010 Jacob Kaplan-Moss
"""
IP Group interface.
"""

from novaclient import base


class IPGroup(base.Resource):
    def __repr__(self):
        return "<IP Group: %s>" % self.name

    def delete(self):
        """
        Delete this group.
        """
        self.manager.delete(self)


class IPGroupManager(base.ManagerWithFind):
    resource_class = IPGroup

    def list(self, detailed=True):
        """
        Get a list of all groups.

        :rtype: list of :class:`IPGroup`
        """
        detail = ""
        if detailed:
            detail = "/detail"
        return self._list("/shared_ip_groups%s" % detail, "sharedIpGroups")

    def get(self, group):
        """
        Get an IP group.

        :param group: ID of the image to get.
        :rtype: :class:`IPGroup`
        """
        return self._get("/shared_ip_groups/%s" % base.getid(group),
                         "sharedIpGroup")

    def create(self, name, server=None):
        """
        Create a new :class:`IPGroup`

        :param name: An (arbitrary) name for the new image.
        :param server: A :class:`Server` (or its ID) to make a member
                       of this group.
        :rtype: :class:`IPGroup`
        """
        data = {"sharedIpGroup": {"name": name}}
        if server:
            data['sharedIpGroup']['server'] = base.getid(server)
        return self._create('/shared_ip_groups', data, "sharedIpGroup")

    def delete(self, group):
        """
        Delete a group.

        :param group: The :class:`IPGroup` (or its ID) to delete.
        """
        self._delete("/shared_ip_groups/%s" % base.getid(group))

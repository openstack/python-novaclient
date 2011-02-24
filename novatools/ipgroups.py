# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
IP Group interface.
"""

from novatools import base


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

    def list(self):
        """
        Get a list of all groups.

        :rtype: list of :class:`IPGroup`
        """
        return self._list("/shared_ip_groups/detail", "sharedIpGroups")

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

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
Flavor interface.
"""


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

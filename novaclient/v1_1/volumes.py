# Copyright 2011 Denali Systems, Inc.
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
Volume interface (1.1 extension).
"""

from novaclient import base


class Volume(base.Resource):
    """
    A volume is an extra block level storage to the OpenStack instances.
    """
    def __repr__(self):
        return "<Volume: %s>" % self.id

    def delete(self):
        """
        Delete this volume.
        """
        return self.manager.delete(self)


class VolumeManager(base.ManagerWithFind):
    """
    Manage :class:`Volume` resources.
    """
    resource_class = Volume

    def create(self, size, display_name=None, display_description=None):
        """
        Create a volume.

        :param size: Size of volume in GB
        :param display_name: Name of the volume
        :param display_description: Description of the volume
        :rtype: :class:`Volume`
        """
        body = {'volume': {'size': size,
                            'display_name': display_name,
                            'display_description': display_description}}
        return self._create('/os-volumes', body, 'volume')

    def get(self, volume_id):
        """
        Get a volume.

        :param volume_id: The ID of the volume to delete.
        :rtype: :class:`Volume`
        """
        return self._get("/os-volumes/%s" % base.getid(volume), "volume")

    def list(self, detailed=True):
        """
        Get a list of all volumes.

        :rtype: list of :class:`Volume`
        """
        if detailed is True:
            return self._list("/os-volumes/detail", "volumes")
        else:
            return self._list("/os-volumes", "volumes")

    def delete(self, volume):
        """
        Delete a volume.

        :param volume: The :class:`Volume` to delete.
        """
        self._delete("/os-volumes/%s" % base.getid(volume))

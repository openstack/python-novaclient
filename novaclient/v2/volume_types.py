# Copyright (c) 2011 Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
DEPRECATED: Volume Type interface.
"""

import warnings

from novaclient import base


class VolumeType(base.Resource):
    """
    DEPRECATED: A Volume Type is the type of volume to be created
    """
    def __repr__(self):
        return "<Volume Type: %s>" % self.name


class VolumeTypeManager(base.ManagerWithFind):
    """
    DEPRECATED: Manage :class:`VolumeType` resources.
    """
    resource_class = VolumeType

    def list(self):
        """
        DEPRECATED: Get a list of all volume types.

        :rtype: list of :class:`VolumeType`.
        """
        warnings.warn('The novaclient.v2.volume_types module is deprecated '
                      'and will be removed after Nova 13.0.0 is released. Use '
                      'python-cinderclient or python-openstacksdk instead.',
                      DeprecationWarning)
        with self.alternate_service_type(
                'volumev2', allowed_types=('volume', 'volumev2')):
            return self._list("/types", "volume_types")

    def get(self, volume_type):
        """
        DEPRECATED: Get a specific volume type.

        :param volume_type: The ID of the :class:`VolumeType` to get.
        :rtype: :class:`VolumeType`
        """
        warnings.warn('The novaclient.v2.volume_types module is deprecated '
                      'and will be removed after Nova 13.0.0 is released. Use '
                      'python-cinderclient or python-openstacksdk instead.',
                      DeprecationWarning)
        with self.alternate_service_type(
                'volumev2', allowed_types=('volume', 'volumev2')):
            return self._get("/types/%s" % base.getid(volume_type),
                             "volume_type")

    def delete(self, volume_type):
        """
        DEPRECATED: Delete a specific volume_type.

        :param volume_type: The ID of the :class:`VolumeType` to get.
        """
        warnings.warn('The novaclient.v2.volume_types module is deprecated '
                      'and will be removed after Nova 13.0.0 is released. Use '
                      'python-cinderclient or python-openstacksdk instead.',
                      DeprecationWarning)
        with self.alternate_service_type(
                'volumev2', allowed_types=('volume', 'volumev2')):
            self._delete("/types/%s" % base.getid(volume_type))

    def create(self, name):
        """
        DEPRECATED: Create a volume type.

        :param name: Descriptive name of the volume type
        :rtype: :class:`VolumeType`
        """
        warnings.warn('The novaclient.v2.volume_types module is deprecated '
                      'and will be removed after Nova 13.0.0 is released. Use '
                      'python-cinderclient or python-openstacksdk instead.',
                      DeprecationWarning)
        with self.alternate_service_type(
                'volumev2', allowed_types=('volume', 'volumev2')):
            body = {
                "volume_type": {
                    "name": name,
                }
            }
            return self._create("/types", body, "volume_type")

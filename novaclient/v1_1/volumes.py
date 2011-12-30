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
        self.manager.delete(self)


class VolumeManager(base.ManagerWithFind):
    """
    Manage :class:`Volume` resources.
    """
    resource_class = Volume

    def create(self, size, snapshot_id=None,
                    display_name=None, display_description=None):
        """
        Create a volume.

        :param size: Size of volume in GB
        :param snapshot_id: ID of the snapshot
        :param display_name: Name of the volume
        :param display_description: Description of the volume
        :rtype: :class:`Volume`
        """
        body = {'volume': {'size': size,
                            'snapshot_id': snapshot_id,
                            'display_name': display_name,
                            'display_description': display_description}}
        return self._create('/os-volumes', body, 'volume')

    def get(self, volume_id):
        """
        Get a volume.

        :param volume_id: The ID of the volume to delete.
        :rtype: :class:`Volume`
        """
        return self._get("/os-volumes/%s" % volume_id, "volume")

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

    def create_server_volume(self, server_id, volume_id, device):
        """
        Attach a volume identified by the volume ID to the given server ID

        :param server_id: The ID of the server
        :param volume_id: The ID of the volume to attach.
        :param device: The device name
        :rtype: :class:`Volume`
        """
        body = {'volumeAttachment': {'volumeId': volume_id,
                            'device': device}}
        return self._create("/servers/%s/os-volume_attachments" % server_id,
            body, "volumeAttachment")

    def get_server_volume(self, server_id, attachment_id):
        """
        Get the volume identified by the attachment ID, that is attached to
        the given server ID

        :param server_id: The ID of the server
        :param attachment_id: The ID of the attachment
        :rtype: :class:`Volume`
        """
        return self._get("/servers/%s/os-volume_attachments/%s" % (server_id,
            attachment_id,), "volumeAttachment")

    def get_server_volumes(self, server_id):
        """
        Get a list of all the attached volumes for the given server ID

        :param server_id: The ID of the server
        :rtype: list of :class:`Volume`
        """
        return self._list("/servers/%s/os-volume_attachments" % server_id,
            "volumeAttachments")

    def delete_server_volume(self, server_id, attachment_id):
        """
        Detach a volume identified by the attachment ID from the given server

        :param server_id: The ID of the server
        :param attachment_id: The ID of the attachment
        """
        self._delete("/servers/%s/os-volume_attachments/%s" %
                                        (server_id, attachment_id,))

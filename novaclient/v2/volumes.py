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
Volume interface
"""
import warnings

from novaclient import api_versions
from novaclient import base


class Volume(base.Resource):
    """
    A volume is an extra block level storage to the OpenStack
    instances.
    """
    NAME_ATTR = 'display_name'

    def __repr__(self):
        return "<Volume: %s>" % self.id


class VolumeManager(base.Manager):
    """
    Manage :class:`Volume` resources. This is really about volume attachments.
    """
    resource_class = Volume

    @api_versions.wraps("2.0", "2.48")
    def create_server_volume(self, server_id, volume_id, device=None):
        """
        Attach a volume identified by the volume ID to the given server ID

        :param server_id: The ID of the server
        :param volume_id: The ID of the volume to attach.
        :param device: The device name (optional)
        :rtype: :class:`Volume`
        """
        body = {'volumeAttachment': {'volumeId': volume_id}}
        if device is not None:
            body['volumeAttachment']['device'] = device
        return self._create("/servers/%s/os-volume_attachments" % server_id,
                            body, "volumeAttachment")

    @api_versions.wraps("2.49")
    def create_server_volume(self, server_id, volume_id, device=None,
                             tag=None):
        """
        Attach a volume identified by the volume ID to the given server ID

        :param server_id: The ID of the server
        :param volume_id: The ID of the volume to attach.
        :param device: The device name (optional)
        :param tag: The tag (optional)
        :rtype: :class:`Volume`
        """
        body = {'volumeAttachment': {'volumeId': volume_id}}
        if device is not None:
            body['volumeAttachment']['device'] = device
        if tag is not None:
            body['volumeAttachment']['tag'] = tag
        return self._create("/servers/%s/os-volume_attachments" % server_id,
                            body, "volumeAttachment")

    def update_server_volume(self, server_id, src_volid, dest_volid):
        """
        Swaps the existing volume attachment to point to a new volume.

        Takes a server, a source (attached) volume and a destination volume and
        performs a hypervisor assisted data migration from src to dest volume,
        detaches the original (source) volume and attaches the new destination
        volume. Note that not all backing hypervisor drivers support this
        operation and it may be disabled via policy.


        :param server_id: The ID of the server
        :param source_volume: The ID of the src volume
        :param dest_volume: The ID of the destination volume
        :rtype: :class:`Volume`
        """
        body = {'volumeAttachment': {'volumeId': dest_volid}}
        return self._update("/servers/%s/os-volume_attachments/%s" %
                            (server_id, src_volid,),
                            body, "volumeAttachment")

    def get_server_volume(self, server_id, volume_id=None, attachment_id=None):
        """
        Get the volume identified by the volume ID, that is attached to
        the given server ID

        :param server_id: The ID of the server
        :param volume_id: The ID of the volume to attach
        :rtype: :class:`Volume`
        """

        if attachment_id is not None and volume_id is not None:
            raise TypeError("You cannot specify both volume_id "
                            "and attachment_id arguments.")

        elif attachment_id is not None:
            warnings.warn("attachment_id argument "
                          "of volumes.get_server_volume "
                          "method is deprecated in favor "
                          "of volume_id.")
            volume_id = attachment_id

        if volume_id is None:
            raise TypeError("volume_id is required argument.")

        return self._get("/servers/%s/os-volume_attachments/%s" % (server_id,
                         volume_id,), "volumeAttachment")

    def get_server_volumes(self, server_id):
        """
        Get a list of all the attached volumes for the given server ID

        :param server_id: The ID of the server
        :rtype: list of :class:`Volume`
        """
        return self._list("/servers/%s/os-volume_attachments" % server_id,
                          "volumeAttachments")

    def delete_server_volume(self, server_id, volume_id=None,
                             attachment_id=None):
        """
        Detach a volume identified by the volume ID from the given server

        :param server_id: The ID of the server
        :param volume_id: The ID of the volume to attach
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        if attachment_id is not None and volume_id is not None:
            raise TypeError("You cannot specify both volume_id "
                            "and attachment_id arguments.")

        elif attachment_id is not None:
            warnings.warn("attachment_id argument "
                          "of volumes.delete_server_volume "
                          "method is deprecated in favor "
                          "of volume_id.")
            volume_id = attachment_id

        if volume_id is None:
            raise TypeError("volume_id is required argument.")

        return self._delete("/servers/%s/os-volume_attachments/%s" %
                            (server_id, volume_id,))

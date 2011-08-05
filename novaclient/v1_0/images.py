# Copyright 2010 Jacob Kaplan-Moss
"""
Image interface.
"""

from novaclient import base


class Image(base.Resource):
    """
    An image is a collection of files used to create or rebuild a server.
    """
    def __repr__(self):
        return "<Image: %s>" % self.name

    def delete(self):
        """
        Delete this image.
        """
        return self.manager.delete(self)


class ImageManager(base.ManagerWithFind):
    """
    Manage :class:`Image` resources.
    """
    resource_class = Image

    def get(self, image):
        """
        Get an image.

        :param image: The ID of the image to get.
        :rtype: :class:`Image`
        """
        return self._get("/images/%s" % base.getid(image), "image")

    def list(self, detailed=True):
        """
        Get a list of all images.

        :rtype: list of :class:`Image`
        """
        detail = ""
        if detailed:
            detail = "/detail"
        return self._list("/images%s" % detail, "images")

    def create(self, server, name):
        """
        Create a new image by snapshotting a running :class:`Server`

        :param name: An (arbitrary) name for the new image.
        :param server: The :class:`Server` (or its ID) to make a snapshot of.
        :rtype: :class:`Image`
        """
        data = {"image": {"serverId": base.getid(server), "name": name}}
        return self._create("/images", data, "image")

    def delete(self, image):
        """
        Delete an image.

        It should go without saying that you can't delete an image
        that you didn't create.

        :param image: The :class:`Image` (or its ID) to delete.
        """
        self._delete("/images/%s" % base.getid(image))

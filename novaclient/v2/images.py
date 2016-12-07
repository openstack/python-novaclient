# Copyright 2010 Jacob Kaplan-Moss
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
DEPRECATED: Image interface.
"""

import warnings

from oslo_utils import uuidutils
from six.moves.urllib import parse

from novaclient import api_versions
from novaclient import base
from novaclient import exceptions
from novaclient.i18n import _


class Image(base.Resource):
    """
    DEPRECATED: An image is a collection of files used to create or rebuild a
    server.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Image: %s>" % self.name

    def delete(self):
        """
        DEPRECATED: Delete this image.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(self)


class GlanceManager(base.Manager):
    """Use glance directly from service catalog.

    This is used to do name to id lookups for images. Do not use it
    for anything else besides that. You have been warned.

    """

    resource_class = Image

    def find_image(self, name_or_id):
        """Find an image by name or id (user provided input)."""

        with self.alternate_service_type(
                'image', allowed_types=('image',)):
            # glance catalog entries are the unversioned endpoint, so
            # we need to jam a version bit in here.
            if uuidutils.is_uuid_like(name_or_id):
                # if it's a uuid, then just go collect the info and be
                # done with it.
                return self._get('/v2/images/%s' % name_or_id, None)
            else:
                matches = self._list('/v2/images?name=%s' % name_or_id,
                                     "images")
                num_matches = len(matches)
                if num_matches == 0:
                    msg = "No %s matching %s." % (
                        self.resource_class.__name__, name_or_id)
                    raise exceptions.NotFound(404, msg)
                elif num_matches > 1:
                    msg = (_("Multiple %(class)s matches found for "
                             "'%(name)s', use an ID to be more specific.") %
                           {'class': self.resource_class.__name__.lower(),
                            'name': name_or_id})
                    raise exceptions.NoUniqueMatch(msg)
                else:
                    matches[0].append_request_ids(matches.request_ids)
                    return matches[0]


class ImageManager(base.ManagerWithFind):
    """
    DEPRECATED: Manage :class:`Image` resources.
    """
    resource_class = Image

    @api_versions.wraps('2.0', '2.35')
    def get(self, image):
        """
        DEPRECATED: Get an image.

        :param image: The ID of the image to get.
        :rtype: :class:`Image`
        """
        warnings.warn(
            'The novaclient.v2.images module is deprecated and will be '
            'removed after Nova 15.0.0 is released. Use python-glanceclient '
            'or python-openstacksdk instead.', DeprecationWarning)
        return self._get("/images/%s" % base.getid(image), "image")

    def list(self, detailed=True, limit=None, marker=None):
        """
        DEPRECATED: Get a list of all images.

        :rtype: list of :class:`Image`
        :param limit: maximum number of images to return.
        :param marker: Begin returning images that appear later in the image
                       list than that represented by this image id (optional).
        """
        # FIXME(mriedem): Should use the api_versions.wraps decorator but that
        # breaks the ManagerWithFind.findall method which checks the argspec
        # on this function looking for the 'detailed' arg, and it's getting
        # tripped up if you use the wraps decorator. This is all deprecated for
        # removal anyway so we probably don't care too much about this.
        if self.api.api_version > api_versions.APIVersion('2.35'):
            raise exceptions.VersionNotFoundForAPIMethod(
                self.api.api_version, 'list')
        warnings.warn(
            'The novaclient.v2.images module is deprecated and will be '
            'removed after Nova 15.0.0 is released. Use python-glanceclient '
            'or python-openstacksdk instead.', DeprecationWarning)
        params = {}
        detail = ''
        if detailed:
            detail = '/detail'
        if limit:
            params['limit'] = int(limit)
        if marker:
            params['marker'] = str(marker)
        params = sorted(params.items(), key=lambda x: x[0])
        query = '?%s' % parse.urlencode(params) if params else ''
        return self._list('/images%s%s' % (detail, query), 'images')

    @api_versions.wraps('2.0', '2.35')
    def delete(self, image):
        """
        DEPRECATED: Delete an image.

        It should go without saying that you can't delete an image
        that you didn't create.

        :param image: The :class:`Image` (or its ID) to delete.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        warnings.warn(
            'The novaclient.v2.images module is deprecated and will be '
            'removed after Nova 15.0.0 is released. Use python-glanceclient '
            'or python-openstacksdk instead.', DeprecationWarning)
        return self._delete("/images/%s" % base.getid(image))

    @api_versions.wraps('2.0', '2.38')
    def set_meta(self, image, metadata):
        """
        DEPRECATED: Set an images metadata

        :param image: The :class:`Image` to add metadata to
        :param metadata: A dict of metadata to add to the image
        """
        warnings.warn(
            'The novaclient.v2.images module is deprecated and will be '
            'removed after Nova 15.0.0 is released. Use python-glanceclient '
            'or python-openstacksdk instead.', DeprecationWarning)
        body = {'metadata': metadata}
        return self._create("/images/%s/metadata" % base.getid(image),
                            body, "metadata")

    @api_versions.wraps('2.0', '2.38')
    def delete_meta(self, image, keys):
        """
        DEPRECATED: Delete metadata from an image

        :param image: The :class:`Image` to delete metadata
        :param keys: A list of metadata keys to delete from the image
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        warnings.warn(
            'The novaclient.v2.images module is deprecated and will be '
            'removed after Nova 15.0.0 is released. Use python-glanceclient '
            'or python-openstacksdk instead.', DeprecationWarning)
        result = base.TupleWithMeta((), None)
        for k in keys:
            ret = self._delete("/images/%s/metadata/%s" %
                               (base.getid(image), k))
            result.append_request_ids(ret.request_ids)

        return result

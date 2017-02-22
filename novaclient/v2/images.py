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

from oslo_utils import uuidutils

from novaclient import base
from novaclient import exceptions
from novaclient.i18n import _


class Image(base.Resource):
    HUMAN_ID = True

    def __repr__(self):
        return "<Image: %s>" % self.name


class GlanceManager(base.Manager):
    """Use glance directly from service catalog.

    This is used to do name to id lookups for images and listing images for
    the --image-with option to the 'boot' command. Do not use it
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

    def list(self):
        """
        Get a detailed list of all images.

        :rtype: list of :class:`Image`
        """
        with self.alternate_service_type('image', allowed_types=('image',)):
            return self._list('/v2/images', 'images')

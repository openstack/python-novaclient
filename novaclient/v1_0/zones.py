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
Zone interface.
"""

from novaclient import base
from novaclient.v1_0 import base as local_base


class Weighting(base.Resource):
    def __init__(self, manager, info):
        self.name = "n/a"
        super(Weighting, self).__init__(manager, info)

    def __repr__(self):
        return "<Weighting: %s>" % self.name

    def to_dict(self):
        """Return the original info setting, which is a dict."""
        return self._info


class Zone(base.Resource):
    def __init__(self, manager, info):
        self.name = "n/a"
        self.is_active = "n/a"
        self.capabilities = "n/a"
        super(Zone, self).__init__(manager, info)

    def __repr__(self):
        return "<Zone: %s>" % self.api_url

    def delete(self):
        """
        Delete a child zone.
        """
        self.manager.delete(self)

    def update(self, api_url=None, username=None, password=None,
               weight_offset=None, weight_scale=None):
        """
        Update the name for this child zone.

        :param api_url: Update the child zone's API URL.
        :param username: Update the child zone's username.
        :param password: Update the child zone's password.
        :param weight_offset: Update the child zone's weight offset.
        :param weight_scale: Update the child zone's weight scale.
        """
        self.manager.update(self, api_url, username, password,
                            weight_offset, weight_scale)


class ZoneManager(local_base.BootingManagerWithFind):
    resource_class = Zone

    def info(self):
        """
        Get info on this zone.

        :rtype: :class:`Zone`
        """
        return self._get("/zones/info", "zone")

    def get(self, zone):
        """
        Get a child zone.

        :param server: ID of the :class:`Zone` to get.
        :rtype: :class:`Zone`
        """
        return self._get("/zones/%s" % base.getid(zone), "zone")

    def list(self, detailed=True):
        """
        Get a list of child zones.
        :rtype: list of :class:`Zone`
        """
        detail = ""
        if detailed:
            detail = "/detail"
        return self._list("/zones%s" % detail, "zones")

    def create(self, api_url, username, password,
               weight_offset=0.0, weight_scale=1.0):
        """
        Create a new child zone.

        :param api_url: The child zone's API URL.
        :param username: The child zone's username.
        :param password: The child zone's password.
        :param weight_offset: The child zone's weight offset.
        :param weight_scale: The child zone's weight scale.
        """
        body = {"zone": {
            "api_url": api_url,
            "username": username,
            "password": password,
            "weight_offset": weight_offset,
            "weight_scale": weight_scale
        }}

        return self._create("/zones", body, "zone")

    def boot(self, name, image, flavor, ipgroup=None, meta=None, files=None,
               zone_blob=None, reservation_id=None, min_count=None,
               max_count=None):
        """
        Create (boot) a new server while being aware of Zones.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param ipgroup: An initial :class:`IPGroup` for this server.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param files: A dict of files to overrwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.
        :param zone_blob: a single (encrypted) string which is used internally
                      by Nova for routing between Zones. Users cannot populate
                      this field.
        :param reservation_id: a UUID for the set of servers being requested.
        :param min_count: minimum number of servers to create.
        :param max_count: maximum number of servers to create.
        """
        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        return self._boot("/zones/boot", "reservation_id", name, image, flavor,
                          ipgroup=ipgroup, meta=meta, files=files,
                          zone_blob=zone_blob, reservation_id=reservation_id,
                          return_raw=True, min_count=min_count,
                          max_count=max_count)

    def select(self, *args, **kwargs):
        """
        Given requirements for a new instance, select hosts
        in this zone that best match those requirements.
        """
        # 'specs' may be passed in as None, so change to an empty string.
        specs = kwargs.get("specs") or ""
        url = "/zones/select"
        weighting_list = self._list(url, "weights", Weighting, body=specs)
        return [wt.to_dict() for wt in weighting_list]

    def delete(self, zone):
        """
        Delete a child zone.
        """
        self._delete("/zones/%s" % base.getid(zone))

    def update(self, zone, api_url=None, username=None, password=None,
               weight_offset=None, weight_scale=None):
        """
        Update the name or the api_url for a zone.

        :param zone: The :class:`Zone` (or its ID) to update.
        :param api_url: Update the API URL.
        :param username: Update the username.
        :param password: Update the password.
        :param weight_offset: Update the child zone's weight offset.
        :param weight_scale: Update the child zone's weight scale.
        """

        body = {"zone": {}}
        if api_url:
            body["zone"]["api_url"] = api_url
        if username:
            body["zone"]["username"] = username
        if password:
            body["zone"]["password"] = password
        if weight_offset:
            body["zone"]["weight_offset"] = weight_offset
        if weight_scale:
            body["zone"]["weight_scale"] = weight_scale
        if not len(body["zone"]):
            return
        self._update("/zones/%s" % base.getid(zone), body)

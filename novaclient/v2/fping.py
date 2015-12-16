# Copyright 2012 OpenStack Foundation
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
Fping interface.
"""
from six.moves import urllib

from novaclient import base


class Fping(base.Resource):
    """A server to fping."""
    HUMAN_ID = True

    def __repr__(self):
        return "<Fping: %s>" % self.id


class FpingManager(base.ManagerWithFind):
    """Manage :class:`Fping` resources."""
    resource_class = Fping

    def list(self, all_tenants=False, include=None, exclude=None):
        """Fping all servers.

        :returns: list of :class:`Fping`.
        """
        include = include or []
        exclude = exclude or []
        params = []
        if all_tenants:
            params.append(("all_tenants", 1))
        if include:
            params.append(("include", ",".join(include)))
        elif exclude:
            params.append(("exclude", ",".join(exclude)))
        uri = "/os-fping"
        if params:
            uri = "%s?%s" % (uri, urllib.parse.urlencode(params))
        return self._list(uri, "servers")

    def get(self, server):
        """Fping a specific server.

        :param server: ID of the server to fping.
        :returns: :class:`Fping`
        """
        return self._get("/os-fping/%s" % base.getid(server), "server")

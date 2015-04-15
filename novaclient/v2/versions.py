# Copyright 2014 NEC Corporation.  All rights reserved.
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
version interface
"""

from six.moves import urllib

from novaclient import base
from novaclient import client


class Version(base.Resource):
    """
    Compute REST API information
    """
    def __repr__(self):
        return "<Version>"


class VersionManager(base.ManagerWithFind):
    resource_class = Version

    def _is_session_client(self):
        return isinstance(self.api.client, client.SessionClient)

    def list(self):
        """List all versions."""

        version_url = None
        if self._is_session_client():
            # NOTE: "list versions" API needs to be accessed without base
            # URI (like "v2/{project-id}"), so here should be a scheme("http",
            # etc.) and a hostname.
            endpoint = self.api.client.get_endpoint()
            url = urllib.parse.urlparse(endpoint)
            version_url = '%s://%s/' % (url.scheme, url.netloc)

        return self._list(version_url, "versions")

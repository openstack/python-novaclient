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

    def get_current(self):
        """Returns info about current version."""
        if self._is_session_client():
            url = self.api.client.get_endpoint().rsplit("/", 1)[0]
            return self._get(url, "version")
        else:
            # NOTE(andreykurilin): HTTPClient doesn't have ability to send get
            # request without token in the url, so `self._get` doesn't work.
            all_versions = self.list()
            url = self.client.management_url.rsplit("/", 1)[0]
            for version in all_versions:
                for link in version.links:
                    if link["href"].rstrip('/') == url:
                        return version

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

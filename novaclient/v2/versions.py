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

from urllib import parse

from novaclient import base
from novaclient import exceptions as exc


class Version(base.Resource):
    """
    Compute REST API information
    """
    def __repr__(self):
        return "<Version>"


class VersionManager(base.ManagerWithFind):
    resource_class = Version

    def _get_current(self):
        """Returns info about current version."""

        # TODO(sdague): we've now got to make up to 3 HTTP requests to
        # determine what version we are running, due to differences in
        # deployments and versions. We really need to cache the
        # results of this per endpoint and keep the results of it for
        # some reasonable TTL (like 24 hours) to reduce our round trip
        # traffic.
        try:
            # Assume that the value of get_endpoint() is something
            # we can get the version of. This is a 404 for Nova <
            # Mitaka if the service catalog contains project_id.
            #
            # TODO(sdague): add microversion for when this will
            # change
            url = "%s" % self.api.client.get_endpoint()
            return self._get(url, "version")
        except exc.NotFound:
            # If that's a 404, we can instead try hacking together
            # an endpoint root url by chopping off the last 2 /s.
            # This is kind of gross, but we've had this baked in
            # so long people got used to this hard coding.
            #
            # NOTE(sdague): many service providers don't really
            # implement GET / in the expected way, if we do a GET
            # /v2 that's actually a 300 redirect to
            # /v2/... because of how paste works. So adding the
            # end slash is really important.
            url = "%s/" % url.rsplit("/", 1)[0]
            return self._get(url, "version")

    def get_current(self):
        try:
            return self._get_current()
        except exc.Unauthorized:
            # NOTE(sdague): RAX's repose configuration blocks access to the
            # versioned endpoint, which is definitely non-compliant behavior.
            # However, there is no defcore test for this yet. Remove this code
            # block once we land things in defcore.
            return None

    def list(self):
        """List all versions."""

        endpoint = self.api.client.get_endpoint()
        url = parse.urlparse(endpoint)
        # NOTE(andreykurilin): endpoint URL has at least 3 formats:
        #   1. the classic (legacy) endpoint:
        #       http://{host}:{optional_port}/v{2 or 2.1}/{project-id}
        #   2. starting from microversion 2.18 project-id is not included:
        #       http://{host}:{optional_port}/v{2 or 2.1}
        #   3. under wsgi:
        #       http://{host}:{optional_port}/compute/v{2 or 2.1}
        if (url.path.endswith("v2") or "/v2/" in url.path or
                url.path.endswith("v2.1") or "/v2.1/" in url.path):
            # this way should handle all 3 possible formats
            path = url.path[:url.path.rfind("/v2")]
            version_url = '%s://%s%s' % (url.scheme, url.netloc, path)
        else:
            # NOTE(andreykurilin): probably, it is one of the next cases:
            #  * https://compute.example.com/
            #  * https://example.com/compute
            # leave as is without cropping.
            version_url = endpoint

        return self._list(version_url, "versions")

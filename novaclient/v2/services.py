# Copyright 2012 IBM Corp.
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
service interface
"""
from six.moves import urllib

from novaclient import api_versions
from novaclient import base


class Service(base.Resource):
    def __repr__(self):
        return "<Service: %s>" % self.binary

    def _add_details(self, info):
        dico = 'resource' in info and info['resource'] or info
        for (k, v) in dico.items():
            setattr(self, k, v)


class ServiceManager(base.ManagerWithFind):
    resource_class = Service

    def list(self, host=None, binary=None):
        """
        Get a list of services.

        :param host: destination host name.
        """
        url = "/os-services"
        filters = []
        if host:
            filters.append(("host", host))
        if binary:
            filters.append(("binary", binary))
        if filters:
            url = "%s?%s" % (url, urllib.parse.urlencode(filters))
        return self._list(url, "services")

    @api_versions.wraps("2.0", "2.10")
    def _update_body(self, host, binary, disabled_reason=None):
        body = {"host": host,
                "binary": binary}
        if disabled_reason is not None:
            body["disabled_reason"] = disabled_reason
        return body

    @api_versions.wraps("2.11")
    def _update_body(self, host, binary, disabled_reason=None,
                     force_down=None):
        body = {"host": host,
                "binary": binary}
        if disabled_reason is not None:
            body["disabled_reason"] = disabled_reason
        if force_down is not None:
            body["forced_down"] = force_down
        return body

    def enable(self, host, binary):
        """Enable the service specified by hostname and binary."""
        body = self._update_body(host, binary)
        return self._update("/os-services/enable", body, "service")

    def disable(self, host, binary):
        """Disable the service specified by hostname and binary."""
        body = self._update_body(host, binary)
        return self._update("/os-services/disable", body, "service")

    def disable_log_reason(self, host, binary, reason):
        """Disable the service with reason."""
        body = self._update_body(host, binary, reason)
        return self._update("/os-services/disable-log-reason", body, "service")

    def delete(self, service_id):
        """Delete a service."""
        return self._delete("/os-services/%s" % service_id)

    @api_versions.wraps("2.11")
    def force_down(self, host, binary, force_down=None):
        """Force service state to down specified by hostname and binary."""
        body = self._update_body(host, binary, force_down=force_down)
        return self._update("/os-services/force-down", body, "service")

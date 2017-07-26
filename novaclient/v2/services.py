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
        return "<Service: %s>" % self.id

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

    @api_versions.wraps('2.0', '2.52')
    def enable(self, host, binary):
        """Enable the service specified by hostname and binary."""
        body = self._update_body(host, binary)
        return self._update("/os-services/enable", body, "service")

    @api_versions.wraps('2.53')
    def enable(self, service_uuid):
        """Enable the service specified by the service UUID ID.

        :param service_uuid: The UUID ID of the service to enable.
        """
        return self._update(
            "/os-services/%s" % service_uuid, {'status': 'enabled'}, "service")

    @api_versions.wraps('2.0', '2.52')
    def disable(self, host, binary):
        """Disable the service specified by hostname and binary."""
        body = self._update_body(host, binary)
        return self._update("/os-services/disable", body, "service")

    @api_versions.wraps('2.53')
    def disable(self, service_uuid):
        """Disable the service specified by the service UUID ID.

        :param service_uuid: The UUID ID of the service to disable.
        """
        return self._update("/os-services/%s" % service_uuid,
                            {'status': 'disabled'}, "service")

    @api_versions.wraps('2.0', '2.52')
    def disable_log_reason(self, host, binary, reason):
        """Disable the service with reason."""
        body = self._update_body(host, binary, reason)
        return self._update("/os-services/disable-log-reason", body, "service")

    @api_versions.wraps('2.53')
    def disable_log_reason(self, service_uuid, reason):
        """Disable the service with a reason.

        :param service_uuid: The UUID ID of the service to disable.
        :param reason: The reason for disabling a service. The minimum length
            is 1 and the maximum length is 255.
        """
        body = {
            'status': 'disabled',
            'disabled_reason': reason
        }
        return self._update("/os-services/%s" % service_uuid, body, "service")

    def delete(self, service_id):
        """Delete a service.

        :param service_id: Before microversion 2.53, this must be an integer id
            and may not uniquely the service in a multi-cell deployment.
            Starting with microversion 2.53 this must be a UUID.
        """
        return self._delete("/os-services/%s" % service_id)

    @api_versions.wraps("2.11", "2.52")
    def force_down(self, host, binary, force_down=None):
        """Force service state to down specified by hostname and binary."""
        body = self._update_body(host, binary, force_down=force_down)
        return self._update("/os-services/force-down", body, "service")

    @api_versions.wraps("2.53")
    def force_down(self, service_uuid, force_down):
        """Update the service's ``forced_down`` field specified by the
        service UUID ID.

        :param service_uuid: The UUID ID of the service.
        :param force_down: Whether or not this service was forced down manually
            by an administrator. This value is useful to know that some 3rd
            party has verified the service should be marked down.
        """
        return self._update("/os-services/%s" % service_uuid,
                            {'forced_down': force_down}, "service")

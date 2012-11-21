# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM
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
from novaclient import base


class Service(base.Resource):
    def __repr__(self):
        return "<Service: %s>" % self.service

    def _add_details(self, info):
        dico = 'resource' in info and info['resource'] or info
        for (k, v) in dico.items():
            setattr(self, k, v)


class ServiceManager(base.ManagerWithFind):
    resource_class = Service

    def list(self, host=None, service=None):
        """
        Describes cpu/memory/hdd info for host.

        :param host: destination host name.
        """
        url = "/os-services"
        if host:
            url = "/os-services?host=%s" % host
        if service:
            url = "/os-services?service=%s" % service
        if host and service:
            url = "/os-services?host=%s&service=%s" % (host, service)
        return self._list(url, "services")

    def enable(self, host, service):
        """Enable the service specified by hostname and servicename"""
        body = {"host": host, "service": service}
        result = self._update("/os-services/enable", body)
        return self.resource_class(self, result)

    def disable(self, host, service):
        """Enable the service specified by hostname and servicename"""
        body = {"host": host, "service": service}
        result = self._update("/os-services/disable", body)
        return self.resource_class(self, result)

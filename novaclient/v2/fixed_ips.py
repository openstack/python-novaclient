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
Fixed IPs interface.
"""

from novaclient import api_versions
from novaclient import base


class FixedIP(base.Resource):
    """DEPRECATED"""
    def __repr__(self):
        return "<FixedIP: %s>" % self.address


class FixedIPsManager(base.Manager):
    """DEPRECATED"""
    resource_class = FixedIP

    @api_versions.deprecated_after('2.35')
    def get(self, fixed_ip):
        """DEPRECATED: Show information for a Fixed IP.

        :param fixed_ip: Fixed IP address to get info for
        """
        return self._get('/os-fixed-ips/%s' % base.getid(fixed_ip),
                         "fixed_ip")

    @api_versions.deprecated_after('2.35')
    def reserve(self, fixed_ip):
        """DEPRECATED: Reserve a Fixed IP.

        :param fixed_ip: Fixed IP address to reserve
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        body = {"reserve": None}
        resp, body = self.api.client.post('/os-fixed-ips/%s/action' %
                                          base.getid(fixed_ip), body=body)
        return self.convert_into_with_meta(body, resp)

    @api_versions.deprecated_after('2.35')
    def unreserve(self, fixed_ip):
        """DEPRECATED: Unreserve a Fixed IP.

        :param fixed_ip: Fixed IP address to unreserve
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        body = {"unreserve": None}
        resp, body = self.api.client.post('/os-fixed-ips/%s/action' %
                                          base.getid(fixed_ip), body=body)
        return self.convert_into_with_meta(body, resp)

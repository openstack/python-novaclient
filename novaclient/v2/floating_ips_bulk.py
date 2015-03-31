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
Bulk Floating IPs interface
"""
from novaclient import base
from novaclient.v2 import floating_ips


class FloatingIPRange(base.Resource):
    def __repr__(self):
        return "<FloatingIPRange: %s>" % self.ip_range


class FloatingIPBulkManager(base.ManagerWithFind):
    resource_class = FloatingIPRange

    def list(self, host=None):
        """
        List all floating IPs
        """
        if host is None:
            return self._list('/os-floating-ips-bulk',
                              'floating_ip_info',
                              obj_class=floating_ips.FloatingIP)
        else:
            return self._list('/os-floating-ips-bulk/%s' % host,
                              'floating_ip_info',
                              obj_class=floating_ips.FloatingIP)

    def create(self, ip_range, pool=None, interface=None):
        """
        Create floating IPs by range
        """
        body = {"floating_ips_bulk_create": {'ip_range': ip_range}}
        if pool is not None:
            body['floating_ips_bulk_create']['pool'] = pool
        if interface is not None:
            body['floating_ips_bulk_create']['interface'] = interface

        return self._create('/os-floating-ips-bulk', body,
                            'floating_ips_bulk_create')

    def delete(self, ip_range):
        """
        Delete floating IPs by range
        """
        body = {"ip_range": ip_range}
        return self._update('/os-floating-ips-bulk/delete', body)

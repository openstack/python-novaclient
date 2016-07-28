# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack Foundation
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

from novaclient import api_versions
from novaclient import base


class FloatingIP(base.Resource):
    """DEPRECATED"""

    def delete(self):
        """
        DEPRECATED: Delete this floating IP

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(self)


class FloatingIPManager(base.ManagerWithFind):
    """DEPRECATED"""
    resource_class = FloatingIP

    @api_versions.deprecated_after('2.35')
    def list(self):
        """DEPRECATED: List floating IPs"""
        return self._list("/os-floating-ips", "floating_ips")

    @api_versions.deprecated_after('2.35')
    def create(self, pool=None):
        """DEPRECATED: Create (allocate) a  floating IP for a tenant"""
        return self._create("/os-floating-ips", {'pool': pool}, "floating_ip")

    @api_versions.deprecated_after('2.35')
    def delete(self, floating_ip):
        """DEPRECATED: Delete (deallocate) a  floating IP for a tenant

        :param floating_ip: The floating IP address to delete.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete("/os-floating-ips/%s" % base.getid(floating_ip))

    @api_versions.deprecated_after('2.35')
    def get(self, floating_ip):
        """DEPRECATED: Retrieve a floating IP"""
        return self._get("/os-floating-ips/%s" % base.getid(floating_ip),
                         "floating_ip")

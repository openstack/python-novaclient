# Copyright 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from novaclient import api_versions
from novaclient import base


class TenantNetwork(base.Resource):
    def delete(self):
        """
        DEPRECATED: Delete this project network.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(network=self)


class TenantNetworkManager(base.ManagerWithFind):
    """DEPRECATED"""
    resource_class = base.Resource

    @api_versions.deprecated_after('2.35')
    def list(self):
        """DEPRECATED"""
        return self._list('/os-tenant-networks', 'networks')

    @api_versions.deprecated_after('2.35')
    def get(self, network):
        """DEPRECATED"""
        return self._get('/os-tenant-networks/%s' % base.getid(network),
                         'network')

    @api_versions.deprecated_after('2.35')
    def delete(self, network):
        """
        DEPRECATED: Delete a specified project network.

        :param network: a project network to delete
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete('/os-tenant-networks/%s' % base.getid(network))

    @api_versions.deprecated_after('2.35')
    def create(self, label, cidr):
        """DEPRECATED"""
        body = {'network': {'label': label, 'cidr': cidr}}
        return self._create('/os-tenant-networks', body, 'network')

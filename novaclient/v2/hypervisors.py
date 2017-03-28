# Copyright 2012 OpenStack Foundation
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
Hypervisors interface
"""

from six.moves.urllib import parse

from novaclient import api_versions
from novaclient import base
from novaclient import utils


class Hypervisor(base.Resource):
    NAME_ATTR = 'hypervisor_hostname'

    def __repr__(self):
        return "<Hypervisor: %s>" % self.id


class HypervisorManager(base.ManagerWithFind):
    resource_class = Hypervisor
    is_alphanum_id_allowed = True

    def _list_base(self, detailed=True, marker=None, limit=None):
        path = '/os-hypervisors'
        if detailed:
            path += '/detail'
        params = {}
        if limit is not None:
            params['limit'] = int(limit)
        if marker is not None:
            params['marker'] = str(marker)
        path += utils.prepare_query_string(params)
        return self._list(path, 'hypervisors')

    @api_versions.wraps("2.0", "2.32")
    def list(self, detailed=True):
        """
        Get a list of hypervisors.
        """
        return self._list_base(detailed=detailed)

    @api_versions.wraps("2.33")
    def list(self, detailed=True, marker=None, limit=None):
        """
        Get a list of hypervisors.

        :param marker: Begin returning hypervisor that appear later in the
                       keypair list than that represented by this keypair name
                       (optional).
        :param limit: maximum number of keypairs to return (optional).
        """
        return self._list_base(detailed=detailed, marker=marker, limit=limit)

    def search(self, hypervisor_match, servers=False):
        """
        Get a list of matching hypervisors.

        :param servers: If True, server information is also retrieved.
        """
        target = 'servers' if servers else 'search'
        url = ('/os-hypervisors/%s/%s' %
               (parse.quote(hypervisor_match, safe=''), target))
        return self._list(url, 'hypervisors')

    def get(self, hypervisor):
        """
        Get a specific hypervisor.
        """
        return self._get("/os-hypervisors/%s" % base.getid(hypervisor),
                         "hypervisor")

    def uptime(self, hypervisor):
        """
        Get the uptime for a specific hypervisor.
        """
        return self._get("/os-hypervisors/%s/uptime" % base.getid(hypervisor),
                         "hypervisor")

    def statistics(self):
        """
        Get hypervisor statistics over all compute nodes.

        Kept for backwards compatibility, new code should call
        hypervisor_stats.statistics() instead of hypervisors.statistics()
        """
        return self.api.hypervisor_stats.statistics()


class HypervisorStats(base.Resource):
    def __repr__(self):
        return ("<HypervisorStats: %d Hypervisor%s>" %
                (self.count, "s" if self.count != 1 else ""))


class HypervisorStatsManager(base.Manager):
    resource_class = HypervisorStats

    def statistics(self):
        """
        Get hypervisor statistics over all compute nodes.
        """
        return self._get("/os-hypervisors/statistics", "hypervisor_statistics")

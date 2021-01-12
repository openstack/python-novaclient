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

from urllib import parse

from novaclient import api_versions
from novaclient import base
from novaclient import exceptions
from novaclient.i18n import _
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

        :param detailed: Include a detailed response.
        """
        return self._list_base(detailed=detailed)

    @api_versions.wraps("2.33")
    def list(self, detailed=True, marker=None, limit=None):
        """
        Get a list of hypervisors.

        :param detailed: Include a detailed response.
        :param marker: Begin returning hypervisors that appear later in the
                       hypervisors list than that represented by this
                       hypervisor ID. Starting with microversion 2.53 the
                       marker must be a UUID hypervisor ID.
                       (optional).
        :param limit: maximum number of hypervisors to return (optional).
                      Note the API server has a configurable default limit.
                      If no limit is specified here or limit is larger than
                      default, the default limit will be used.
        """
        return self._list_base(detailed=detailed, marker=marker, limit=limit)

    def search(self, hypervisor_match, servers=False, detailed=False):
        """
        Get a list of matching hypervisors.

        :param hypervisor_match: The hypervisor host name or a portion of it.
            The hypervisor hosts are selected with the host name matching
            this pattern.
        :param servers: If True, server information is also retrieved.
        :param detailed: If True, detailed hypervisor information is returned.
            This requires API version 2.53 or greater.
        """
        # Starting with microversion 2.53, the /servers and /search routes are
        # deprecated and we get the same results using GET /os-hypervisors
        # using query parameters for the hostname pattern and servers.
        if self.api_version >= api_versions.APIVersion('2.53'):
            url = ('/os-hypervisors%s?hypervisor_hostname_pattern=%s' %
                   ('/detail' if detailed else '',
                    parse.quote(hypervisor_match, safe='')))
            if servers:
                url += '&with_servers=True'
        else:
            if detailed:
                raise exceptions.UnsupportedVersion(
                    _('Parameter "detailed" requires API version 2.53 or '
                      'greater.'))
            target = 'servers' if servers else 'search'
            url = ('/os-hypervisors/%s/%s' %
                   (parse.quote(hypervisor_match, safe=''), target))
        return self._list(url, 'hypervisors')

    def get(self, hypervisor):
        """
        Get a specific hypervisor.

        :param hypervisor: Either a Hypervisor object or an ID. Starting with
            microversion 2.53 the ID must be a UUID value.
        """
        return self._get("/os-hypervisors/%s" % base.getid(hypervisor),
                         "hypervisor")

    def uptime(self, hypervisor):
        """
        Get the uptime for a specific hypervisor.

        :param hypervisor: Either a Hypervisor object or an ID. Starting with
            microversion 2.53 the ID must be a UUID value.
        """
        # Starting with microversion 2.88, the '/os-hypervisors/{id}/uptime'
        # route is removed in favour of returning 'uptime' in the response of
        # the '/os-hypervisors/{id}' route. This behaves slightly differently,
        # in that it won't error out if a virt driver doesn't support reporting
        # uptime or if the hypervisor is down, but it's a good enough
        # approximation
        if self.api_version < api_versions.APIVersion("2.88"):
            return self._get(
                "/os-hypervisors/%s/uptime" % base.getid(hypervisor),
                "hypervisor")

        resp, body = self.api.client.get(
            "/os-hypervisors/%s" % base.getid(hypervisor)
        )
        content = {
            k: v for k, v in body['hypervisor'].items()
            if k in ('id', 'hypervisor_hostname', 'state', 'status', 'uptime')
        }
        return self.resource_class(self, content, loaded=True, resp=resp)

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

    @api_versions.wraps("2.0", "2.87")
    def statistics(self):
        """
        Get hypervisor statistics over all compute nodes.
        """
        return self._get("/os-hypervisors/statistics", "hypervisor_statistics")

    @api_versions.wraps("2.88")
    def statistics(self):
        raise exceptions.UnsupportedVersion(
            _("The 'statistics' API is removed in API version 2.88 or later.")
        )

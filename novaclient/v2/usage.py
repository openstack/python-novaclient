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
Usage interface.
"""

import oslo_utils

from novaclient import api_versions
from novaclient import base


class Usage(base.Resource):
    """
    Usage contains information about a tenant's physical resource usage
    """
    def __repr__(self):
        return "<ComputeUsage>"

    def get(self):
        fmt = '%Y-%m-%dT%H:%M:%S.%f'
        if self.start and self.stop and self.tenant_id:
            # set_loaded() first ... so if we have to bail, we know we tried.
            self.set_loaded(True)
            start = oslo_utils.timeutils.parse_strtime(self.start, fmt=fmt)
            stop = oslo_utils.timeutils.parse_strtime(self.stop, fmt=fmt)

            new = self.manager.get(self.tenant_id, start, stop)
            if new:
                self._add_details(new._info)
                self.append_request_ids(new.request_ids)


class UsageManager(base.ManagerWithFind):
    """
    Manage :class:`Usage` resources.
    """
    resource_class = Usage
    usage_prefix = 'os-simple-tenant-usage'

    def _usage_query(self, start, end, marker=None, limit=None, detailed=None):
        query = "?start=%s&end=%s" % (start.isoformat(), end.isoformat())
        if limit:
            query = "%s&limit=%s" % (query, int(limit))
        if marker:
            query = "%s&marker=%s" % (query, marker)
        if detailed is not None:
            query = "%s&detailed=%s" % (query, int(bool(detailed)))
        return query

    @api_versions.wraps("2.0", "2.39")
    def list(self, start, end, detailed=False):
        """
        Get usage for all tenants

        :param start: :class:`datetime.datetime` Start date in UTC
        :param end: :class:`datetime.datetime` End date in UTC
        :param detailed: Whether to include information about each
                         instance whose usage is part of the report
        :rtype: list of :class:`Usage`.
        """
        query_string = self._usage_query(start, end, detailed=detailed)
        url = '/%s%s' % (self.usage_prefix, query_string)
        return self._list(url, 'tenant_usages')

    @api_versions.wraps("2.40")
    def list(self, start, end, detailed=False, marker=None, limit=None):
        """
        Get usage for all tenants

        :param start: :class:`datetime.datetime` Start date in UTC
        :param end: :class:`datetime.datetime` End date in UTC
        :param detailed: Whether to include information about each
                         instance whose usage is part of the report
        :param marker: Begin returning usage data for instances that appear
                       later in the instance list than that represented by
                       this instance UUID (optional).
        :param limit: Maximum number of instances to include in the usage
                      (optional). Note the API server has a configurable
                      default limit. If no limit is specified here or limit
                      is larger than default, the default limit will be used.
        :rtype: list of :class:`Usage`.
        """
        query_string = self._usage_query(start, end, marker, limit, detailed)
        url = '/%s%s' % (self.usage_prefix, query_string)
        return self._list(url, 'tenant_usages')

    @api_versions.wraps("2.0", "2.39")
    def get(self, tenant_id, start, end):
        """
        Get usage for a specific tenant.

        :param tenant_id: Tenant ID to fetch usage for
        :param start: :class:`datetime.datetime` Start date in UTC
        :param end: :class:`datetime.datetime` End date in UTC
        :rtype: :class:`Usage`
        """
        query_string = self._usage_query(start, end)
        url = '/%s/%s%s' % (self.usage_prefix, tenant_id, query_string)
        return self._get(url, 'tenant_usage')

    @api_versions.wraps("2.40")
    def get(self, tenant_id, start, end, marker=None, limit=None):
        """
        Get usage for a specific tenant.

        :param tenant_id: Tenant ID to fetch usage for
        :param start: :class:`datetime.datetime` Start date in UTC
        :param end: :class:`datetime.datetime` End date in UTC
        :param marker: Begin returning usage data for instances that appear
                       later in the instance list than that represented by
                       this instance UUID (optional).
        :param limit: Maximum number of instances to include in the usage
                      (optional). Note the API server has a configurable
                      default limit. If no limit is specified here or limit
                      is larger than default, the default limit will be used.
        :rtype: :class:`Usage`
        """
        query_string = self._usage_query(start, end, marker, limit)
        url = '/%s/%s%s' % (self.usage_prefix, tenant_id, query_string)
        return self._get(url, 'tenant_usage')

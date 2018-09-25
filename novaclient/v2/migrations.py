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
migration interface
"""

from novaclient import api_versions
from novaclient import base


class Migration(base.Resource):
    def __repr__(self):
        return "<Migration: %s>" % self.id


class MigrationManager(base.ManagerWithFind):
    resource_class = Migration

    def _list_base(self, host=None, status=None, instance_uuid=None,
                   marker=None, limit=None, changes_since=None,
                   changes_before=None):
        opts = {}
        if host:
            opts['host'] = host
        if status:
            opts['status'] = status
        if instance_uuid:
            opts['instance_uuid'] = instance_uuid
        if marker:
            opts['marker'] = marker
        if limit:
            opts['limit'] = limit
        if changes_since:
            opts['changes-since'] = changes_since
        if changes_before:
            opts['changes-before'] = changes_before

        return self._list("/os-migrations", "migrations", filters=opts)

    @api_versions.wraps("2.0", "2.58")
    def list(self, host=None, status=None, instance_uuid=None):
        """
        Get a list of migrations.
        :param host: filter migrations by host name (optional).
        :param status: filter migrations by status (optional).
        :param instance_uuid: filter migrations by instance uuid (optional).
        """
        return self._list_base(host=host, status=status,
                               instance_uuid=instance_uuid)

    @api_versions.wraps("2.59", "2.65")
    def list(self, host=None, status=None, instance_uuid=None,
             marker=None, limit=None, changes_since=None):
        """
        Get a list of migrations.
        :param host: filter migrations by host name (optional).
        :param status: filter migrations by status (optional).
        :param instance_uuid: filter migrations by instance uuid (optional).
        :param marker: Begin returning migrations that appear later in the
        migrations list than that represented by this migration UUID
        (optional).
        :param limit: maximum number of migrations to return (optional).
        :param changes_since: only return migrations changed later or equal
        to a certain point of time. The provided time should be an ISO 8061
        formatted time. e.g. 2016-03-04T06:27:59Z . (optional).
        """
        return self._list_base(host=host, status=status,
                               instance_uuid=instance_uuid,
                               marker=marker, limit=limit,
                               changes_since=changes_since)

    @api_versions.wraps("2.66")
    def list(self, host=None, status=None, instance_uuid=None,
             marker=None, limit=None, changes_since=None,
             changes_before=None):
        """
        Get a list of migrations.
        :param host: filter migrations by host name (optional).
        :param status: filter migrations by status (optional).
        :param instance_uuid: filter migrations by instance uuid (optional).
        :param marker: Begin returning migrations that appear later in the
        migrations list than that represented by this migration UUID
        (optional).
        :param limit: maximum number of migrations to return (optional).
        :param changes_since: Only return migrations changed later or equal
        to a certain point of time. The provided time should be an ISO 8061
        formatted time. e.g. 2016-03-04T06:27:59Z . (optional).
        :param changes_before: Only return migrations changed earlier or
        equal to a certain point of time. The provided time should be an ISO
        8061 formatted time. e.g. 2016-03-05T06:27:59Z . (optional).
        """
        return self._list_base(host=host, status=status,
                               instance_uuid=instance_uuid,
                               marker=marker, limit=limit,
                               changes_since=changes_since,
                               changes_before=changes_before)

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
                   changes_before=None, migration_type=None,
                   source_compute=None, user_id=None, project_id=None):
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
        if migration_type:
            opts['migration_type'] = migration_type
        if source_compute:
            opts['source_compute'] = source_compute
        if user_id:
            opts['user_id'] = user_id
        if project_id:
            opts['project_id'] = project_id

        return self._list("/os-migrations", "migrations", filters=opts)

    @api_versions.wraps("2.0", "2.58")
    def list(self, host=None, status=None, instance_uuid=None,
             migration_type=None, source_compute=None):
        """
        Get a list of migrations.
        :param host: filter migrations by host name (optional).
        :param status: filter migrations by status (optional).
        :param instance_uuid: filter migrations by instance uuid (optional).
        :param migration_type: Filter migrations by type. Valid values are:
        evacuation, live-migration, migration (cold), resize
        :param source_compute: Filter migrations by source compute host name.
        """
        return self._list_base(host=host, status=status,
                               instance_uuid=instance_uuid,
                               migration_type=migration_type,
                               source_compute=source_compute)

    @api_versions.wraps("2.59", "2.65")
    def list(self, host=None, status=None, instance_uuid=None,
             marker=None, limit=None, changes_since=None,
             migration_type=None, source_compute=None):
        """
        Get a list of migrations.
        :param host: filter migrations by host name (optional).
        :param status: filter migrations by status (optional).
        :param instance_uuid: filter migrations by instance uuid (optional).
        :param marker: Begin returning migrations that appear later in the
        migrations list than that represented by this migration UUID
        (optional).
        :param limit: maximum number of migrations to return (optional).
        Note the API server has a configurable default limit. If no limit is
        specified here or limit is larger than default, the default limit will
        be used.
        :param changes_since: only return migrations changed later or equal
        to a certain point of time. The provided time should be an ISO 8061
        formatted time. e.g. 2016-03-04T06:27:59Z . (optional).
        :param migration_type: Filter migrations by type. Valid values are:
        evacuation, live-migration, migration (cold), resize
        :param source_compute: Filter migrations by source compute host name.
        """
        return self._list_base(host=host, status=status,
                               instance_uuid=instance_uuid,
                               marker=marker, limit=limit,
                               changes_since=changes_since,
                               migration_type=migration_type,
                               source_compute=source_compute)

    @api_versions.wraps("2.66", "2.79")
    def list(self, host=None, status=None, instance_uuid=None,
             marker=None, limit=None, changes_since=None,
             changes_before=None, migration_type=None, source_compute=None):
        """
        Get a list of migrations.
        :param host: filter migrations by host name (optional).
        :param status: filter migrations by status (optional).
        :param instance_uuid: filter migrations by instance uuid (optional).
        :param marker: Begin returning migrations that appear later in the
        migrations list than that represented by this migration UUID
        (optional).
        :param limit: maximum number of migrations to return (optional).
        Note the API server has a configurable default limit. If no limit is
        specified here or limit is larger than default, the default limit will
        be used.
        :param changes_since: Only return migrations changed later or equal
        to a certain point of time. The provided time should be an ISO 8061
        formatted time. e.g. 2016-03-04T06:27:59Z . (optional).
        :param changes_before: Only return migrations changed earlier or
        equal to a certain point of time. The provided time should be an ISO
        8061 formatted time. e.g. 2016-03-05T06:27:59Z . (optional).
        :param migration_type: Filter migrations by type. Valid values are:
        evacuation, live-migration, migration (cold), resize
        :param source_compute: Filter migrations by source compute host name.
        """
        return self._list_base(host=host, status=status,
                               instance_uuid=instance_uuid,
                               marker=marker, limit=limit,
                               changes_since=changes_since,
                               changes_before=changes_before,
                               migration_type=migration_type,
                               source_compute=source_compute)

    @api_versions.wraps("2.80")
    def list(self, host=None, status=None, instance_uuid=None,
             marker=None, limit=None, changes_since=None,
             changes_before=None, migration_type=None,
             source_compute=None, user_id=None, project_id=None):
        """
        Get a list of migrations.
        :param host: filter migrations by host name (optional).
        :param status: filter migrations by status (optional).
        :param instance_uuid: filter migrations by instance uuid (optional).
        :param marker: Begin returning migrations that appear later in the
        migrations list than that represented by this migration UUID
        (optional).
        :param limit: maximum number of migrations to return (optional).
        Note the API server has a configurable default limit. If no limit is
        specified here or limit is larger than default, the default limit will
        be used.
        :param changes_since: Only return migrations changed later or equal
        to a certain point of time. The provided time should be an ISO 8061
        formatted time. e.g. 2016-03-04T06:27:59Z . (optional).
        :param changes_before: Only return migrations changed earlier or
        equal to a certain point of time. The provided time should be an ISO
        8061 formatted time. e.g. 2016-03-05T06:27:59Z . (optional).
        :param migration_type: Filter migrations by type. Valid values are:
        evacuation, live-migration, migration, resize
        :param source_compute: Filter migrations by source compute host name.
        :param user_id: filter migrations by user (optional).
        :param project_id: filter migrations by project (optional).
        """
        return self._list_base(host=host, status=status,
                               instance_uuid=instance_uuid,
                               marker=marker, limit=limit,
                               changes_since=changes_since,
                               changes_before=changes_before,
                               migration_type=migration_type,
                               source_compute=source_compute,
                               user_id=user_id,
                               project_id=project_id)

# Copyright 2016 OpenStack Foundation
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


class ServerMigration(base.Resource):
    def __repr__(self):
        return "<ServerMigration>"


class ServerMigrationsManager(base.ManagerWithFind):
    resource_class = ServerMigration

    @api_versions.wraps("2.22")
    def live_migrate_force_complete(self, server, migration):
        """
        Force on-going live migration to complete

        :param server: The :class:`Server` (or its ID)
        :param migration: Migration id that will be forced to complete
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        body = {'force_complete': None}
        resp, body = self.api.client.post(
            '/servers/%s/migrations/%s/action' % (base.getid(server),
                                                  base.getid(migration)),
            body=body)
        return self.convert_into_with_meta(body, resp)

    @api_versions.wraps("2.23")
    def get(self, server, migration):
        """
        Get a migration of a specified server

        :param server: The :class:`Server` (or its ID)
        :param migration: Migration id that will be gotten.
        :returns: An instance of
                  novaclient.v2.server_migrations.ServerMigration
        """
        return self._get('/servers/%s/migrations/%s' %
                         (base.getid(server), base.getid(migration)),
                         'migration')

    @api_versions.wraps("2.23")
    def list(self, server):
        """
        Get a migrations list of a specified server

        :param server: The :class:`Server` (or its ID)
        :returns: An instance of novaclient.base.ListWithMeta
        """
        return self._list(
            '/servers/%s/migrations' % (base.getid(server)), "migrations")

    @api_versions.wraps("2.24")
    def live_migration_abort(self, server, migration):
        """
        Cancel an ongoing live migration

        :param server: The :class:`Server` (or its ID)
        :param migration: Migration id that will be cancelled
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete(
            '/servers/%s/migrations/%s' % (base.getid(server),
                                           base.getid(migration)))

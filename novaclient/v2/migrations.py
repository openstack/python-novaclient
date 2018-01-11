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

from novaclient import base


class Migration(base.Resource):
    def __repr__(self):
        return "<Migration: %s>" % self.id


class MigrationManager(base.ManagerWithFind):
    resource_class = Migration

    def list(self, host=None, status=None, instance_uuid=None):
        """
        Get a list of migrations.
        :param host: (optional) filter migrations by host name.
        :param status: (optional) filter migrations by status.
        """
        opts = {}
        if host:
            opts['host'] = host
        if status:
            opts['status'] = status
        if instance_uuid:
            opts['instance_uuid'] = instance_uuid

        return self._list("/os-migrations", "migrations", filters=opts)

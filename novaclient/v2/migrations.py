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

from six.moves.urllib import parse

from novaclient import base
from novaclient.i18n import _

import warnings


class Migration(base.Resource):
    def __repr__(self):
        return "<Migration: %s>" % self.id


class MigrationManager(base.ManagerWithFind):
    resource_class = Migration

    def list(self, host=None, status=None, cell_name=None, instance_uuid=None):
        """
        Get a list of migrations.
        :param host: (optional) filter migrations by host name.
        :param status: (optional) filter migrations by status.
        :param cell_name: (optional) filter migrations for a cell.
        """
        opts = {}
        if host:
            opts['host'] = host
        if status:
            opts['status'] = status
        if cell_name:
            warnings.warn(_("Argument 'cell_name' is "
                            "deprecated since Pike, and will "
                            "be removed in a future release."))
            opts['cell_name'] = cell_name
        if instance_uuid:
            opts['instance_uuid'] = instance_uuid

        # Transform the dict to a sequence of two-element tuples in fixed
        # order, then the encoded string will be consistent in Python 2&3.
        new_opts = sorted(opts.items(), key=lambda x: x[0])

        query_string = "?%s" % parse.urlencode(new_opts) if new_opts else ""

        return self._list("/os-migrations%s" % query_string, "migrations")

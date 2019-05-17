# Copyright 2013 Rackspace Hosting
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


class InstanceAction(base.Resource):
    pass


class InstanceActionManager(base.ManagerWithFind):
    resource_class = InstanceAction

    def get(self, server, request_id):
        """
        Get details of an action performed on an instance.

        :param request_id: The request_id of the action to get.
        """
        return self._get("/servers/%s/os-instance-actions/%s" %
                         (base.getid(server), request_id), 'instanceAction')

    @api_versions.wraps("2.0", "2.57")
    def list(self, server):
        """
        Get a list of actions performed on a server.

        :param server: The :class:`Server` (or its ID)
        """
        return self._list('/servers/%s/os-instance-actions' %
                          base.getid(server), 'instanceActions')

    @api_versions.wraps("2.58", "2.65")
    def list(self, server, marker=None, limit=None, changes_since=None):
        """
        Get a list of actions performed on a server.

        :param server: The :class:`Server` (or its ID)
        :param marker: Begin returning actions that appear later in the action
                       list than that represented by this action request id
                       (optional).
        :param limit: Maximum number of actions to return. (optional).
                      Note the API server has a configurable default limit.
                      If no limit is specified here or limit is larger than
                      default, the default limit will be used.
        :param changes_since: List only instance actions changed later or
                              equal to a certain point of time. The provided
                              time should be an ISO 8061 formatted time.
                              e.g. 2016-03-04T06:27:59Z . (optional).
        """
        opts = {}
        if marker:
            opts['marker'] = marker
        if limit:
            opts['limit'] = limit
        if changes_since:
            opts['changes-since'] = changes_since
        return self._list('/servers/%s/os-instance-actions' %
                          base.getid(server), 'instanceActions', filters=opts)

    @api_versions.wraps("2.66")
    def list(self, server, marker=None, limit=None, changes_since=None,
             changes_before=None):
        """
        Get a list of actions performed on a server.

        :param server: The :class:`Server` (or its ID)
        :param marker: Begin returning actions that appear later in the action
                       list than that represented by this action request id
                       (optional).
        :param limit: Maximum number of actions to return. (optional).
        :param changes_since: List only instance actions changed later or
                              equal to a certain point of time. The provided
                              time should be an ISO 8061 formatted time.
                              e.g. 2016-03-04T06:27:59Z . (optional).
        :param changes_before: List only instance actions changed earlier or
                               equal to a certain point of time. The provided
                               time should be an ISO 8061 formatted time.
                               e.g. 2016-03-05T06:27:59Z . (optional).
        """
        opts = {}
        if marker:
            opts['marker'] = marker
        if limit:
            opts['limit'] = limit
        if changes_since:
            opts['changes-since'] = changes_since
        if changes_before:
            opts['changes-before'] = changes_before
        return self._list('/servers/%s/os-instance-actions' %
                          base.getid(server), 'instanceActions', filters=opts)

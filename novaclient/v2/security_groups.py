# Copyright 2011 OpenStack Foundation
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
Security group interface (1.1 extension).
"""

from six.moves.urllib import parse

from novaclient import api_versions
from novaclient import base


class SecurityGroup(base.Resource):
    """DEPRECATED"""

    def __str__(self):
        return str(self.id)

    def delete(self):
        """
        DEPRECATED: Delete this security group.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(self)

    def update(self):
        """
        DEPRECATED: Update this security group.

        :returns: :class:`SecurityGroup`
        """
        return self.manager.update(self)


class SecurityGroupManager(base.ManagerWithFind):
    """DEPRECATED"""

    resource_class = SecurityGroup

    @api_versions.deprecated_after('2.35')
    def create(self, name, description):
        """
        DEPRECATED: Create a security group

        :param name: name for the security group to create
        :param description: description of the security group
        :rtype: the security group object
        """
        body = {"security_group": {"name": name, 'description': description}}
        return self._create('/os-security-groups', body, 'security_group')

    @api_versions.deprecated_after('2.35')
    def update(self, group, name, description):
        """
        DEPRECATED: Update a security group

        :param group: The security group to update (group or ID)
        :param name: name for the security group to update
        :param description: description for the security group to update
        :rtype: the security group object
        """
        body = {"security_group": {"name": name, 'description': description}}
        return self._update('/os-security-groups/%s' % base.getid(group),
                            body, 'security_group')

    @api_versions.deprecated_after('2.35')
    def delete(self, group):
        """
        DEPRECATED: Delete a security group

        :param group: The security group to delete (group or ID)
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete('/os-security-groups/%s' % base.getid(group))

    @api_versions.deprecated_after('2.35')
    def get(self, group_id):
        """
        DEPRECATED: Get a security group

        :param group_id: The security group to get by ID
        :rtype: :class:`SecurityGroup`
        """
        return self._get('/os-security-groups/%s' % group_id,
                         'security_group')

    @api_versions.deprecated_after('2.35')
    def list(self, search_opts=None):
        """
        DEPRECATED: Get a list of all security_groups

        :rtype: list of :class:`SecurityGroup`
        """
        search_opts = search_opts or {}

        qparams = dict((k, v) for (k, v) in search_opts.items() if v)

        query_string = '?%s' % parse.urlencode(qparams) if qparams else ''

        return self._list('/os-security-groups%s' % query_string,
                          'security_groups')

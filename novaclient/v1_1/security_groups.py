# Copyright 2011 OpenStack LLC.
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

from novaclient import base


class SecurityGroup(base.Resource):
    def __str__(self):
        return str(self.id)

    def delete(self):
        self.manager.delete(self)


class SecurityGroupManager(base.ManagerWithFind):
    resource_class = SecurityGroup

    def create(self, name, description):
        """
        Create a security group

        :param name: name for the security group to create
        :param description: description of the security group
        :rtype: the security group object
        """
        body = {"security_group": {"name": name, 'description': description}}
        return self._create('/os-security-groups', body, 'security_group')

    def delete(self, group):
        """
        Delete a security group

        :param group: The security group to delete (group or ID)
        :rtype: None
        """
        self._delete('/os-security-groups/%s' % base.getid(group))

    def get(self, id):
        """
        Get a security group

        :param group: The security group to get by ID
        :rtype: :class:`SecurityGroup`
        """
        return self._get('/os-security-groups/%s' % id,
                         'security_group')

    def list(self):
        """
        Get a list of all security_groups

        :rtype: list of :class:`SecurityGroup`
        """
        return self._list("/os-security-groups", "security_groups")

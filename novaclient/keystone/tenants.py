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

from novaclient import base


class RoleRefs(base.Resource):
    def __repr__(self):
        return "<Roleref %s>" % self._info


class Tenant(base.Resource):
    def __repr__(self):
        return "<Tenant %s>" % self._info

    def delete(self):
        self.manager.delete(self)

    def update(self, description=None, enabled=None):
        # FIXME(ja): set the attributes in this object if successful
        self.manager.update(self.id, description, enabled)

    def add_user(self, user):
        self.manager.add_user_to_tenant(self.id, base.getid(user))


class TenantManager(base.ManagerWithFind):
    resource_class = Tenant

    def get(self, tenant_id):
        return self._get("/tenants/%s" % tenant_id, "tenant")

    # FIXME(ja): finialize roles once finalized in keystone
    #            right now the only way to add/remove a tenant is to
    #            give them a role within a project
    def get_user_role_refs(self, user_id):
        return self._get("/users/%s/roleRefs" % user_id, "roleRefs")

    def add_user_to_tenant(self, tenant_id, user_id):
        params = {"roleRef": {"tenantId": tenant_id, "roleId": "Member"}}
        return self._create("/users/%s/roleRefs" % user_id, params, "roleRef")

    def remove_user_from_tenant(self, tenant_id, user_id):
        params = {"roleRef": {"tenantId": tenant_id, "roleId": "Member"}}
        # FIXME(ja): we have to get the roleref?  what is 5?
        return self._delete("/users/%s/roleRefs/5" % user_id)

    def create(self, tenant_id, description=None, enabled=True):
        """
        Create a new tenant.
        """
        params = {"tenant": {"id": tenant_id,
                             "description": description,
                             "enabled": enabled}}

        return self._create('/tenants', params, "tenant")

    def list(self):
        """
        Get a list of tenants.
        :rtype: list of :class:`Tenant`
        """
        return self._list("/tenants", "tenants")

    def update(self, tenant_id, description=None, enabled=None):
        """
        update a tenant with a new name and description
        """
        body = {"tenant": {'id': tenant_id}}
        if enabled is not None:
            body['tenant']['enabled'] = enabled
        if description:
            body['tenant']['description'] = description

        self._update("/tenants/%s" % tenant_id, body)

    def delete(self, tenant):
        """
        Delete a tenant.
        """
        self._delete("/tenants/%s" % (base.getid(tenant)))

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


class User(base.Resource):
    def __repr__(self):
        return "<User %s>" % self._info

    def delete(self):
        self.manager.delete(self)


class UserManager(base.ManagerWithFind):
    resource_class = User

    def get(self, user):
        return self._get("/users/%s" % base.getid(user), "user")

    def update_email(self, user, email):
        """
        Update email
        """
        # FIXME(ja): why do we have to send id in params and url?
        params = {"user": {"id": base.getid(user),
                           "email": email}}

        self._update("/users/%s" % base.getid(user), params)

    def update_enabled(self, user, enabled):
        """
        Update enabled-ness
        """
        params = {"user": {"id": base.getid(user),
                           "enabled": enabled}}

        self._update("/users/%s/enabled" % base.getid(user), params)

    def update_password(self, user, password):
        """
        Update password
        """
        params = {"user": {"id": base.getid(user),
                           "password": password}}

        self._update("/users/%s/password" % base.getid(user), params)

    def update_tenant(self, user, tenant):
        """
        Update default tenant.
        """
        params = {"user": {"id": base.getid(user),
                           "tenantId": base.getid(tenant)}}

        # FIXME(ja): seems like a bad url - default tenant is an attribute
        #            not a subresource!???
        self._update("/users/%s/tenant" % base.getid(user), params)

    def create(self, user_id, password, email, tenant_id=None, enabled=True):
        """
        Create a user.
        """
        # FIXME(ja): email should be optional but keystone currently
        # requires it
        params = {"user": {"id": user_id,
                           "password": password,
                           "tenantId": tenant_id,
                           "email": email,
                           "enabled": enabled}}
        return self._create('/users', params, "user")

    def _create(self, url, body, response_key):
        # NOTE(ja): since we post the id, we have to use a PUT instead of POST
        resp, body = self.api.client.put(url, body=body)
        return self.resource_class(self, body[response_key])

    def delete(self, user):
        """
        Delete a user.
        """
        self._delete("/users/%s" % base.getid(user))

    def list(self, tenant_id=None):
        """
        Get a list of users (optionally limited to a tenant)

        :rtype: list of :class:`User`
        """

        if not tenant_id:
            return self._list("/users", "users")
        else:
            return self._list("/tenants/%s/users" % tenant_id, "users")

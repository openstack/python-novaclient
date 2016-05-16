# Copyright 2012 OpenStack Foundation
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

"""Flavor access interface."""

from novaclient import base
from novaclient.i18n import _


class FlavorAccess(base.Resource):
    def __repr__(self):
        return ("<FlavorAccess flavor id: %s, tenant id: %s>" %
                (self.flavor_id, self.tenant_id))


class FlavorAccessManager(base.ManagerWithFind):
    """Manage :class:`FlavorAccess` resources."""
    resource_class = FlavorAccess

    def list(self, **kwargs):
        # NOTE(mriedem): This looks a bit weird, you would normally expect this
        # method to just take a flavor arg, but it used to erroneously accept
        # flavor or tenant, but never actually implemented support for listing
        # flavor access by tenant. We leave the interface unchanged though for
        # backward compatibility.
        if kwargs.get('flavor'):
            return self._list('/flavors/%s/os-flavor-access' %
                              base.getid(kwargs['flavor']), 'flavor_access')
        raise NotImplementedError(_('Unknown list options.'))

    def add_tenant_access(self, flavor, tenant):
        """Add a tenant to the given flavor access list."""
        info = {'tenant': tenant}
        return self._action('addTenantAccess', flavor, info)

    def remove_tenant_access(self, flavor, tenant):
        """Remove a tenant from the given flavor access list."""
        info = {'tenant': tenant}
        return self._action('removeTenantAccess', flavor, info)

    def _action(self, action, flavor, info, **kwargs):
        """Perform a flavor action."""
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/flavors/%s/action' % base.getid(flavor)
        resp, body = self.api.client.post(url, body=body)

        items = [self.resource_class(self, res)
                 for res in body['flavor_access']]

        return base.ListWithMeta(items, resp)

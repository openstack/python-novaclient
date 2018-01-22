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

from novaclient import api_versions
from novaclient import base


class QuotaSet(base.Resource):

    def update(self, *args, **kwargs):
        return self.manager.update(self.id, *args, **kwargs)


class QuotaSetManager(base.Manager):
    resource_class = QuotaSet

    def get(self, tenant_id, user_id=None, detail=False):
        url = '/os-quota-sets/%(tenant_id)s'
        if detail:
            url += '/detail'

        if user_id:
            params = {'tenant_id': tenant_id, 'user_id': user_id}
            url += '?user_id=%(user_id)s'
        else:
            params = {'tenant_id': tenant_id}

        return self._get(url % params, "quota_set")

    # NOTE(mriedem): Before 2.57 the resources you could update was just a
    # kwargs dict and not validated on the client-side, only on the API server
    # side.
    @api_versions.wraps("2.0", "2.56")
    def update(self, tenant_id, **kwargs):

        user_id = kwargs.pop('user_id', None)
        body = {'quota_set': kwargs}

        for key in list(body['quota_set']):
            if body['quota_set'][key] is None:
                body['quota_set'].pop(key)

        if user_id:
            url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        else:
            url = '/os-quota-sets/%s' % tenant_id
        return self._update(url, body, 'quota_set')

    # NOTE(mriedem): 2.57 does strict validation of the resources you can
    # specify. 2.36 blocks network-related resources and 2.57 blocks
    # injected files related quotas.
    @api_versions.wraps("2.57")
    def update(self, tenant_id, user_id=None, force=False,
               instances=None, cores=None, ram=None,
               metadata_items=None, key_pairs=None, server_groups=None,
               server_group_members=None):

        resources = {}
        if force:
            resources['force'] = force
        if instances is not None:
            resources['instances'] = instances
        if cores is not None:
            resources['cores'] = cores
        if ram is not None:
            resources['ram'] = ram
        if metadata_items is not None:
            resources['metadata_items'] = metadata_items
        if key_pairs is not None:
            resources['key_pairs'] = key_pairs
        if server_groups is not None:
            resources['server_groups'] = server_groups
        if server_group_members is not None:
            resources['server_group_members'] = server_group_members
        body = {'quota_set': resources}

        if user_id:
            url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        else:
            url = '/os-quota-sets/%s' % tenant_id
        return self._update(url, body, 'quota_set')

    def defaults(self, tenant_id):
        return self._get('/os-quota-sets/%s/defaults' % tenant_id,
                         'quota_set')

    def delete(self, tenant_id, user_id=None):
        """
        Delete quota for a tenant or for a user.

        :param tenant_id: A tenant for which quota is to be deleted
        :param user_id: A user for which quota is to be deleted
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        if user_id:
            url = '/os-quota-sets/%s?user_id=%s' % (tenant_id, user_id)
        else:
            url = '/os-quota-sets/%s' % tenant_id
        return self._delete(url)

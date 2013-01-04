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


class QuotaSet(base.Resource):

    @property
    def id(self):
        """QuotaSet does not have a 'id' attribute but base.Resource needs it
        to self-refresh and QuotaSet is indexed by tenant_id"""
        return self.tenant_id

    def update(self, *args, **kwargs):
        return self.manager.update(self.tenant_id, *args, **kwargs)


class QuotaSetManager(base.ManagerWithFind):
    resource_class = QuotaSet

    def get(self, tenant_id):
        if hasattr(tenant_id, 'tenant_id'):
            tenant_id = tenant_id.tenant_id
        return self._get("/os-quota-sets/%s" % (tenant_id), "quota_set")

    def update(self, tenant_id, metadata_items=None,
               injected_file_content_bytes=None, injected_file_path_bytes=None,
               volumes=None, gigabytes=None,
               ram=None, floating_ips=None, instances=None,
               injected_files=None, cores=None, key_pairs=None,
               security_groups=None, security_group_rules=None):

        body = {'quota_set': {
                'tenant_id': tenant_id,
                'metadata_items': metadata_items,
                'key_pairs': key_pairs,
                'injected_file_content_bytes': injected_file_content_bytes,
                'injected_file_path_bytes': injected_file_path_bytes,
                'volumes': volumes,
                'gigabytes': gigabytes,
                'ram': ram,
                'floating_ips': floating_ips,
                'instances': instances,
                'injected_files': injected_files,
                'cores': cores,
                'security_groups': security_groups,
                'security_group_rules': security_group_rules}}

        for key in body['quota_set'].keys():
            if body['quota_set'][key] is None:
                body['quota_set'].pop(key)

        return self._update('/os-quota-sets/%s' % tenant_id, body, 'quota_set')

    def defaults(self, tenant_id):
        return self._get('/os-quota-sets/%s/defaults' % tenant_id,
                         'quota_set')

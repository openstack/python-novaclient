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

from novaclient import api_versions
from novaclient import base


class QuotaClassSet(base.Resource):

    def update(self, *args, **kwargs):
        return self.manager.update(self.id, *args, **kwargs)


class QuotaClassSetManager(base.Manager):
    resource_class = QuotaClassSet

    def get(self, class_name):
        return self._get("/os-quota-class-sets/%s" % (class_name),
                         "quota_class_set")

    def _update_body(self, **kwargs):
        return {'quota_class_set': kwargs}

    # NOTE(mriedem): Before 2.50 the resources you could update was just a
    # kwargs dict and not validated on the client-side, only on the API server
    # side.
    @api_versions.wraps("2.0", "2.49")
    def update(self, class_name, **kwargs):
        body = self._update_body(**kwargs)

        for key in list(body['quota_class_set']):
            if body['quota_class_set'][key] is None:
                body['quota_class_set'].pop(key)

        return self._update('/os-quota-class-sets/%s' % (class_name),
                            body,
                            'quota_class_set')

    # NOTE(mriedem): 2.50 does strict validation of the resources you can
    # specify since the network-related resources are blocked in 2.50.
    @api_versions.wraps("2.50", "2.56")
    def update(self, class_name, instances=None, cores=None, ram=None,
               metadata_items=None, injected_files=None,
               injected_file_content_bytes=None, injected_file_path_bytes=None,
               key_pairs=None, server_groups=None, server_group_members=None):
        resources = {}
        if instances is not None:
            resources['instances'] = instances
        if cores is not None:
            resources['cores'] = cores
        if ram is not None:
            resources['ram'] = ram
        if metadata_items is not None:
            resources['metadata_items'] = metadata_items
        if injected_files is not None:
            resources['injected_files'] = injected_files
        if injected_file_content_bytes is not None:
            resources['injected_file_content_bytes'] = (
                injected_file_content_bytes)
        if injected_file_path_bytes is not None:
            resources['injected_file_path_bytes'] = injected_file_path_bytes
        if key_pairs is not None:
            resources['key_pairs'] = key_pairs
        if server_groups is not None:
            resources['server_groups'] = server_groups
        if server_group_members is not None:
            resources['server_group_members'] = server_group_members

        body = {'quota_class_set': resources}
        return self._update('/os-quota-class-sets/%s' % class_name, body,
                            'quota_class_set')

    # NOTE(mriedem): 2.57 deprecates the usage of injected_files,
    # injected_file_content_bytes and injected_file_path_bytes so those
    # kwargs are removed.
    @api_versions.wraps("2.57")
    def update(self, class_name, instances=None, cores=None, ram=None,
               metadata_items=None, key_pairs=None, server_groups=None,
               server_group_members=None):
        resources = {}
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

        body = {'quota_class_set': resources}
        return self._update('/os-quota-class-sets/%s' % class_name, body,
                            'quota_class_set')

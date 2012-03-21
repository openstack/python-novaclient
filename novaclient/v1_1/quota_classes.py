# Copyright 2012 OpenStack LLC.
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


class QuotaClassSet(base.Resource):

    @property
    def id(self):
        """QuotaClassSet does not have a 'id' attribute but base.Resource
        needs it to self-refresh and QuotaSet is indexed by class_name"""
        return self.class_name

    def update(self, *args, **kwargs):
        self.manager.update(self.class_name, *args, **kwargs)


class QuotaClassSetManager(base.ManagerWithFind):
    resource_class = QuotaClassSet

    def get(self, class_name):
        return self._get("/os-quota-class-sets/%s" % (class_name),
                         "quota_class_set")

    def update(self, class_name, metadata_items=None,
               injected_file_content_bytes=None, volumes=None, gigabytes=None,
               ram=None, floating_ips=None, instances=None,
               injected_files=None, cores=None):

        body = {'quota_class_set': {
                'class_name': class_name,
                'metadata_items': metadata_items,
                'injected_file_content_bytes': injected_file_content_bytes,
                'volumes': volumes,
                'gigabytes': gigabytes,
                'ram': ram,
                'floating_ips': floating_ips,
                'instances': instances,
                'injected_files': injected_files,
                'cores': cores}}

        for key in body['quota_class_set'].keys():
            if body['quota_class_set'][key] is None:
                body['quota_class_set'].pop(key)

        self._update('/os-quota-class-sets/%s' % (class_name), body)

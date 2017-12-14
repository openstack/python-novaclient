# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from novaclient.tests.unit.fixture_data import base


class V1(base.Fixture):

    base_url = 'os-quota-sets'

    def setUp(self):
        super(V1, self).setUp()

        uuid = '97f4c221-bff4-4578-b030-0df4ef119353'
        uuid2 = '97f4c221bff44578b0300df4ef119353'
        test_json = {'quota_set': self.test_quota('test')}
        self.headers = self.json_headers

        for u in ('test', 'tenant-id', 'tenant-id/defaults',
                  '%s/defaults' % uuid2, 'test/detail'):
            self.requests_mock.get(self.url(u),
                                   json=test_json,
                                   headers=self.headers)

        self.requests_mock.put(self.url(uuid),
                               json={'quota_set': self.test_quota(uuid)},
                               headers=self.headers)

        self.requests_mock.get(self.url(uuid),
                               json={'quota_set': self.test_quota(uuid)},
                               headers=self.headers)

        self.requests_mock.put(self.url(uuid2),
                               json={'quota_set': self.test_quota(uuid2)},
                               headers=self.headers)
        self.requests_mock.get(self.url(uuid2),
                               json={'quota_set': self.test_quota(uuid2)},
                               headers=self.headers)

        for u in ('test', uuid2):
            self.requests_mock.delete(self.url(u), status_code=202,
                                      headers=self.headers)

    def test_quota(self, tenant_id='test'):
        return {
            'id': tenant_id,
            'metadata_items': 1,
            'injected_file_content_bytes': 1,
            'injected_file_path_bytes': 1,
            'ram': 1,
            'fixed_ips': -1,
            'floating_ips': 1,
            'instances': 1,
            'injected_files': 1,
            'cores': 1,
            'key_pairs': 1,
            'security_groups': 1,
            'security_group_rules': 1,
            'server_groups': 1,
            'server_group_members': 1
        }


class V2_57(V1):
    """2.57 fixture data where there are no injected file or network resources
    """

    def test_quota(self, tenant_id='test'):
        return {
            'id': tenant_id,
            'metadata_items': 1,
            'ram': 1,
            'instances': 1,
            'cores': 1,
            'key_pairs': 1,
            'server_groups': 1,
            'server_group_members': 1
        }

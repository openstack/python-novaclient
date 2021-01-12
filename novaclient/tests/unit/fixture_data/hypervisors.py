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

from urllib import parse

from oslo_utils import encodeutils

from novaclient import api_versions
from novaclient.tests.unit.fixture_data import base


class V1(base.Fixture):

    base_url = 'os-hypervisors'
    api_version = '2.1'
    hyper_id_1 = 1234
    hyper_id_2 = 5678
    service_id_1 = 1
    service_id_2 = 2

    @staticmethod
    def _transform_hypervisor_details(hypervisor):
        """Transform a detailed hypervisor view from 2.53 to 2.88."""
        del hypervisor['current_workload']
        del hypervisor['disk_available_least']
        del hypervisor['free_ram_mb']
        del hypervisor['free_disk_gb']
        del hypervisor['local_gb']
        del hypervisor['local_gb_used']
        del hypervisor['memory_mb']
        del hypervisor['memory_mb_used']
        del hypervisor['running_vms']
        del hypervisor['vcpus']
        del hypervisor['vcpus_used']
        hypervisor['uptime'] = 'fake uptime'

    def setUp(self):
        super(V1, self).setUp()

        api_version = api_versions.APIVersion(self.api_version)

        get_os_hypervisors = {
            'hypervisors': [
                {
                    'id': self.hyper_id_1,
                    'hypervisor_hostname': 'hyper1',
                    'state': 'up',
                    'status': 'enabled',
                },
                {
                    'id': self.hyper_id_2,
                    'hypervisor_hostname': 'hyper2',
                    'state': 'up',
                    'status': 'enabled',
                },
            ]
        }

        self.headers = self.json_headers

        self.requests_mock.get(self.url(),
                               json=get_os_hypervisors,
                               headers=self.headers)

        get_os_hypervisors_detail = {
            'hypervisors': [
                {
                    'id': self.hyper_id_1,
                    'service': {
                        'id': self.service_id_1,
                        'host': 'compute1',
                    },
                    'vcpus': 4,
                    'memory_mb': 10 * 1024,
                    'local_gb': 250,
                    'vcpus_used': 2,
                    'memory_mb_used': 5 * 1024,
                    'local_gb_used': 125,
                    'hypervisor_type': 'xen',
                    'hypervisor_version': 3,
                    'hypervisor_hostname': 'hyper1',
                    'free_ram_mb': 5 * 1024,
                    'free_disk_gb': 125,
                    'current_workload': 2,
                    'running_vms': 2,
                    'cpu_info': 'cpu_info',
                    'disk_available_least': 100,
                    'state': 'up',
                    'status': 'enabled',
                },
                {
                    'id': self.hyper_id_2,
                    'service': {
                        'id': self.service_id_2,
                        'host': 'compute2',
                    },
                    'vcpus': 4,
                    'memory_mb': 10 * 1024,
                    'local_gb': 250,
                    'vcpus_used': 2,
                    'memory_mb_used': 5 * 1024,
                    'local_gb_used': 125,
                    'hypervisor_type': 'xen',
                    'hypervisor_version': 3,
                    'hypervisor_hostname': 'hyper2',
                    'free_ram_mb': 5 * 1024,
                    'free_disk_gb': 125,
                    'current_workload': 2,
                    'running_vms': 2,
                    'cpu_info': 'cpu_info',
                    'disk_available_least': 100,
                    'state': 'up',
                    'status': 'enabled',
                }
            ]
        }

        if api_version >= api_versions.APIVersion('2.88'):
            for hypervisor in get_os_hypervisors_detail['hypervisors']:
                self._transform_hypervisor_details(hypervisor)

        self.requests_mock.get(self.url('detail'),
                               json=get_os_hypervisors_detail,
                               headers=self.headers)

        get_os_hypervisors_stats = {
            'hypervisor_statistics': {
                'count': 2,
                'vcpus': 8,
                'memory_mb': 20 * 1024,
                'local_gb': 500,
                'vcpus_used': 4,
                'memory_mb_used': 10 * 1024,
                'local_gb_used': 250,
                'free_ram_mb': 10 * 1024,
                'free_disk_gb': 250,
                'current_workload': 4,
                'running_vms': 4,
                'disk_available_least': 200,
            }
        }

        self.requests_mock.get(self.url('statistics'),
                               json=get_os_hypervisors_stats,
                               headers=self.headers)

        get_os_hypervisors_search = {
            'hypervisors': [
                {
                    'id': self.hyper_id_1,
                    'hypervisor_hostname': 'hyper1',
                    'state': 'up',
                    'status': 'enabled',
                },
                {
                    'id': self.hyper_id_2,
                    'hypervisor_hostname': 'hyper2',
                    'state': 'up',
                    'status': 'enabled',
                },
            ]
        }

        if api_version >= api_versions.APIVersion('2.53'):
            url = self.url(hypervisor_hostname_pattern='hyper')
        else:
            url = self.url('hyper', 'search')
        self.requests_mock.get(url,
                               json=get_os_hypervisors_search,
                               headers=self.headers)

        if api_version >= api_versions.APIVersion('2.53'):
            get_os_hypervisors_search_u_v2_53 = {
                'error_name': 'BadRequest',
                'message': 'Invalid input for query parameters '
                           'hypervisor_hostname_pattern.',
                'code': 400}
            # hypervisor_hostname_pattern is encoded in the url method
            url = self.url(hypervisor_hostname_pattern='\\u5de5\\u4f5c')
            self.requests_mock.get(url,
                                   json=get_os_hypervisors_search_u_v2_53,
                                   headers=self.headers, status_code=400)
        else:
            get_os_hypervisors_search_unicode = {
                'error_name': 'NotFound',
                'message': "No hypervisor matching "
                           "'\\u5de5\\u4f5c' could be found.",
                'code': 404
            }
            hypervisor_hostname_pattern = parse.quote(encodeutils.safe_encode(
                '\\u5de5\\u4f5c'))
            url = self.url(hypervisor_hostname_pattern, 'search')
            self.requests_mock.get(url,
                                   json=get_os_hypervisors_search_unicode,
                                   headers=self.headers, status_code=404)

        get_hyper_server = {
            'hypervisors': [
                {
                    'id': self.hyper_id_1,
                    'hypervisor_hostname': 'hyper1',
                    'state': 'up',
                    'status': 'enabled',
                    'servers': [
                        {'name': 'inst1', 'uuid': 'uuid1'},
                        {'name': 'inst2', 'uuid': 'uuid2'}
                    ]
                },
                {
                    'id': self.hyper_id_2,
                    'hypervisor_hostname': 'hyper2',
                    'state': 'up',
                    'status': 'enabled',
                    'servers': [
                        {'name': 'inst3', 'uuid': 'uuid3'},
                        {'name': 'inst4', 'uuid': 'uuid4'}
                    ]
                }
            ]
        }

        if api_version >= api_versions.APIVersion('2.53'):
            url = self.url(hypervisor_hostname_pattern='hyper',
                           with_servers=True)
        else:
            url = self.url('hyper', 'servers')
        self.requests_mock.get(url,
                               json=get_hyper_server,
                               headers=self.headers)

        get_os_hypervisors_hyper1 = {
            'hypervisor': {
                'id': self.hyper_id_1,
                'service': {'id': self.service_id_1, 'host': 'compute1'},
                'vcpus': 4,
                'memory_mb': 10 * 1024,
                'local_gb': 250,
                'vcpus_used': 2,
                'memory_mb_used': 5 * 1024,
                'local_gb_used': 125,
                'hypervisor_type': 'xen',
                'hypervisor_version': 3,
                'hypervisor_hostname': 'hyper1',
                'free_ram_mb': 5 * 1024,
                'free_disk_gb': 125,
                'current_workload': 2,
                'running_vms': 2,
                'cpu_info': 'cpu_info',
                'disk_available_least': 100,
                'state': 'up',
                'status': 'enabled',
            }
        }

        if api_version >= api_versions.APIVersion('2.88'):
            self._transform_hypervisor_details(
                get_os_hypervisors_hyper1['hypervisor'])

        self.requests_mock.get(self.url(self.hyper_id_1),
                               json=get_os_hypervisors_hyper1,
                               headers=self.headers)

        get_os_hypervisors_uptime = {
            'hypervisor': {
                'id': self.hyper_id_1,
                'hypervisor_hostname': 'hyper1',
                'uptime': 'fake uptime',
                'state': 'up',
                'status': 'enabled',
            }
        }

        self.requests_mock.get(self.url(self.hyper_id_1, 'uptime'),
                               json=get_os_hypervisors_uptime,
                               headers=self.headers)


class V253(V1):
    """Fixture data for the os-hypervisors 2.53 API."""
    api_version = '2.53'
    hyper_id_1 = 'd480b1b6-2255-43c2-b2c2-d60d42c2c074'
    hyper_id_2 = '43a8214d-f36a-4fc0-a25c-3cf35c17522d'
    service_id_1 = 'a87743ff-9c29-42ff-805d-2444659b5fc0'
    service_id_2 = '0486ab8b-1cfc-4ccb-9d94-9f22ec8bbd6b'


class V288(V253):
    """Fixture data for the os-hypervisors 2.88 API."""
    api_version = '2.88'

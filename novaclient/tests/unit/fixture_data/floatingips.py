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

from novaclient.tests.unit import fakes
from novaclient.tests.unit.fixture_data import base


class FloatingFixture(base.Fixture):

    base_url = 'os-floating-ips'

    def setUp(self):
        super(FloatingFixture, self).setUp()

        floating_ips = [{'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'},
                        {'id': 2, 'fixed_ip': '10.0.0.2', 'ip': '11.0.0.2'}]

        get_os_floating_ips = {'floating_ips': floating_ips}
        self.requests_mock.get(self.url(),
                               json=get_os_floating_ips,
                               headers=self.json_headers)

        for ip in floating_ips:
            get_os_floating_ip = {'floating_ip': ip}
            self.requests_mock.get(self.url(ip['id']),
                                   json=get_os_floating_ip,
                                   headers=self.json_headers)

            self.requests_mock.delete(self.url(ip['id']),
                                      headers=self.json_headers,
                                      status_code=204)

        def post_os_floating_ips(request, context):
            ip = floating_ips[0].copy()
            ip['pool'] = request.json().get('pool')
            return {'floating_ip': ip}
        self.requests_mock.post(self.url(),
                                json=post_os_floating_ips,
                                headers=self.json_headers)


class DNSFixture(base.Fixture):

    base_url = 'os-floating-ip-dns'

    def setUp(self):
        super(DNSFixture, self).setUp()

        get_os_floating_ip_dns = {
            'domain_entries': [
                {'domain': 'example.org'},
                {'domain': 'example.com'}
            ]
        }
        self.requests_mock.get(self.url(),
                               json=get_os_floating_ip_dns,
                               headers=self.json_headers,
                               status_code=205)

        get_dns_testdomain_entries_testname = {
            'dns_entry': {
                'ip': "10.10.10.10",
                'name': 'testname',
                'type': "A",
                'domain': 'testdomain'
            }
        }

        self.requests_mock.get(self.url('testdomain', 'entries', 'testname'),
                               json=get_dns_testdomain_entries_testname,
                               headers=self.json_headers,
                               status_code=205)

        self.requests_mock.delete(self.url('testdomain'),
                                  headers=self.json_headers)

        url = self.url('testdomain', 'entries', 'testname')
        self.requests_mock.delete(url, headers=self.json_headers)

        def put_dns_testdomain_entries_testname(request, context):
            fakes.assert_has_keys(request.json()['dns_entry'],
                                  required=['ip', 'dns_type'])
            context.status_code = 205
            return request.body
        self.requests_mock.put(url,
                               text=put_dns_testdomain_entries_testname,
                               headers=self.json_headers)

        url = self.url('testdomain', 'entries')
        self.requests_mock.get(url, status_code=404)

        get_os_floating_ip_dns_testdomain = {
            'dns_entries': [
                {
                    'dns_entry': {
                        'ip': '1.2.3.4',
                        'name': "host1",
                        'type': "A",
                        'domain': 'testdomain'
                    }
                },
                {
                    'dns_entry': {
                        'ip': '1.2.3.4',
                        'name': "host2",
                        'type': "A",
                        'domain': 'testdomain'
                    }
                },
            ]
        }
        self.requests_mock.get(url + '?ip=1.2.3.4',
                               json=get_os_floating_ip_dns_testdomain,
                               status_code=205,
                               headers=self.json_headers)

        def put_os_floating_ip_dns_testdomain(request, context):
            body = request.json()
            if body['domain_entry']['scope'] == 'private':
                fakes.assert_has_keys(body['domain_entry'],
                                      required=['availability_zone', 'scope'])
            elif body['domain_entry']['scope'] == 'public':
                fakes.assert_has_keys(body['domain_entry'],
                                      required=['project', 'scope'])
            else:
                fakes.assert_has_keys(body['domain_entry'],
                                      required=['project', 'scope'])

            return request.body

        self.requests_mock.put(self.url('testdomain'),
                               text=put_os_floating_ip_dns_testdomain,
                               status_code=205,
                               headers=self.json_headers)


class BulkFixture(base.Fixture):

    base_url = 'os-floating-ips-bulk'

    def setUp(self):
        super(BulkFixture, self).setUp()

        get_os_floating_ips_bulk = {
            'floating_ip_info': [
                {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'},
                {'id': 2, 'fixed_ip': '10.0.0.2', 'ip': '11.0.0.2'},
            ]
        }
        self.requests_mock.get(self.url(),
                               json=get_os_floating_ips_bulk,
                               headers=self.json_headers)
        self.requests_mock.get(self.url('testHost'),
                               json=get_os_floating_ips_bulk,
                               headers=self.json_headers)

        def put_os_floating_ips_bulk_delete(request, context):
            ip_range = request.json().get('ip_range')
            return {'floating_ips_bulk_delete': ip_range}

        self.requests_mock.put(self.url('delete'),
                               json=put_os_floating_ips_bulk_delete,
                               headers=self.json_headers)

        def post_os_floating_ips_bulk(request, context):
            params = request.json().get('floating_ips_bulk_create')
            pool = params.get('pool', 'defaultPool')
            interface = params.get('interface', 'defaultInterface')
            return {
                'floating_ips_bulk_create': {
                    'ip_range': '192.168.1.0/30',
                    'pool': pool,
                    'interface': interface
                }
            }

        self.requests_mock.post(self.url(),
                                json=post_os_floating_ips_bulk,
                                headers=self.json_headers)


class PoolsFixture(base.Fixture):

    base_url = 'os-floating-ip-pools'

    def setUp(self):
        super(PoolsFixture, self).setUp()

        get_os_floating_ip_pools = {
            'floating_ip_pools': [
                {'name': 'foo'},
                {'name': 'bar'}
            ]
        }
        self.requests_mock.get(self.url(),
                               json=get_os_floating_ip_pools,
                               headers=self.json_headers)

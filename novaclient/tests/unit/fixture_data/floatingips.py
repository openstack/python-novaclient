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

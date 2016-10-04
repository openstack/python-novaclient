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


class Fixture(base.Fixture):

    base_url = 'os-networks'

    def setUp(self):
        super(Fixture, self).setUp()

        get_os_networks = {
            'networks': [
                {
                    "label": "1",
                    "cidr": "10.0.0.0/24",
                    'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                    'id': '1'
                }
            ]
        }

        headers = self.json_headers

        self.requests_mock.get(self.url(),
                               json=get_os_networks,
                               headers=headers)

        def post_os_networks(request, context):
            return {'network': request.json()}

        self.requests_mock.post(self.url(),
                                json=post_os_networks,
                                headers=headers)

        get_os_networks_1 = {'network': {"label": "1", "cidr": "10.0.0.0/24"}}

        self.requests_mock.get(self.url(1),
                               json=get_os_networks_1,
                               headers=headers)

        self.requests_mock.delete(self.url('networkdelete'),
                                  status_code=202,
                                  headers=headers)

        for u in ('add', 'networkdisassociate/action', 'networktest/action',
                  '1/action', '2/action'):
            self.requests_mock.post(self.url(u),
                                    status_code=202,
                                    headers=headers)

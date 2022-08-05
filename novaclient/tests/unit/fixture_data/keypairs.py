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

from novaclient import api_versions
from novaclient.tests.unit import fakes
from novaclient.tests.unit.fixture_data import base


class V1(base.Fixture):

    api_version = '2.1'
    base_url = 'os-keypairs'

    def setUp(self):
        super(V1, self).setUp()
        api_version = api_versions.APIVersion(self.api_version)

        keypair = {'fingerprint': 'FAKE_KEYPAIR', 'name': 'test'}

        headers = self.json_headers

        self.requests_mock.get(self.url(),
                               json={'keypairs': [keypair]},
                               headers=headers)

        self.requests_mock.get(self.url('test'),
                               json={'keypair': keypair},
                               headers=headers)

        self.requests_mock.delete(self.url('test'),
                                  status_code=202,
                                  headers=headers)

        def post_os_keypairs(request, context):
            body = request.json()
            assert list(body) == ['keypair']
            if api_version >= api_versions.APIVersion("2.92"):
                # In 2.92, public_key becomes mandatory
                required = ['name', 'public_key']
            else:
                required = ['name']
            fakes.assert_has_keys(body['keypair'],
                                  required=required)
            return {'keypair': keypair}

        self.requests_mock.post(self.url(),
                                json=post_os_keypairs,
                                headers=headers)

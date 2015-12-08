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

import fixtures
from keystoneauth1 import fixture
from keystoneauth1 import loading
from keystoneauth1 import session

from novaclient import client

IDENTITY_URL = 'http://identityserver:5000/v2.0'
COMPUTE_URL = 'http://compute.host'


class V1(fixtures.Fixture):

    def __init__(self, requests_mock,
                 compute_url=COMPUTE_URL, identity_url=IDENTITY_URL,
                 **client_kwargs):
        super(V1, self).__init__()
        self.identity_url = identity_url
        self.compute_url = compute_url
        self.client = None
        self.requests_mock = requests_mock

        self.token = fixture.V2Token()
        self.token.set_scope()
        self.discovery = fixture.V2Discovery(href=self.identity_url)

        s = self.token.add_service('compute')
        s.add_endpoint(self.compute_url)

        s = self.token.add_service('computev3')
        s.add_endpoint(self.compute_url)

        self._client_kwargs = client_kwargs

    def setUp(self):
        super(V1, self).setUp()

        auth_url = '%s/tokens' % self.identity_url
        headers = {'X-Content-Type': 'application/json'}
        self.requests_mock.post(auth_url,
                                json=self.token,
                                headers=headers)
        self.requests_mock.get(self.identity_url,
                               json=self.discovery,
                               headers=headers)
        self.client = self.new_client(**self._client_kwargs)

    def new_client(self, **client_kwargs):
        return client.Client("2", username='xx',
                             password='xx',
                             project_id='xx',
                             auth_url=self.identity_url,
                             **client_kwargs)


class SessionV1(V1):

    def new_client(self):
        self.session = session.Session()
        loader = loading.get_plugin_loader('password')
        self.session.auth = loader.load_from_options(
            auth_url=self.identity_url, username='xx', password='xx')
        return client.Client("2", session=self.session)

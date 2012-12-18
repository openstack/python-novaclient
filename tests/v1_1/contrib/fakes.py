# Copyright 2012 OpenStack, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from novaclient.v1_1 import client
from tests.v1_1 import fakes


class FakeClient(fakes.FakeClient):
    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(fakes.FakeHTTPClient):
    def get_os_tenant_networks(self):
        return (200, {}, {'networks': [{"label": "1", "cidr": "10.0.0.0/24",
                'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                'id': '1'}]})

    def get_os_tenant_networks_1(self, **kw):
        return (200, {}, {'network': {"label": "1", "cidr": "10.0.0.0/24",
                'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                'id': '1'}})

    def post_os_tenant_networks(self, **kw):
        return (201, {}, {'network': {"label": "1", "cidr": "10.0.0.0/24",
                'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                'id': '1'}})

    def delete_os_tenant_networks_1(self, **kw):
        return (204, {}, None)

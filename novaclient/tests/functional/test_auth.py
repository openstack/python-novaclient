# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from six.moves.urllib import parse
import tempest_lib.cli.base

from novaclient.tests.functional import base


class TestAuthentication(base.ClientTestBase):
    def nova(self, action, identity_api_version):
        url = parse.urlparse(self.cli_clients.uri)
        url = parse.urlunparse((url.scheme, url.netloc,
                                '/v%s' % identity_api_version,
                                url.params, url.query,
                                url.fragment))
        flags = ('--os-username %s --os-tenant-name %s --os-password %s '
                 '--os-auth-url %s --endpoint-type publicURL' % (
                     self.cli_clients.username,
                     self.cli_clients.tenant_name,
                     self.cli_clients.password,
                     url))
        if self.cli_clients.insecure:
            flags += ' --insecure '

        return tempest_lib.cli.base.execute(
            "nova", action, flags, cli_dir=self.cli_clients.cli_dir)

    def test_auth_via_keystone_v2(self):
        self.nova("list", identity_api_version="2.0")

    def test_auth_via_keystone_v3(self):
        self.nova("list", identity_api_version="3")

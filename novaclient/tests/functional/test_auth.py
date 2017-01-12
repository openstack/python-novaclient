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
import tempest.lib.cli.base

from novaclient import client
from novaclient.tests.functional import base


class TestAuthentication(base.ClientTestBase):

    def _get_url(self, identity_api_version):
        url = parse.urlparse(self.cli_clients.uri)
        return parse.urlunparse((url.scheme, url.netloc,
                                 '/identity/v%s' % identity_api_version,
                                 url.params, url.query,
                                 url.fragment))

    def nova_auth_with_password(self, action, identity_api_version):
        flags = ('--os-username %s --os-tenant-name %s --os-password %s '
                 '--os-auth-url %s --os-endpoint-type publicURL' % (
                     self.cli_clients.username,
                     self.cli_clients.tenant_name,
                     self.cli_clients.password,
                     self._get_url(identity_api_version)))
        if self.cli_clients.insecure:
            flags += ' --insecure '

        return tempest.lib.cli.base.execute(
            "nova", action, flags, cli_dir=self.cli_clients.cli_dir)

    def nova_auth_with_token(self, identity_api_version):
        auth_ref = self.client.client.session.auth.get_access(
            self.client.client.session)
        token = auth_ref.auth_token
        auth_url = self._get_url(identity_api_version)
        kw = {}
        if identity_api_version == "3":
            kw["project_domain_id"] = self.project_domain_id
        nova = client.Client("2", auth_token=token, auth_url=auth_url,
                             project_name=self.project_name, **kw)
        nova.servers.list()

        # NOTE(andreykurilin): token auth is completely broken in CLI
        # flags = ('--os-username %s --os-tenant-name %s --os-auth-token %s '
        #         '--os-auth-url %s --os-endpoint-type publicURL' % (
        #             self.cli_clients.username,
        #             self.cli_clients.tenant_name,
        #             token, auth_url))
        # if self.cli_clients.insecure:
        #    flags += ' --insecure '
        #
        # return tempest.lib.cli.base.execute(
        #    "nova", action, flags, cli_dir=self.cli_clients.cli_dir)

    def test_auth_via_keystone_v2(self):
        session = self.keystone.session
        version = (2, 0)
        if not base.is_keystone_version_available(session, version):
            self.skipTest("Identity API version 2.0 is not available.")

        self.nova_auth_with_password("list", identity_api_version="2.0")
        self.nova_auth_with_token(identity_api_version="2.0")

    def test_auth_via_keystone_v3(self):
        session = self.keystone.session
        version = (3, 0)
        if not base.is_keystone_version_available(session, version):
            self.skipTest("Identity API version 3.0 is not available.")

        self.nova_auth_with_password("list", identity_api_version="3")
        self.nova_auth_with_token(identity_api_version="3")

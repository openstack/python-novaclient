#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes


class ListExtensionsTests(utils.TestCase):
    def setUp(self):
        super(ListExtensionsTests, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.1"))

    def test_list_extensions(self):
        all_exts = self.cs.list_extensions.show_all()
        self.assert_request_id(all_exts, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/extensions')
        self.assertGreater(len(all_exts), 0)
        for r in all_exts:
            self.assertGreater(len(r.summary), 0)

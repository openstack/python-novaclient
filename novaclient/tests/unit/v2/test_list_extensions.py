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

import mock

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes


class ListExtensionsTests(utils.TestCase):
    def setUp(self):
        super(ListExtensionsTests, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.1"))

    @mock.patch('warnings.warn')
    def test_list_extensions(self, mock_warn):
        all_exts = self.cs.list_extensions.show_all()
        self.assert_request_id(all_exts, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/extensions')
        self.assertGreater(len(all_exts), 0)
        warning_message = (
            'The API extension interface has been deprecated since 12.0.0 '
            'Liberty Release. This API binding will be removed in the first '
            'major release after the Nova server 20.0.0 Train release.')
        mock_warn.assert_called_once_with(warning_message, DeprecationWarning)
        for r in all_exts:
            mock_warn.reset_mock()
            self.assertGreater(len(r.summary), 0)
            mock_warn.assert_called_once_with(warning_message,
                                              DeprecationWarning)

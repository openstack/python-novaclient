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
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import limits as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import limits


class LimitsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.Fixture
    supports_image_meta = True   # 2.39 deprecates maxImageMeta
    supports_personality = True  # 2.57 deprecates maxPersonality*

    def test_get_limits(self):
        obj = self.cs.limits.get()
        self.assert_request_id(obj, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/limits')
        self.assertIsInstance(obj, limits.Limits)

    def test_get_limits_for_a_tenant(self):
        obj = self.cs.limits.get(tenant_id=1234)
        self.assert_request_id(obj, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/limits?tenant_id=1234')
        self.assertIsInstance(obj, limits.Limits)

    def test_absolute_limits_reserved(self):
        obj = self.cs.limits.get(reserved=True)
        self.assert_request_id(obj, fakes.FAKE_REQUEST_ID_LIST)

        expected = [
            limits.AbsoluteLimit("maxTotalRAMSize", 51200),
            limits.AbsoluteLimit("maxServerMeta", 5)
        ]
        if self.supports_image_meta:
            expected.append(limits.AbsoluteLimit("maxImageMeta", 5))
        if self.supports_personality:
            expected.extend([
                limits.AbsoluteLimit("maxPersonality", 5),
                limits.AbsoluteLimit("maxPersonalitySize", 10240)])

        self.assert_called('GET', '/limits?reserved=1')
        abs_limits = list(obj.absolute)
        self.assertEqual(len(abs_limits), len(expected))

        for limit in abs_limits:
            self.assertIn(limit, expected)

    def test_rate_absolute_limits(self):
        obj = self.cs.limits.get()
        self.assert_request_id(obj, fakes.FAKE_REQUEST_ID_LIST)

        expected = (
            limits.RateLimit('POST', '*', '.*', 10, 2, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('PUT', '*', '.*', 10, 2, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('DELETE', '*', '.*', 100, 100, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('POST', '*/servers', '^/servers', 25, 24, 'DAY',
                             '2011-12-15T22:42:45Z'),
        )

        rate_limits = list(obj.rate)
        self.assertEqual(len(rate_limits), len(expected))

        for limit in rate_limits:
            self.assertIn(limit, expected)

        expected = [
            limits.AbsoluteLimit("maxTotalRAMSize", 51200),
            limits.AbsoluteLimit("maxServerMeta", 5)
        ]
        if self.supports_image_meta:
            expected.append(limits.AbsoluteLimit("maxImageMeta", 5))
        if self.supports_personality:
            expected.extend([
                limits.AbsoluteLimit("maxPersonality", 5),
                limits.AbsoluteLimit("maxPersonalitySize", 10240)])

        abs_limits = list(obj.absolute)
        self.assertEqual(len(abs_limits), len(expected))

        for limit in abs_limits:
            self.assertIn(limit, expected)


class LimitsTest2_57(LimitsTest):
    data_fixture_class = data.Fixture2_57
    supports_image_meta = False
    supports_personality = False

    def setUp(self):
        super(LimitsTest2_57, self).setUp()
        self.cs.api_version = api_versions.APIVersion('2.57')

# Copyright 2015 Mirantis
# All Rights Reserved.
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
from novaclient import exceptions
from novaclient.tests.unit import utils


class APIVersionTestCase(utils.TestCase):
    def test_valid_version_strings(self):
        def _test_string(version, exp_major, exp_minor):
            v = api_versions.APIVersion(version)
            self.assertEqual(v.ver_major, exp_major)
            self.assertEqual(v.ver_minor, exp_minor)

        _test_string("1.1", 1, 1)
        _test_string("2.10", 2, 10)
        _test_string("5.234", 5, 234)
        _test_string("12.5", 12, 5)
        _test_string("2.0", 2, 0)
        _test_string("2.200", 2, 200)

    def test_null_version(self):
        v = api_versions.APIVersion()
        self.assertTrue(v.is_null())

    def test_invalid_version_strings(self):
        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "2")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "200")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "2.1.4")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "200.23.66.3")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "5 .3")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "5. 3")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "5.03")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "02.1")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "2.001")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, " 2.1")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.APIVersion, "2.1 ")

    def test_version_comparisons(self):
        v1 = api_versions.APIVersion("2.0")
        v2 = api_versions.APIVersion("2.5")
        v3 = api_versions.APIVersion("5.23")
        v4 = api_versions.APIVersion("2.0")
        v_null = api_versions.APIVersion()

        self.assertTrue(v1 < v2)
        self.assertTrue(v3 > v2)
        self.assertTrue(v1 != v2)
        self.assertTrue(v1 == v4)
        self.assertTrue(v1 != v_null)
        self.assertTrue(v_null == v_null)
        self.assertRaises(TypeError, v1.__le__, "2.1")

    def test_version_matches(self):
        v1 = api_versions.APIVersion("2.0")
        v2 = api_versions.APIVersion("2.5")
        v3 = api_versions.APIVersion("2.45")
        v4 = api_versions.APIVersion("3.3")
        v5 = api_versions.APIVersion("3.23")
        v6 = api_versions.APIVersion("2.0")
        v7 = api_versions.APIVersion("3.3")
        v8 = api_versions.APIVersion("4.0")
        v_null = api_versions.APIVersion()

        self.assertTrue(v2.matches(v1, v3))
        self.assertTrue(v2.matches(v1, v_null))
        self.assertTrue(v1.matches(v6, v2))
        self.assertTrue(v4.matches(v2, v7))
        self.assertTrue(v4.matches(v_null, v7))
        self.assertTrue(v4.matches(v_null, v8))
        self.assertFalse(v1.matches(v2, v3))
        self.assertFalse(v5.matches(v2, v4))
        self.assertFalse(v2.matches(v3, v1))

        self.assertRaises(ValueError, v_null.matches, v1, v3)

    def test_get_string(self):
        v1_string = "3.23"
        v1 = api_versions.APIVersion(v1_string)
        self.assertEqual(v1_string, v1.get_string())

        self.assertRaises(ValueError,
                          api_versions.APIVersion().get_string)


class UpdateHeadersTestCase(utils.TestCase):
    def test_api_version_is_null(self):
        headers = {}
        api_versions.update_headers(headers, api_versions.APIVersion())
        self.assertEqual({}, headers)

    def test_api_version_is_major(self):
        headers = {}
        api_versions.update_headers(headers, api_versions.APIVersion("7.0"))
        self.assertEqual({}, headers)

    def test_api_version_is_not_null(self):
        api_version = api_versions.APIVersion("2.3")
        headers = {}
        api_versions.update_headers(headers, api_version)
        self.assertEqual(
            {"X-OpenStack-Nova-API-Version": api_version.get_string()},
            headers)


class GetAPIVersionTestCase(utils.TestCase):
    def test_get_available_client_versions(self):
        output = api_versions.get_available_major_versions()
        self.assertNotEqual([], output)

    def test_wrong_format(self):
        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.get_api_version, "something_wrong")

    def test_wrong_major_version(self):
        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.get_api_version, "1")

    @mock.patch("novaclient.api_versions.APIVersion")
    def test_only_major_part_is_presented(self, mock_apiversion):
        version = 7
        self.assertEqual(mock_apiversion.return_value,
                         api_versions.get_api_version(version))
        mock_apiversion.assert_called_once_with("%s.0" % str(version))

    @mock.patch("novaclient.api_versions.APIVersion")
    def test_major_and_minor_parts_is_presented(self, mock_apiversion):
        version = "2.7"
        self.assertEqual(mock_apiversion.return_value,
                         api_versions.get_api_version(version))
        mock_apiversion.assert_called_once_with(version)

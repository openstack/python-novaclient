# Copyright 2016 Mirantis
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

import novaclient
from novaclient import api_versions
from novaclient import exceptions
from novaclient.tests.unit import utils
from novaclient import utils as nutils
from novaclient.v2 import versions


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

        self.assertTrue(v1.__lt__(v2))
        self.assertTrue(v3.__gt__(v2))
        self.assertTrue(v1.__ne__(v2))
        self.assertTrue(v1.__eq__(v4))
        self.assertTrue(v1.__ne__(v_null))
        self.assertTrue(v_null.__eq__(v_null))
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

    def test_api_version_is_gte_27(self):
        api_version = api_versions.APIVersion("2.27")
        headers = {}
        api_versions.update_headers(headers, api_version)
        self.assertIn('X-OpenStack-Nova-API-Version', headers)
        self.assertIn('OpenStack-API-Version', headers)
        self.assertEqual(api_version.get_string(),
                         headers['X-OpenStack-Nova-API-Version'])
        self.assertEqual('%s %s' % (api_versions.SERVICE_TYPE,
                                    api_version.get_string()),
                         headers['OpenStack-API-Version'])


class CheckHeadersTestCase(utils.TestCase):
    def setUp(self):
        super(CheckHeadersTestCase, self).setUp()
        mock_log_patch = mock.patch("novaclient.api_versions.LOG")
        self.mock_log = mock_log_patch.start()
        self.addCleanup(mock_log_patch.stop)

    def test_legacy_microversion_is_specified(self):
        response = mock.MagicMock(
            headers={api_versions.LEGACY_HEADER_NAME: ""})
        api_versions.check_headers(response, api_versions.APIVersion("2.2"))
        self.assertFalse(self.mock_log.warning.called)

        response = mock.MagicMock(headers={})
        api_versions.check_headers(response, api_versions.APIVersion("2.2"))
        self.assertTrue(self.mock_log.warning.called)

    def test_generic_microversion_is_specified(self):
        response = mock.MagicMock(
            headers={api_versions.HEADER_NAME: ""})
        api_versions.check_headers(response, api_versions.APIVersion("2.27"))
        self.assertFalse(self.mock_log.warning.called)

        response = mock.MagicMock(headers={})
        api_versions.check_headers(response, api_versions.APIVersion("2.27"))
        self.assertTrue(self.mock_log.warning.called)

    def test_microversion_is_not_specified(self):
        response = mock.MagicMock(
            headers={api_versions.LEGACY_HEADER_NAME: ""})
        api_versions.check_headers(response, api_versions.APIVersion("2.2"))
        self.assertFalse(self.mock_log.warning.called)

        response = mock.MagicMock(headers={})
        api_versions.check_headers(response, api_versions.APIVersion("2.0"))
        self.assertFalse(self.mock_log.warning.called)


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


class WrapsTestCase(utils.TestCase):

    def _get_obj_with_vers(self, vers):
        return mock.MagicMock(api_version=api_versions.APIVersion(vers))

    def _side_effect_of_vers_method(self, *args, **kwargs):
        m = mock.MagicMock(start_version=args[1], end_version=args[2])
        m.name = args[0]
        return m

    @mock.patch("novaclient.api_versions._get_function_name")
    @mock.patch("novaclient.api_versions.VersionedMethod")
    def test_end_version_is_none(self, mock_versioned_method, mock_name):
        mock_versioned_method.side_effect = self._side_effect_of_vers_method

        @api_versions.wraps("2.2")
        def foo(*args, **kwargs):
            pass

        foo(self._get_obj_with_vers("2.4"))

        mock_versioned_method.assert_called_once_with(
            mock_name.return_value, api_versions.APIVersion("2.2"),
            api_versions.APIVersion("2.latest"), mock.ANY)

    @mock.patch("novaclient.api_versions._get_function_name")
    @mock.patch("novaclient.api_versions.VersionedMethod")
    def test_start_and_end_version_are_presented(self, mock_versioned_method,
                                                 mock_name):
        mock_versioned_method.side_effect = self._side_effect_of_vers_method

        @api_versions.wraps("2.2", "2.6")
        def foo(*args, **kwargs):
            pass

        foo(self._get_obj_with_vers("2.4"))

        mock_versioned_method.assert_called_once_with(
            mock_name.return_value, api_versions.APIVersion("2.2"),
            api_versions.APIVersion("2.6"), mock.ANY)

    @mock.patch("novaclient.api_versions._get_function_name")
    @mock.patch("novaclient.api_versions.VersionedMethod")
    def test_api_version_doesnt_match(self, mock_versioned_method, mock_name):
        mock_versioned_method.side_effect = self._side_effect_of_vers_method

        @api_versions.wraps("2.2", "2.6")
        def foo(*args, **kwargs):
            pass

        self.assertRaises(exceptions.VersionNotFoundForAPIMethod,
                          foo, self._get_obj_with_vers("2.1"))

        mock_versioned_method.assert_called_once_with(
            mock_name.return_value, api_versions.APIVersion("2.2"),
            api_versions.APIVersion("2.6"), mock.ANY)

    def test_define_method_is_actually_called(self):
        checker = mock.MagicMock()

        @api_versions.wraps("2.2", "2.6")
        def some_func(*args, **kwargs):
            checker(*args, **kwargs)

        obj = self._get_obj_with_vers("2.4")
        some_args = ("arg_1", "arg_2")
        some_kwargs = {"key1": "value1", "key2": "value2"}

        some_func(obj, *some_args, **some_kwargs)

        checker.assert_called_once_with(*((obj,) + some_args), **some_kwargs)

    @mock.patch("novaclient.api_versions._get_function_name")
    def test_arguments_property_is_copied(self, mock_name):
        @nutils.arg("argument_1")
        @api_versions.wraps("2.666", "2.777")
        @nutils.arg("argument_2")
        def some_func():
            pass

        versioned_method = api_versions.get_substitutions(
            mock_name.return_value, api_versions.APIVersion("2.700"))[0]

        self.assertEqual(some_func.arguments,
                         versioned_method.func.arguments)
        self.assertIn((("argument_1",), {}), versioned_method.func.arguments)
        self.assertIn((("argument_2",), {}), versioned_method.func.arguments)

    def test_several_methods_with_same_name_in_one_module(self):

        class A(object):
            api_version = api_versions.APIVersion("777.777")

            @api_versions.wraps("777.777")
            def f(self):
                return 1

        class B(object):
            api_version = api_versions.APIVersion("777.777")

            @api_versions.wraps("777.777")
            def f(self):
                return 2

        self.assertEqual(1, A().f())
        self.assertEqual(2, B().f())

    def test_generate_function_name(self):
        expected_name = "novaclient.tests.unit.test_api_versions.fake_func"

        self.assertNotIn(expected_name, api_versions._SUBSTITUTIONS)

        @api_versions.wraps("7777777.7777777")
        def fake_func():
            pass

        self.assertIn(expected_name, api_versions._SUBSTITUTIONS)
        self.assertEqual(expected_name, fake_func.__id__)


class DiscoverVersionTestCase(utils.TestCase):
    def setUp(self):
        super(DiscoverVersionTestCase, self).setUp()
        self.orig_max = novaclient.API_MAX_VERSION
        self.orig_min = novaclient.API_MIN_VERSION
        self.addCleanup(self._clear_fake_version)

    def _clear_fake_version(self):
        novaclient.API_MAX_VERSION = self.orig_max
        novaclient.API_MIN_VERSION = self.orig_min

    def test_server_is_too_new(self):
        fake_client = mock.MagicMock()
        fake_client.versions.get_current.return_value = mock.MagicMock(
            version="2.7", min_version="2.4")
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.3")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")
        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.discover_version, fake_client,
                          api_versions.APIVersion('2.latest'))

    def test_server_is_too_old(self):
        fake_client = mock.MagicMock()
        fake_client.versions.get_current.return_value = mock.MagicMock(
            version="2.7", min_version="2.4")
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.10")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.9")

        self.assertRaises(exceptions.UnsupportedVersion,
                          api_versions.discover_version, fake_client,
                          api_versions.APIVersion('2.latest'))

    def test_server_end_version_is_the_latest_one(self):
        fake_client = mock.MagicMock()
        fake_client.versions.get_current.return_value = mock.MagicMock(
            version="2.7", min_version="2.4")
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.11")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")

        self.assertEqual(
            "2.7",
            api_versions.discover_version(
                fake_client,
                api_versions.APIVersion('2.latest')).get_string())

    def test_client_end_version_is_the_latest_one(self):
        fake_client = mock.MagicMock()
        fake_client.versions.get_current.return_value = mock.MagicMock(
            version="2.16", min_version="2.4")
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.11")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")

        self.assertEqual(
            "2.11",
            api_versions.discover_version(
                fake_client,
                api_versions.APIVersion('2.latest')).get_string())

    def test_server_without_microversion(self):
        fake_client = mock.MagicMock()
        fake_client.versions.get_current.return_value = mock.MagicMock(
            version='', min_version='')
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.11")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")

        self.assertEqual(
            "2.0",
            api_versions.discover_version(
                fake_client,
                api_versions.APIVersion('2.latest')).get_string())

    def test_server_without_microversion_and_no_version_field(self):
        fake_client = mock.MagicMock()
        fake_client.versions.get_current.return_value = versions.Version(
            None, {})
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.11")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")

        self.assertEqual(
            "2.0",
            api_versions.discover_version(
                fake_client,
                api_versions.APIVersion('2.latest')).get_string())

    def test_server_without_microversion_rax_workaround(self):
        fake_client = mock.MagicMock()
        fake_client.versions.get_current.return_value = None
        novaclient.API_MAX_VERSION = api_versions.APIVersion("2.11")
        novaclient.API_MIN_VERSION = api_versions.APIVersion("2.1")

        self.assertEqual(
            "2.0",
            api_versions.discover_version(
                fake_client,
                api_versions.APIVersion('2.latest')).get_string())


class DecoratedAfterTestCase(utils.TestCase):
    def test_decorated_after(self):

        class Fake(object):
            api_version = api_versions.APIVersion('2.123')

            @api_versions.deprecated_after('2.123')
            def foo(self):
                pass

        with mock.patch('warnings.warn') as mock_warn:
            Fake().foo()
            msg = ('The novaclient.tests.unit.test_api_versions module '
                   'is deprecated and will be removed.')
            mock_warn.assert_called_once_with(msg, mock.ANY)

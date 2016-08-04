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

import sys

import mock
from oslo_utils import encodeutils
import six
from six.moves.urllib import parse

from novaclient import base
from novaclient import exceptions
from novaclient.tests.unit import fakes
from novaclient.tests.unit import utils as test_utils
from novaclient import utils

UUID = '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0'


class FakeResource(object):
    NAME_ATTR = 'name'

    request_ids = fakes.FAKE_REQUEST_ID_LIST

    def __init__(self, _id, properties):
        self.id = _id
        try:
            self.name = properties['name']
        except KeyError:
            pass

    def append_request_ids(self, resp):
        pass


class FakeManager(base.ManagerWithFind):

    resource_class = FakeResource

    resources = [
        FakeResource('1234', {'name': 'entity_one'}),
        FakeResource('12345', {'name': 'UPPER'}),
        FakeResource('123456', {'name': 'lower'}),
        FakeResource('1234567', {'name': 'Mixed'}),
        FakeResource('12345678', {'name': 'mixed'}),
        FakeResource(UUID, {'name': 'entity_two'}),
        FakeResource('5678', {'name': '9876'}),
        FakeResource('01234', {'name': 'entity_three'})
    ]

    is_alphanum_id_allowed = None

    def __init__(self, alphanum_id_allowed=False):
        self.is_alphanum_id_allowed = alphanum_id_allowed

    def get(self, resource_id):
        for resource in self.resources:
            if resource.id == str(resource_id):
                return resource
        raise exceptions.NotFound(resource_id)

    def list(self):
        return base.ListWithMeta(self.resources, fakes.FAKE_REQUEST_ID_LIST)


class FakeDisplayResource(object):
    NAME_ATTR = 'display_name'

    def __init__(self, _id, properties):
        self.id = _id
        try:
            self.display_name = properties['display_name']
        except KeyError:
            pass

    def append_request_ids(self, resp):
        pass


class FakeDisplayManager(FakeManager):

    resource_class = FakeDisplayResource

    resources = [
        FakeDisplayResource('4242', {'display_name': 'entity_three'}),
    ]


class FindResourceTestCase(test_utils.TestCase):

    def setUp(self):
        super(FindResourceTestCase, self).setUp()
        self.manager = FakeManager(None)

    def test_find_none(self):
        """Test a few non-valid inputs."""
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          'asdf')
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          None)
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          {})

    def test_find_by_integer_id(self):
        output = utils.find_resource(self.manager, 1234)
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_str_id(self):
        output = utils.find_resource(self.manager, '1234')
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_uuid(self):
        output = utils.find_resource(self.manager, UUID)
        self.assertEqual(output, self.manager.get(UUID))

    def test_find_by_str_name(self):
        output = utils.find_resource(self.manager, 'entity_one')
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_str_upper_name(self):
        output = utils.find_resource(self.manager, 'UPPER')
        self.assertEqual(output, self.manager.get('12345'))

    def test_find_by_str_lower_name(self):
        output = utils.find_resource(self.manager, 'lower')
        self.assertEqual(output, self.manager.get('123456'))

    def test_find_by_str_mix_name(self):
        output = utils.find_resource(self.manager, 'Mixed')
        self.assertEqual(output, self.manager.get('1234567'))

    def test_find_by_str_lower_name_mixed(self):
        output = utils.find_resource(self.manager, 'mixed')
        self.assertEqual(output, self.manager.get('12345678'))

    def test_find_by_str_display_name(self):
        display_manager = FakeDisplayManager(None)
        output = utils.find_resource(display_manager, 'entity_three')
        self.assertEqual(output, display_manager.get('4242'))

    def test_find_in_alphanum_allowed_manager_by_str_id_(self):
        alphanum_manager = FakeManager(True)
        output = utils.find_resource(alphanum_manager, '01234')
        self.assertEqual(output, alphanum_manager.get('01234'))

    def test_find_without_wrapping_exception(self):
        alphanum_manager = FakeManager(True)
        self.assertRaises(exceptions.NotFound, utils.find_resource,
                          alphanum_manager, 'not_exist', wrap_exception=False)
        res = alphanum_manager.resources[0]
        alphanum_manager.resources.append(res)
        self.assertRaises(exceptions.NoUniqueMatch, utils.find_resource,
                          alphanum_manager, res.name, wrap_exception=False)


class _FakeResult(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class PrintResultTestCase(test_utils.TestCase):
    @mock.patch('sys.stdout', six.StringIO())
    def test_print_dict(self):
        dict = {'key': 'value'}
        utils.print_dict(dict)
        self.assertEqual('+----------+-------+\n'
                         '| Property | Value |\n'
                         '+----------+-------+\n'
                         '| key      | value |\n'
                         '+----------+-------+\n',
                         sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_dict_wrap(self):
        dict = {'key1': 'not wrapped',
                'key2': 'this will be wrapped'}
        utils.print_dict(dict, wrap=16)
        self.assertEqual('+----------+--------------+\n'
                         '| Property | Value        |\n'
                         '+----------+--------------+\n'
                         '| key1     | not wrapped  |\n'
                         '| key2     | this will be |\n'
                         '|          | wrapped      |\n'
                         '+----------+--------------+\n',
                         sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_list_sort_by_str(self):
        objs = [_FakeResult("k1", 1),
                _FakeResult("k3", 2),
                _FakeResult("k2", 3)]

        utils.print_list(objs, ["Name", "Value"], sortby_index=0)

        self.assertEqual('+------+-------+\n'
                         '| Name | Value |\n'
                         '+------+-------+\n'
                         '| k1   | 1     |\n'
                         '| k2   | 3     |\n'
                         '| k3   | 2     |\n'
                         '+------+-------+\n',
                         sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_list_sort_by_integer(self):
        objs = [_FakeResult("k1", 1),
                _FakeResult("k3", 2),
                _FakeResult("k2", 3)]

        utils.print_list(objs, ["Name", "Value"], sortby_index=1)

        self.assertEqual('+------+-------+\n'
                         '| Name | Value |\n'
                         '+------+-------+\n'
                         '| k1   | 1     |\n'
                         '| k3   | 2     |\n'
                         '| k2   | 3     |\n'
                         '+------+-------+\n',
                         sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_unicode_list(self):
        objs = [_FakeResult("k", u'\u2026')]
        utils.print_list(objs, ["Name", "Value"])
        if six.PY3:
            s = u'\u2026'
        else:
            s = encodeutils.safe_encode(u'\u2026')
        self.assertEqual('+------+-------+\n'
                         '| Name | Value |\n'
                         '+------+-------+\n'
                         '| k    | %s     |\n'
                         '+------+-------+\n' % s,
                         sys.stdout.getvalue())

    # without sorting
    @mock.patch('sys.stdout', six.StringIO())
    def test_print_list_sort_by_none(self):
        objs = [_FakeResult("k1", 1),
                _FakeResult("k3", 3),
                _FakeResult("k2", 2)]

        utils.print_list(objs, ["Name", "Value"], sortby_index=None)

        self.assertEqual('+------+-------+\n'
                         '| Name | Value |\n'
                         '+------+-------+\n'
                         '| k1   | 1     |\n'
                         '| k3   | 3     |\n'
                         '| k2   | 2     |\n'
                         '+------+-------+\n',
                         sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_dict_dictionary(self):
        dict = {'k': {'foo': 'bar'}}
        utils.print_dict(dict)
        self.assertEqual('+----------+----------------+\n'
                         '| Property | Value          |\n'
                         '+----------+----------------+\n'
                         '| k        | {"foo": "bar"} |\n'
                         '+----------+----------------+\n',
                         sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_dict_list_dictionary(self):
        dict = {'k': [{'foo': 'bar'}]}
        utils.print_dict(dict)
        self.assertEqual('+----------+------------------+\n'
                         '| Property | Value            |\n'
                         '+----------+------------------+\n'
                         '| k        | [{"foo": "bar"}] |\n'
                         '+----------+------------------+\n',
                         sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_dict_list(self):
        dict = {'k': ['foo', 'bar']}
        utils.print_dict(dict)
        self.assertEqual('+----------+----------------+\n'
                         '| Property | Value          |\n'
                         '+----------+----------------+\n'
                         '| k        | ["foo", "bar"] |\n'
                         '+----------+----------------+\n',
                         sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_large_dict_list(self):
        dict = {'k': ['foo1', 'bar1', 'foo2', 'bar2',
                      'foo3', 'bar3', 'foo4', 'bar4']}
        utils.print_dict(dict, wrap=40)
        self.assertEqual(
            '+----------+------------------------------------------+\n'
            '| Property | Value                                    |\n'
            '+----------+------------------------------------------+\n'
            '| k        | ["foo1", "bar1", "foo2", "bar2", "foo3", |\n'
            '|          | "bar3", "foo4", "bar4"]                  |\n'
            '+----------+------------------------------------------+\n',
            sys.stdout.getvalue())

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_unicode_dict(self):
        dict = {'k': u'\u2026'}
        utils.print_dict(dict)
        if six.PY3:
            s = u'\u2026'
        else:
            s = encodeutils.safe_encode(u'\u2026')
        self.assertEqual('+----------+-------+\n'
                         '| Property | Value |\n'
                         '+----------+-------+\n'
                         '| k        | %s     |\n'
                         '+----------+-------+\n' % s,
                         sys.stdout.getvalue())


class FlattenTestCase(test_utils.TestCase):
    def test_flattening(self):
        squashed = utils.flatten_dict(
            {'a1': {'b1': 1234,
                    'b2': 'string',
                    'b3': set((1, 2, 3)),
                    'b4': {'c1': ['l', 'l', ['l']],
                           'c2': 'string'}},
             'a2': ['l'],
             'a3': ('t',),
             'a4': {}})

        self.assertEqual({'a1_b1': 1234,
                          'a1_b2': 'string',
                          'a1_b3': set([1, 2, 3]),
                          'a1_b4_c1': ['l', 'l', ['l']],
                          'a1_b4_c2': 'string',
                          'a2': ['l'],
                          'a3': ('t',),
                          'a4': {}},
                         squashed)

    def test_pretty_choice_dict(self):
        d = {}
        r = utils.pretty_choice_dict(d)
        self.assertEqual("", r)

        d = {"k1": "v1",
             "k2": "v2",
             "k3": "v3"}
        r = utils.pretty_choice_dict(d)
        self.assertEqual("'k1=v1', 'k2=v2', 'k3=v3'", r)


class ValidationsTestCase(test_utils.TestCase):
    def test_validate_flavor_metadata_keys_with_valid_keys(self):
        valid_keys = ['key1', 'month.price', 'I-Am:AK-ey.01-', 'spaces and _']
        utils.validate_flavor_metadata_keys(valid_keys)

    def test_validate_flavor_metadata_keys_with_invalid_keys(self):
        invalid_keys = ['/1', '?1', '%1', '<', '>', '\1']
        for key in invalid_keys:
            try:
                utils.validate_flavor_metadata_keys([key])
                self.fail("Invalid key passed validation: %s" % key)
            except exceptions.CommandError as ce:
                self.assertIn(key, str(ce))


class ResourceManagerExtraKwargsHookTestCase(test_utils.TestCase):
    def test_get_resource_manager_extra_kwargs_hook_test(self):
        do_foo = mock.MagicMock()

        def hook1(args):
            return {'kwarg1': 'v_hook1'}

        def hook2(args):
            return {'kwarg1': 'v_hook2'}
        do_foo.resource_manager_kwargs_hooks = [hook1, hook2]
        args = {}
        exc = self.assertRaises(exceptions.NoUniqueMatch,
                                utils.get_resource_manager_extra_kwargs,
                                do_foo,
                                args)
        except_error = ("Hook 'hook2' is attempting to redefine "
                        "attributes")
        self.assertIn(except_error, six.text_type(exc))


class DoActionOnManyTestCase(test_utils.TestCase):

    def _test_do_action_on_many(self, side_effect, fail):
        action = mock.Mock(side_effect=side_effect)

        if fail:
            self.assertRaises(exceptions.CommandError,
                              utils.do_action_on_many,
                              action, [1, 2], 'success with %s', 'error')
        else:
            utils.do_action_on_many(action, [1, 2], 'success with %s', 'error')
        action.assert_has_calls([mock.call(1), mock.call(2)])

    def test_do_action_on_many_success(self):
        self._test_do_action_on_many([None, None], fail=False)

    def test_do_action_on_many_first_fails(self):
        self._test_do_action_on_many([Exception(), None], fail=True)

    def test_do_action_on_many_last_fails(self):
        self._test_do_action_on_many([None, Exception()], fail=True)


class RecordTimeTestCase(test_utils.TestCase):

    def test_record_time(self):
        times = []

        with utils.record_time(times, True, 'a', 'b'):
            pass
        self.assertEqual(1, len(times))
        self.assertEqual(3, len(times[0]))
        self.assertEqual('a b', times[0][0])
        self.assertIsInstance(times[0][1], float)
        self.assertIsInstance(times[0][2], float)

        times = []
        with utils.record_time(times, False, 'x'):
            pass
        self.assertEqual(0, len(times))


class PrepareQueryStringTestCase(test_utils.TestCase):
    def test_convert_dict_to_string(self):
        ustr = b'?\xd0\xbf=1&\xd1\x80=2'
        if six.PY3:
            # in py3 real unicode symbols will be urlencoded
            ustr = ustr.decode('utf8')
        cases = (
            ({}, ''),
            ({'2': 2, '10': 1}, '?10=1&2=2'),
            ({'abc': 1, 'abc1': 2}, '?abc=1&abc1=2'),
            ({b'\xd0\xbf': 1, b'\xd1\x80': 2}, ustr),
            ({(1, 2): '1', (3, 4): '2'}, '?(1, 2)=1&(3, 4)=2')
        )
        for case in cases:
            self.assertEqual(
                case[1],
                parse.unquote_plus(utils.prepare_query_string(case[0])))

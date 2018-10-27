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

import requests
import six

from novaclient import api_versions
from novaclient import base
from novaclient import exceptions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import flavors


def create_response_obj_with_header():
    resp = requests.Response()
    resp.headers['x-openstack-request-id'] = fakes.FAKE_REQUEST_ID
    return resp


def create_response_obj_with_compute_header():
    resp = requests.Response()
    resp.headers['x-compute-request-id'] = fakes.FAKE_REQUEST_ID
    return resp


class BaseTest(utils.TestCase):
    def test_resource_repr(self):
        r = base.Resource(None, dict(foo="bar", baz="spam"))
        self.assertEqual("<Resource baz=spam, foo=bar>", repr(r))

    def test_getid(self):
        self.assertEqual(4, base.getid(4))

        class TmpObject(object):
            id = 4
        self.assertEqual(4, base.getid(TmpObject))

    def test_resource_lazy_getattr(self):
        cs = fakes.FakeClient(api_versions.APIVersion("2.0"))
        f = flavors.Flavor(cs.flavors, {'id': 1})
        self.assertEqual('256 MiB Server', f.name)
        cs.assert_called('GET', '/flavors/1')

        # Missing stuff still fails after a second get
        self.assertRaises(AttributeError, getattr, f, 'blahblah')

    def test_eq(self):
        # Two resources of the same type with the same id: equal
        r1 = base.Resource(None, {'id': 1, 'name': 'hi'})
        r2 = base.Resource(None, {'id': 1, 'name': 'hello'})
        self.assertEqual(r1, r2)

        # Two resources of different types: never equal
        r1 = base.Resource(None, {'id': 1})
        r2 = flavors.Flavor(None, {'id': 1})
        self.assertNotEqual(r1, r2)

        # Two resources with no ID: equal if their info is equal
        r1 = base.Resource(None, {'name': 'joe', 'age': 12})
        r2 = base.Resource(None, {'name': 'joe', 'age': 12})
        self.assertEqual(r1, r2)

    def test_ne(self):
        # Two resources of different types: never equal
        r1 = base.Resource(None, {'id': 1, 'name': 'test'})
        r2 = object()
        self.assertNotEqual(r1, r2)

    def test_findall_invalid_attribute(self):
        cs = fakes.FakeClient(api_versions.APIVersion("2.0"))
        # Make sure findall with an invalid attribute doesn't cause errors.
        # The following should not raise an exception.
        cs.flavors.findall(vegetable='carrot')

        # However, find() should raise an error
        self.assertRaises(exceptions.NotFound,
                          cs.flavors.find,
                          vegetable='carrot')

    def test_resource_object_with_request_ids(self):
        resp_obj = create_response_obj_with_header()
        r = base.Resource(None, {"name": "1"}, resp=resp_obj)
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, r.request_ids)

    def test_resource_object_with_compute_request_ids(self):
        resp_obj = create_response_obj_with_compute_header()
        r = base.Resource(None, {"name": "1"}, resp=resp_obj)
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, r.request_ids)


class ListWithMetaTest(utils.TestCase):
    def test_list_with_meta(self):
        resp = create_response_obj_with_header()
        obj = base.ListWithMeta([], resp)
        self.assertEqual([], obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


class DictWithMetaTest(utils.TestCase):
    def test_dict_with_meta(self):
        resp = create_response_obj_with_header()
        obj = base.DictWithMeta({}, resp)
        self.assertEqual({}, obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


class TupleWithMetaTest(utils.TestCase):
    def test_tuple_with_meta(self):
        resp = create_response_obj_with_header()
        expected_tuple = (1, 2)
        obj = base.TupleWithMeta(expected_tuple, resp)
        self.assertEqual(expected_tuple, obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


class StrWithMetaTest(utils.TestCase):
    def test_str_with_meta(self):
        resp = create_response_obj_with_header()
        obj = base.StrWithMeta("test-str", resp)
        self.assertEqual("test-str", obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


class BytesWithMetaTest(utils.TestCase):
    def test_bytes_with_meta(self):
        resp = create_response_obj_with_header()
        obj = base.BytesWithMeta(b'test-bytes', resp)
        self.assertEqual(b'test-bytes', obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


if six.PY2:
    class UnicodeWithMetaTest(utils.TestCase):
        def test_unicode_with_meta(self):
            resp = create_response_obj_with_header()
            obj = base.UnicodeWithMeta(u'test-unicode', resp)
            self.assertEqual(u'test-unicode', obj)
            # Check request_ids attribute is added to obj
            self.assertTrue(hasattr(obj, 'request_ids'))
            self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)

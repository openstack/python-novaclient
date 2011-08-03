from __future__ import absolute_import

import mock
from nose.tools import assert_equal, assert_not_equal, assert_raises

from novaclient.v1_0 import flavors
from novaclient.v1_0 import exceptions
from novaclient.v1_0 import base

from .fakes import FakeClient

os = FakeClient()


def test_resource_repr():
    r = base.Resource(None, dict(foo="bar", baz="spam"))
    assert_equal(repr(r), "<Resource baz=spam, foo=bar>")


def test_getid():
    assert_equal(base.getid(4), 4)

    class O(object):
        id = 4
    assert_equal(base.getid(O), 4)


def test_resource_lazy_getattr():
    f = flavors.Flavor(os.flavors, {'id': 1})
    assert_equal(f.name, '256 MB Server')
    os.assert_called('GET', '/flavors/1')

    # Missing stuff still fails after a second get
    assert_raises(AttributeError, getattr, f, 'blahblah')
    os.assert_called('GET', '/flavors/1')


def test_eq():
    # Two resources of the same type with the same id: equal
    r1 = base.Resource(None, {'id': 1, 'name': 'hi'})
    r2 = base.Resource(None, {'id': 1, 'name': 'hello'})
    assert_equal(r1, r2)

    # Two resoruces of different types: never equal
    r1 = base.Resource(None, {'id': 1})
    r2 = flavors.Flavor(None, {'id': 1})
    assert_not_equal(r1, r2)

    # Two resources with no ID: equal if their info is equal
    r1 = base.Resource(None, {'name': 'joe', 'age': 12})
    r2 = base.Resource(None, {'name': 'joe', 'age': 12})
    assert_equal(r1, r2)


def test_findall_invalid_attribute():
    # Make sure findall with an invalid attribute doesn't cause errors.
    # The following should not raise an exception.
    os.flavors.findall(vegetable='carrot')

    # However, find() should raise an error
    assert_raises(exceptions.NotFound, os.flavors.find, vegetable='carrot')

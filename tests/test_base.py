
import mock
import cloudservers.base
from cloudservers import Flavor
from cloudservers.exceptions import NotFound
from cloudservers.base import Resource
from nose.tools import assert_equal, assert_not_equal, assert_raises
from fakeserver import FakeServer

cs = FakeServer()


def test_resource_repr():
    r = Resource(None, dict(foo="bar", baz="spam"))
    assert_equal(repr(r), "<Resource baz=spam, foo=bar>")


def test_getid():
    assert_equal(cloudservers.base.getid(4), 4)

    class O(object):
        id = 4
    assert_equal(cloudservers.base.getid(O), 4)


def test_resource_lazy_getattr():
    f = Flavor(cs.flavors, {'id': 1})
    assert_equal(f.name, '256 MB Server')
    cs.assert_called('GET', '/flavors/1')

    # Missing stuff still fails after a second get
    assert_raises(AttributeError, getattr, f, 'blahblah')
    cs.assert_called('GET', '/flavors/1')


def test_eq():
    # Two resources of the same type with the same id: equal
    r1 = Resource(None, {'id': 1, 'name': 'hi'})
    r2 = Resource(None, {'id': 1, 'name': 'hello'})
    assert_equal(r1, r2)

    # Two resoruces of different types: never equal
    r1 = Resource(None, {'id': 1})
    r2 = Flavor(None, {'id': 1})
    assert_not_equal(r1, r2)

    # Two resources with no ID: equal if their info is equal
    r1 = Resource(None, {'name': 'joe', 'age': 12})
    r2 = Resource(None, {'name': 'joe', 'age': 12})
    assert_equal(r1, r2)


def test_findall_invalid_attribute():
    # Make sure findall with an invalid attribute doesn't cause errors.
    # The following should not raise an exception.
    cs.flavors.findall(vegetable='carrot')

    # However, find() should raise an error
    assert_raises(NotFound, cs.flavors.find, vegetable='carrot')

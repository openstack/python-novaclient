from __future__ import absolute_import

from nose.tools import assert_raises, assert_equal

from novaclient.v1_0 import flavors
from novaclient.v1_0 import exceptions

from .fakes import FakeClient
from .utils import assert_isinstance

os = FakeClient()


def test_list_flavors():
    fl = os.flavors.list()
    os.assert_called('GET', '/flavors/detail')
    [assert_isinstance(f, flavors.Flavor) for f in fl]


def test_list_flavors_undetailed():
    fl = os.flavors.list(detailed=False)
    os.assert_called('GET', '/flavors')
    [assert_isinstance(f, flavors.Flavor) for f in fl]


def test_get_flavor_details():
    f = os.flavors.get(1)
    os.assert_called('GET', '/flavors/1')
    assert_isinstance(f, flavors.Flavor)
    assert_equal(f.ram, 256)
    assert_equal(f.disk, 10)


def test_find():
    f = os.flavors.find(ram=256)
    os.assert_called('GET', '/flavors/detail')
    assert_equal(f.name, '256 MB Server')

    f = os.flavors.find(disk=20)
    assert_equal(f.name, '512 MB Server')

    assert_raises(exceptions.NotFound, os.flavors.find, disk=12345)

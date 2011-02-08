import StringIO
from nose.tools import assert_equal
from fakeserver import FakeServer
from utils import assert_isinstance
from novatools import Zone

os = FakeServer()


def test_list_zones():
    sl = os.zones.list()
    os.assert_called('GET', '/zones/detail')
    [assert_isinstance(s, Zone) for s in sl]


def test_get_zone_details():
    s = os.zones.get(1)
    os.assert_called('GET', '/zones/1')
    assert_isinstance(s, Zone)
    assert_equal(s.id, 1)
    assert_equal(s.auth_url, 'http://foo.com')


def test_create_zone():
    s = os.zones.create(
        name="My zone",
        auth_url="http://foo.com"
    )
    os.assert_called('POST', '/zones')
    assert_isinstance(s, Zone)


def test_update_zone():
    s = os.zones.get(1)

    # Update via instance
    s.update(name='hi')
    os.assert_called('PUT', '/zones/1')
    s.update(name='hi', auth_url='there')
    os.assert_called('PUT', '/zones/1')

    # Silly, but not an error
    s.update()

    # Update via manager
    os.zones.update(s, name='hi')
    os.assert_called('PUT', '/zones/1')
    os.zones.update(1, auth_url='there')
    os.assert_called('PUT', '/zones/1')
    os.zones.update(s, name='hi', auth_url='there')
    os.assert_called('PUT', '/zones/1')


def test_delete_zone():
    s = os.zones.get(1)
    s.delete()
    os.assert_called('DELETE', '/zones/1')
    os.zones.delete(1)
    os.assert_called('DELETE', '/zones/1')
    os.zones.delete(s)
    os.assert_called('DELETE', '/zones/1')


def test_find():
    s = os.zones.find(name='zone2')
    os.assert_called('GET', '/zones/detail')
    assert_equal(s.name, 'zone2')

    # Find with multiple results arbitraility returns the first item
    s = os.zones.find(auth_url='http://foo.com')
    sl = os.zones.findall(auth_url='http://foo.com')
    assert_equal(sl[0], s)
    assert_equal([s.id for s in sl], [1, 2])

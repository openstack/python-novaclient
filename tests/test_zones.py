import StringIO
from nose.tools import assert_equal
from fakeserver import FakeServer
from utils import assert_isinstance
from novaclient import Zone

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
    assert_equal(s.api_url, 'http://foo.com')


def test_create_zone():
    s = os.zones.create(api_url="http://foo.com", username='bob',
                        password='xxx')
    os.assert_called('POST', '/zones')
    assert_isinstance(s, Zone)


def test_update_zone():
    s = os.zones.get(1)

    # Update via instance
    s.update(api_url='http://blah.com')
    os.assert_called('PUT', '/zones/1')
    s.update(api_url='http://blah.com', username='alice', password='xxx')
    os.assert_called('PUT', '/zones/1')

    # Silly, but not an error
    s.update()

    # Update via manager
    os.zones.update(s, api_url='http://blah.com')
    os.assert_called('PUT', '/zones/1')
    os.zones.update(1, api_url= 'http://blah.com')
    os.assert_called('PUT', '/zones/1')
    os.zones.update(s, api_url='http://blah.com', username='fred',
                       password='zip')
    os.assert_called('PUT', '/zones/1')


def test_delete_zone():
    s = os.zones.get(1)
    s.delete()
    os.assert_called('DELETE', '/zones/1')
    os.zones.delete(1)
    os.assert_called('DELETE', '/zones/1')
    os.zones.delete(s)
    os.assert_called('DELETE', '/zones/1')


def test_find_zone():
    s = os.zones.find(password='qwerty')
    os.assert_called('GET', '/zones/detail')
    assert_equal(s.username, 'bob')

    # Find with multiple results returns the first item
    s = os.zones.find(api_url='http://foo.com')
    sl = os.zones.findall(api_url='http://foo.com')
    assert_equal(sl[0], s)
    assert_equal([s.id for s in sl], [1, 2])

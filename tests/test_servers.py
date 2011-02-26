import StringIO
from nose.tools import assert_equal
from fakeserver import FakeServer
from utils import assert_isinstance
from novaclient import Server

cs = FakeServer()


def test_list_servers():
    sl = cs.servers.list()
    cs.assert_called('GET', '/servers/detail')
    [assert_isinstance(s, Server) for s in sl]


def test_get_server_details():
    s = cs.servers.get(1234)
    cs.assert_called('GET', '/servers/1234')
    assert_isinstance(s, Server)
    assert_equal(s.id, 1234)
    assert_equal(s.status, 'BUILD')


def test_create_server():
    s = cs.servers.create(
        name="My server",
        image=1,
        flavor=1,
        meta={'foo': 'bar'},
        ipgroup=1,
        files={
            '/etc/passwd': 'some data',                 # a file
            '/tmp/foo.txt': StringIO.StringIO('data')   # a stream
        }
    )
    cs.assert_called('POST', '/servers')
    assert_isinstance(s, Server)


def test_update_server():
    s = cs.servers.get(1234)

    # Update via instance
    s.update(name='hi')
    cs.assert_called('PUT', '/servers/1234')
    s.update(name='hi', password='there')
    cs.assert_called('PUT', '/servers/1234')

    # Silly, but not an error
    s.update()

    # Update via manager
    cs.servers.update(s, name='hi')
    cs.assert_called('PUT', '/servers/1234')
    cs.servers.update(1234, password='there')
    cs.assert_called('PUT', '/servers/1234')
    cs.servers.update(s, name='hi', password='there')
    cs.assert_called('PUT', '/servers/1234')


def test_delete_server():
    s = cs.servers.get(1234)
    s.delete()
    cs.assert_called('DELETE', '/servers/1234')
    cs.servers.delete(1234)
    cs.assert_called('DELETE', '/servers/1234')
    cs.servers.delete(s)
    cs.assert_called('DELETE', '/servers/1234')


def test_find():
    s = cs.servers.find(name='sample-server')
    cs.assert_called('GET', '/servers/detail')
    assert_equal(s.name, 'sample-server')

    # Find with multiple results arbitraility returns the first item
    s = cs.servers.find(flavorId=1)
    sl = cs.servers.findall(flavorId=1)
    assert_equal(sl[0], s)
    assert_equal([s.id for s in sl], [1234, 5678])


def test_share_ip():
    s = cs.servers.get(1234)

    # Share via instance
    s.share_ip(ipgroup=1, address='1.2.3.4')
    cs.assert_called('PUT', '/servers/1234/ips/public/1.2.3.4')

    # Share via manager
    cs.servers.share_ip(s, ipgroup=1, address='1.2.3.4', configure=False)
    cs.assert_called('PUT', '/servers/1234/ips/public/1.2.3.4')


def test_unshare_ip():
    s = cs.servers.get(1234)

    # Unshare via instance
    s.unshare_ip('1.2.3.4')
    cs.assert_called('DELETE', '/servers/1234/ips/public/1.2.3.4')

    # Unshare via manager
    cs.servers.unshare_ip(s, '1.2.3.4')
    cs.assert_called('DELETE', '/servers/1234/ips/public/1.2.3.4')


def test_reboot_server():
    s = cs.servers.get(1234)
    s.reboot()
    cs.assert_called('POST', '/servers/1234/action')
    cs.servers.reboot(s, type='HARD')
    cs.assert_called('POST', '/servers/1234/action')


def test_rebuild_server():
    s = cs.servers.get(1234)
    s.rebuild(image=1)
    cs.assert_called('POST', '/servers/1234/action')
    cs.servers.rebuild(s, image=1)
    cs.assert_called('POST', '/servers/1234/action')


def test_resize_server():
    s = cs.servers.get(1234)
    s.resize(flavor=1)
    cs.assert_called('POST', '/servers/1234/action')
    cs.servers.resize(s, flavor=1)
    cs.assert_called('POST', '/servers/1234/action')


def test_confirm_resized_server():
    s = cs.servers.get(1234)
    s.confirm_resize()
    cs.assert_called('POST', '/servers/1234/action')
    cs.servers.confirm_resize(s)
    cs.assert_called('POST', '/servers/1234/action')


def test_revert_resized_server():
    s = cs.servers.get(1234)
    s.revert_resize()
    cs.assert_called('POST', '/servers/1234/action')
    cs.servers.revert_resize(s)
    cs.assert_called('POST', '/servers/1234/action')

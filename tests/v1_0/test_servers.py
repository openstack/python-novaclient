from __future__ import absolute_import

import StringIO

from nose.tools import assert_equal

from novaclient.v1_0 import servers

from .fakes import FakeClient
from .utils import assert_isinstance


os = FakeClient()


def test_list_servers():
    sl = os.servers.list()
    os.assert_called('GET', '/servers/detail')
    [assert_isinstance(s, servers.Server) for s in sl]


def test_list_servers_undetailed():
    sl = os.servers.list(detailed=False)
    os.assert_called('GET', '/servers')
    [assert_isinstance(s, servers.Server) for s in sl]


def test_get_server_details():
    s = os.servers.get(1234)
    os.assert_called('GET', '/servers/1234')
    assert_isinstance(s, servers.Server)
    assert_equal(s.id, 1234)
    assert_equal(s.status, 'BUILD')


def test_create_server():
    s = os.servers.create(
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
    os.assert_called('POST', '/servers')
    assert_isinstance(s, servers.Server)


def test_update_server():
    s = os.servers.get(1234)

    # Update via instance
    s.update(name='hi')
    os.assert_called('PUT', '/servers/1234')
    s.update(name='hi', password='there')
    os.assert_called('PUT', '/servers/1234')

    # Silly, but not an error
    s.update()

    # Update via manager
    os.servers.update(s, name='hi')
    os.assert_called('PUT', '/servers/1234')
    os.servers.update(1234, password='there')
    os.assert_called('PUT', '/servers/1234')
    os.servers.update(s, name='hi', password='there')
    os.assert_called('PUT', '/servers/1234')


def test_delete_server():
    s = os.servers.get(1234)
    s.delete()
    os.assert_called('DELETE', '/servers/1234')
    os.servers.delete(1234)
    os.assert_called('DELETE', '/servers/1234')
    os.servers.delete(s)
    os.assert_called('DELETE', '/servers/1234')


def test_find():
    s = os.servers.find(name='sample-server')
    os.assert_called('GET', '/servers/detail')
    assert_equal(s.name, 'sample-server')

    # Find with multiple results arbitraility returns the first item
    s = os.servers.find(flavorId=1)
    sl = os.servers.findall(flavorId=1)
    assert_equal(sl[0], s)
    assert_equal([s.id for s in sl], [1234, 5678])


def test_share_ip():
    s = os.servers.get(1234)

    # Share via instance
    s.share_ip(ipgroup=1, address='1.2.3.4')
    os.assert_called('PUT', '/servers/1234/ips/public/1.2.3.4')

    # Share via manager
    os.servers.share_ip(s, ipgroup=1, address='1.2.3.4', configure=False)
    os.assert_called('PUT', '/servers/1234/ips/public/1.2.3.4')


def test_unshare_ip():
    s = os.servers.get(1234)

    # Unshare via instance
    s.unshare_ip('1.2.3.4')
    os.assert_called('DELETE', '/servers/1234/ips/public/1.2.3.4')

    # Unshare via manager
    os.servers.unshare_ip(s, '1.2.3.4')
    os.assert_called('DELETE', '/servers/1234/ips/public/1.2.3.4')


def test_reboot_server():
    s = os.servers.get(1234)
    s.reboot()
    os.assert_called('POST', '/servers/1234/action')
    os.servers.reboot(s, type='HARD')
    os.assert_called('POST', '/servers/1234/action')


def test_rebuild_server():
    s = os.servers.get(1234)
    s.rebuild(image=1)
    os.assert_called('POST', '/servers/1234/action')
    os.servers.rebuild(s, image=1)
    os.assert_called('POST', '/servers/1234/action')


def test_resize_server():
    s = os.servers.get(1234)
    s.resize(flavor=1)
    os.assert_called('POST', '/servers/1234/action')
    os.servers.resize(s, flavor=1)
    os.assert_called('POST', '/servers/1234/action')


def test_confirm_resized_server():
    s = os.servers.get(1234)
    s.confirm_resize()
    os.assert_called('POST', '/servers/1234/action')
    os.servers.confirm_resize(s)
    os.assert_called('POST', '/servers/1234/action')


def test_revert_resized_server():
    s = os.servers.get(1234)
    s.revert_resize()
    os.assert_called('POST', '/servers/1234/action')
    os.servers.revert_resize(s)
    os.assert_called('POST', '/servers/1234/action')


def test_migrate_server():
    s = os.servers.get(1234)
    s.migrate()
    os.assert_called('POST', '/servers/1234/action')
    os.servers.migrate(s)
    os.assert_called('POST', '/servers/1234/action')


def test_add_fixed_ip():
    s = os.servers.get(1234)
    s.add_fixed_ip(1)
    os.assert_called('POST', '/servers/1234/action')
    os.servers.add_fixed_ip(s, 1)
    os.assert_called('POST', '/servers/1234/action')


def test_remove_fixed_ip():
    s = os.servers.get(1234)
    s.remove_fixed_ip('10.0.0.1')
    os.assert_called('POST', '/servers/1234/action')
    os.servers.remove_fixed_ip(s, '10.0.0.1')
    os.assert_called('POST', '/servers/1234/action')

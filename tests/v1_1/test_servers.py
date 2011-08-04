
import StringIO

from novaclient.v1_1 import servers
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class ServersTest(utils.TestCase):

    def test_list_servers(self):
        sl = cs.servers.list()
        cs.assert_called('GET', '/servers/detail')
        [self.assertTrue(isinstance(s, servers.Server)) for s in sl]

    def test_list_servers_undetailed(self):
        sl = cs.servers.list(detailed=False)
        cs.assert_called('GET', '/servers')
        [self.assertTrue(isinstance(s, servers.Server)) for s in sl]

    def test_get_server_details(self):
        s = cs.servers.get(1234)
        cs.assert_called('GET', '/servers/1234')
        self.assertTrue(isinstance(s, servers.Server))
        self.assertEqual(s.id, 1234)
        self.assertEqual(s.status, 'BUILD')

    def test_create_server(self):
        s = cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': StringIO.StringIO('data')   # a stream
            }
        )
        cs.assert_called('POST', '/servers')
        self.assertTrue(isinstance(s, servers.Server))

    def test_update_server(self):
        s = cs.servers.get(1234)

        # Update via instance
        s.update(name='hi')
        cs.assert_called('PUT', '/servers/1234')
        s.update(name='hi')
        cs.assert_called('PUT', '/servers/1234')

        # Silly, but not an error
        s.update()

        # Update via manager
        cs.servers.update(s, name='hi')
        cs.assert_called('PUT', '/servers/1234')

    def test_delete_server(self):
        s = cs.servers.get(1234)
        s.delete()
        cs.assert_called('DELETE', '/servers/1234')
        cs.servers.delete(1234)
        cs.assert_called('DELETE', '/servers/1234')
        cs.servers.delete(s)
        cs.assert_called('DELETE', '/servers/1234')

    def test_find(self):
        s = cs.servers.find(name='sample-server')
        cs.assert_called('GET', '/servers/detail')
        self.assertEqual(s.name, 'sample-server')

        # Find with multiple results arbitraility returns the first item
        s = cs.servers.find(flavor={"id": 1, "name": "256 MB Server"})
        sl = cs.servers.findall(flavor={"id": 1, "name": "256 MB Server"})
        self.assertEqual(sl[0], s)
        self.assertEqual([s.id for s in sl], [1234, 5678])

    def test_reboot_server(self):
        s = cs.servers.get(1234)
        s.reboot()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.reboot(s, type='HARD')
        cs.assert_called('POST', '/servers/1234/action')

    def test_rebuild_server(self):
        s = cs.servers.get(1234)
        s.rebuild(image=1)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.rebuild(s, image=1)
        cs.assert_called('POST', '/servers/1234/action')

    def test_resize_server(self):
        s = cs.servers.get(1234)
        s.resize(flavor=1)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.resize(s, flavor=1)
        cs.assert_called('POST', '/servers/1234/action')

    def test_confirm_resized_server(self):
        s = cs.servers.get(1234)
        s.confirm_resize()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.confirm_resize(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_revert_resized_server(self):
        s = cs.servers.get(1234)
        s.revert_resize()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.revert_resize(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_migrate_server(self):
        s = cs.servers.get(1234)
        s.migrate()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.migrate(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_add_fixed_ip(self):
        s = cs.servers.get(1234)
        s.add_fixed_ip(1)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.add_fixed_ip(s, 1)
        cs.assert_called('POST', '/servers/1234/action')

    def test_remove_fixed_ip(self):
        s = cs.servers.get(1234)
        s.remove_fixed_ip('10.0.0.1')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.remove_fixed_ip(s, '10.0.0.1')
        cs.assert_called('POST', '/servers/1234/action')

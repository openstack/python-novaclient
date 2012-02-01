import StringIO

from novaclient.v1_1 import servers
from tests import utils
from tests.v1_1 import fakes


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
            userdata="hello moto",
            key_name="fakekey",
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': StringIO.StringIO('data'),   # a stream
            }
        )
        cs.assert_called('POST', '/servers')
        self.assertTrue(isinstance(s, servers.Server))

    def test_create_server_userdata_file_object(self):
        s = cs.servers.create(
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            userdata=StringIO.StringIO('hello moto'),
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': StringIO.StringIO('data'),   # a stream
            },
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

    def test_delete_server_meta(self):
        s = cs.servers.delete_meta(1234, ['test_key'])
        cs.assert_called('DELETE', '/servers/1234/metadata/test_key')

    def test_set_server_meta(self):
        s = cs.servers.set_meta(1234, {'test_key': 'test_value'})
        reval = cs.assert_called('POST', '/servers/1234/metadata',
                         {'metadata': {'test_key': 'test_value'}})

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
        s.rebuild(image=1, password='5678')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.rebuild(s, image=1, password='5678')
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

    def test_add_floating_ip(self):
        s = cs.servers.get(1234)
        s.add_floating_ip('11.0.0.1')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.add_floating_ip(s, '11.0.0.1')
        cs.assert_called('POST', '/servers/1234/action')
        f = cs.floating_ips.list()[0]
        cs.servers.add_floating_ip(s, f)
        cs.assert_called('POST', '/servers/1234/action')
        s.add_floating_ip(f)
        cs.assert_called('POST', '/servers/1234/action')

    def test_remove_floating_ip(self):
        s = cs.servers.get(1234)
        s.remove_floating_ip('11.0.0.1')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.remove_floating_ip(s, '11.0.0.1')
        cs.assert_called('POST', '/servers/1234/action')
        f = cs.floating_ips.list()[0]
        cs.servers.remove_floating_ip(s, f)
        cs.assert_called('POST', '/servers/1234/action')
        s.remove_floating_ip(f)
        cs.assert_called('POST', '/servers/1234/action')

    def test_rescue(self):
        s = cs.servers.get(1234)
        s.rescue()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.rescue(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_unrescue(self):
        s = cs.servers.get(1234)
        s.unrescue()
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.unrescue(s)
        cs.assert_called('POST', '/servers/1234/action')

    def test_get_console_output_without_length(self):
        success = 'foo'
        s = cs.servers.get(1234)
        s.get_console_output()
        self.assertEqual(s.get_console_output(), success)
        cs.assert_called('POST', '/servers/1234/action')

        cs.servers.get_console_output(s)
        self.assertEqual(cs.servers.get_console_output(s), success)
        cs.assert_called('POST', '/servers/1234/action')

    def test_get_console_output_with_length(self):
        success = 'foo'

        s = cs.servers.get(1234)
        s.get_console_output(length=50)
        self.assertEqual(s.get_console_output(length=50), success)
        cs.assert_called('POST', '/servers/1234/action')

        cs.servers.get_console_output(s, length=50)
        self.assertEqual(cs.servers.get_console_output(s, length=50), success)
        cs.assert_called('POST', '/servers/1234/action')

    def test_get_server_actions(self):
        s = cs.servers.get(1234)
        actions = s.actions()
        self.assertTrue(actions is not None)
        cs.assert_called('GET', '/servers/1234/actions')

        actions_from_manager = cs.servers.actions(1234)
        self.assertTrue(actions_from_manager is not None)
        cs.assert_called('GET', '/servers/1234/actions')

        self.assertEqual(actions, actions_from_manager)

    def test_get_server_diagnostics(self):
        s = cs.servers.get(1234)
        diagnostics = s.diagnostics()
        self.assertTrue(diagnostics is not None)
        cs.assert_called('GET', '/servers/1234/diagnostics')

        diagnostics_from_manager = cs.servers.diagnostics(1234)
        self.assertTrue(diagnostics_from_manager is not None)
        cs.assert_called('GET', '/servers/1234/diagnostics')

        self.assertEqual(diagnostics, diagnostics_from_manager)

    def test_get_vnc_console(self):
        s = cs.servers.get(1234)
        s.get_vnc_console('fake')
        cs.assert_called('POST', '/servers/1234/action')

        cs.servers.get_vnc_console(s, 'fake')
        cs.assert_called('POST', '/servers/1234/action')

    def test_create_image(self):
        s = cs.servers.get(1234)
        s.create_image('123')
        cs.assert_called('POST', '/servers/1234/action')
        s.create_image('123', {})
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.create_image(s, '123')
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.create_image(s, '123', {})

    def test_live_migrate_server(self):
        s = cs.servers.get(1234)
        s.live_migrate(host='hostname', block_migration=False,
                       disk_over_commit=False)
        cs.assert_called('POST', '/servers/1234/action')
        cs.servers.live_migrate(s, host='hostname', block_migration=False,
                                disk_over_commit=False)
        cs.assert_called('POST', '/servers/1234/action')

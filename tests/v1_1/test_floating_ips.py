from novaclient import exceptions
from novaclient.v1_1 import floating_ips
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class FloatingIPsTest(utils.TestCase):

    def test_list_floating_ips(self):
        fl = cs.floating_ips.list()
        cs.assert_called('GET', '/os-floating-ips')
        [self.assertTrue(isinstance(f, floating_ips.FloatingIP)) for f in fl]

    def test_delete_floating_ip(self):
        fl = cs.floating_ips.list()[0]
        fl.delete()
        cs.assert_called('DELETE', '/os-floating-ips/1')
        cs.floating_ips.delete(1)
        cs.assert_called('DELETE', '/os-floating-ips/1')
        cs.floating_ips.delete(fl)
        cs.assert_called('DELETE', '/os-floating-ips/1')

    def test_create_floating_ip(self):
        fl = cs.floating_ips.create()
        cs.assert_called('POST', '/os-floating-ips')
        self.assertTrue(isinstance(fl, floating_ips.FloatingIP))

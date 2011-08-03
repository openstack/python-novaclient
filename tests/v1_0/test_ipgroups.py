
from novaclient.v1_0 import ipgroups
from tests.v1_0 import fakes
from tests import utils


cs = fakes.FakeClient()


class IPGroupTest(utils.TestCase):

    def test_list_ipgroups(self):
        ipl = cs.ipgroups.list()
        cs.assert_called('GET', '/shared_ip_groups/detail')
        [self.assertTrue(isinstance(ipg, ipgroups.IPGroup)) \
            for ipg in ipl]

    def test_list_ipgroups_undetailed(self):
        ipl = cs.ipgroups.list(detailed=False)
        cs.assert_called('GET', '/shared_ip_groups')
        [self.assertTrue(isinstance(ipg, ipgroups.IPGroup)) \
            for ipg in ipl]

    def test_get_ipgroup(self):
        ipg = cs.ipgroups.get(1)
        cs.assert_called('GET', '/shared_ip_groups/1')
        self.assertTrue(isinstance(ipg, ipgroups.IPGroup))

    def test_create_ipgroup(self):
        ipg = cs.ipgroups.create("My group", 1234)
        cs.assert_called('POST', '/shared_ip_groups')
        self.assertTrue(isinstance(ipg, ipgroups.IPGroup))

    def test_delete_ipgroup(self):
        ipg = cs.ipgroups.get(1)
        ipg.delete()
        cs.assert_called('DELETE', '/shared_ip_groups/1')
        cs.ipgroups.delete(ipg)
        cs.assert_called('DELETE', '/shared_ip_groups/1')
        cs.ipgroups.delete(1)
        cs.assert_called('DELETE', '/shared_ip_groups/1')

    def test_find(self):
        ipg = cs.ipgroups.find(name='group1')
        cs.assert_called('GET', '/shared_ip_groups/detail')
        self.assertEqual(ipg.name, 'group1')
        ipgl = cs.ipgroups.findall(id=1)
        self.assertEqual(ipgl, [ipgroups.IPGroup(None, {'id': 1})])

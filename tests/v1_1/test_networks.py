from novaclient import exceptions
from novaclient.v1_1 import networks
from tests import utils
from tests.v1_1 import fakes


cs = fakes.FakeClient()


class NetworksTest(utils.TestCase):

    def test_list_networks(self):
        fl = cs.networks.list()
        cs.assert_called('GET', '/os-networks')
        [self.assertTrue(isinstance(f, networks.Network)) for f in fl]

    def test_get_network(self):
        f = cs.networks.get(1)
        cs.assert_called('GET', '/os-networks/1')
        self.assertTrue(isinstance(f, networks.Network))

    def test_delete(self):
        cs.networks.delete('networkdelete')
        cs.assert_called('DELETE', '/os-networks/networkdelete')

    def test_create(self):
        f = cs.networks.create(label='foo')
        cs.assert_called('POST', '/os-networks',
                         {'network': {'label': 'foo'}})
        self.assertTrue(isinstance(f, networks.Network))

    def test_disassociate(self):
        cs.networks.disassociate('networkdisassociate')
        cs.assert_called('POST', '/os-networks/networkdisassociate/action',
                         {'disassociate': None})

    def test_add(self):
        cs.networks.add('networkadd')
        cs.assert_called('POST', '/os-networks/add',
                         {'id': 'networkadd'})

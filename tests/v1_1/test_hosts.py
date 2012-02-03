from novaclient.v1_1 import hosts
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class HostsTest(utils.TestCase):

    def test_describe_resource(self):
        hs = cs.hosts.get('host')
        cs.assert_called('GET', '/os-hosts/host')
        [self.assertTrue(isinstance(h, hosts.Host)) for h in hs]

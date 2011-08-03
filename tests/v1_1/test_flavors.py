
from novaclient import exceptions
from novaclient.v1_1 import flavors
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class FlavorsTest(utils.TestCase):

    def test_list_flavors(self):
        fl = cs.flavors.list()
        cs.assert_called('GET', '/flavors/detail')
        [self.assertTrue(isinstance(f, flavors.Flavor)) for f in fl]

    def test_list_flavors_undetailed(self):
        fl = cs.flavors.list(detailed=False)
        cs.assert_called('GET', '/flavors')
        [self.assertTrue(isinstance(f, flavors.Flavor)) for f in fl]

    def test_get_flavor_details(self):
        f = cs.flavors.get(1)
        cs.assert_called('GET', '/flavors/1')
        self.assertTrue(isinstance(f, flavors.Flavor))
        self.assertEqual(f.ram, 256)
        self.assertEqual(f.disk, 10)

    def test_find(self):
        f = cs.flavors.find(ram=256)
        cs.assert_called('GET', '/flavors/detail')
        self.assertEqual(f.name, '256 MB Server')

        f = cs.flavors.find(disk=20)
        self.assertEqual(f.name, '512 MB Server')

        self.assertRaises(exceptions.NotFound, cs.flavors.find, disk=12345)

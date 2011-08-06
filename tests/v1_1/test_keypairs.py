<<<<<<< HEAD
=======

>>>>>>> keypair api
from novaclient import exceptions
from novaclient.v1_1 import keypairs
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class KeypairsTest(utils.TestCase):

    def test_list_keypairs(self):
        kps = cs.keypairs.list()
        cs.assert_called('GET', '/extras/keypairs')
        [self.assertTrue(isinstance(kp, keypairs.Keypair)) for kp in kps]

    def test_delete_keypair(self):
        kp = cs.keypairs.list()[0]
        kp.delete()
        cs.assert_called('DELETE', '/extras/keypairs/test')
        cs.keypairs.delete('test')
        cs.assert_called('DELETE', '/extras/keypairs/test')
        cs.keypairs.delete(kp)
        cs.assert_called('DELETE', '/extras/keypairs/test')

    def test_create_keypair(self):
        kp = cs.keypairs.create("foo")
        cs.assert_called('POST', '/extras/keypairs')
        self.assertTrue(isinstance(kp, keypairs.Keypair))


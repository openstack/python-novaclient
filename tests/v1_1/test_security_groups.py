from novaclient import exceptions
from novaclient.v1_1 import security_groups
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class SecurityGroupsTest(utils.TestCase):
    def test_list_security_groups(self):
        sgs = cs.security_groups.list()
        cs.assert_called('GET', '/extras/security_groups')
        [self.assertTrue(isinstance(sg, security_groups.SecurityGroup)) for sg in sgs]

    def test_delete_security_group(self):
        sg = cs.security_groups.list()[0]
        sg.delete()
        cs.assert_called('DELETE', '/extras/security_groups/test')
        cs.security_groups.delete('test')
        cs.assert_called('DELETE', '/extras/security_groups/test')
        cs.security_groups.delete(sg)
        cs.assert_called('DELETE', '/extras/security_groups/test')

    def test_create_security_group(self):
        sg = cs.security_groups.create("foo","foo barr")
        cs.assert_called('POST', '/extras/security_groups')
        self.assertTrue(isinstance(sg, security_groups.SecurityGroup))

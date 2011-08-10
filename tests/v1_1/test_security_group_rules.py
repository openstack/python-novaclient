from novaclient import exceptions
from novaclient.v1_1 import security_group_rules
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class SecurityGroupRulesTest(utils.TestCase):
    def test_delete_security_group_rule(self):
        cs.security_group_rules.delete('test')
        cs.assert_called('DELETE', '/extras/security_group_rules/test')

    def test_create_security_group(self):
        sg = cs.security_group_rules.create("foo")
        cs.assert_called('POST', '/extras/security_group_rules')
        self.assertTrue(isinstance(sg, security_group_rules.SecurityGroupRule))

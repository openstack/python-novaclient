from novaclient.v1_1 import security_group_rules
from tests import utils
from tests.v1_1 import fakes


cs = fakes.FakeClient()


class SecurityGroupRulesTest(utils.TestCase):
    def test_delete_security_group_rule(self):
        cs.security_group_rules.delete(1)
        cs.assert_called('DELETE', '/os-security-group-rules/1')

    def test_create_security_group(self):
        sg = cs.security_group_rules.create(1)
        cs.assert_called('POST', '/os-security-group-rules')
        self.assertTrue(isinstance(sg, security_group_rules.SecurityGroupRule))

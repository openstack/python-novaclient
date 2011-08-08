from novaclient import exceptions
from novaclient.v1_1 import quotas
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


class QuoatsTest(utils.TestCase):
    def test_list_quotas(self):
        qs = cs.quotas.list()
        cs.assert_called('GET', '/os-quotas')
        [self.assertTrue(isinstance(q, quotas.QuotaSet)) for q in qs]

    def test_delete_quota(self):
        q = cs.quotas.list()[0]
        q.delete()
        cs.assert_called('DELETE', '/os-quotas/test')
        cs.quotas.delete('test')
        cs.assert_called('DELETE', '/os-quotas/test')
        cs.quotas.delete(q)
        cs.assert_called('DELETE', '/os-quotas/test')

    def test_update_quota(self):
        q = cs.quotas.list()[0]
        q.update(volumes=2)
        cs.assert_called('PUT', '/os-quotas/test')

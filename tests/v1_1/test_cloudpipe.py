from novaclient import exceptions
from novaclient.v1_1 import cloudpipe
from tests import utils
from tests.v1_1 import fakes


cs = fakes.FakeClient()


class CloudpipeTest(utils.TestCase):

    def test_list_cloudpipes(self):
        cp = cs.cloudpipe.list()
        cs.assert_called('GET', '/os-cloudpipe')
        [self.assertTrue(isinstance(c, cloudpipe.Cloudpipe)) for c in cp]

    def test_create(self):
        project = "test"
        cp = cs.cloudpipe.create(project)
        body = {'cloudpipe': {'project_id': project}}
        cs.assert_called('POST', '/os-cloudpipe', body)
        self.assertTrue(isinstance(cp, str))

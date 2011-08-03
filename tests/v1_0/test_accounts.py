
import StringIO

from tests.v1_0 import fakes
from tests import utils


cs = fakes.FakeClient()


class AccountsTest(utils.TestCase):

    def test_instance_creation_for_account(self):
        s = cs.accounts.create_instance_for(
            account_id='test_account',
            name="My server",
            image=1,
            flavor=1,
            meta={'foo': 'bar'},
            ipgroup=1,
            files={
                '/etc/passwd': 'some data',                 # a file
                '/tmp/foo.txt': StringIO.StringIO('data')   # a stream
            })
        cs.assert_called('POST', '/accounts/test_account/create_instance')

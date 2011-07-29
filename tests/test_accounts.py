import StringIO

from nose.tools import assert_equal

from fakeserver import FakeServer
from novaclient import Account

cs = FakeServer()


def test_instance_creation_for_account():
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

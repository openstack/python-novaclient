from __future__ import absolute_import

import StringIO

from .fakes import FakeClient

os = FakeClient()

def test_instance_creation_for_account():
    s = os.accounts.create_instance_for(
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
    os.assert_called('POST', '/accounts/test_account/create_instance')

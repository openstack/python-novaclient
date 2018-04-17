#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
A fake server that "responds" to API methods with pre-canned responses.

All of these responses come from the spec, so if for some reason the spec's
wrong the tests might raise AssertionError. I've indicated in comments the
places where actual behavior differs from the spec.
"""

from novaclient import base

# fake request id
FAKE_REQUEST_ID = 'req-3fdea7c2-e3e3-48b5-a656-6b12504c49a1'
FAKE_REQUEST_ID_LIST = [FAKE_REQUEST_ID]


def assert_has_keys(dict, required=None, optional=None):
    required = required or []
    optional = optional or []
    keys = dict.keys()
    for k in required:
        try:
            assert k in keys
        except AssertionError:
            extra_keys = set(keys).difference(set(required + optional))
            raise AssertionError("found unexpected keys: %s" %
                                 list(extra_keys))


class FakeClient(object):

    def assert_called(self, method, url, body=None, pos=-1):
        """Assert that an HTTP method was called at given order/position.

        :param method: HTTP method name which is expected to be called
        :param url: Expected request url to be called with given method
        :param body: Expected request body to be called with given method
                     and url. Default is None.
        :param pos: Order of the expected method call. If multiple methods
                    calls are made in single API request, then, order of each
                    method call can be checked by passing expected order to
                    this arg.
                    Default is -1 which means most recent call.

        Usage::
            1. self.run_command('flavor-list --extra-specs')
               self.assert_called('GET', '/flavors/aa1/os-extra_specs')

            2. self.run_command(["boot", "--image", "1",
                                 "--flavor", "512 MB Server",
                                 "--max-count", "3", "server"])
               self.assert_called('GET', '/images/1', pos=0)
               self.assert_called('GET', '/flavors/512 MB Server', pos=1)
               self.assert_called('GET', '/flavors?is_public=None', pos=2)
               self.assert_called('GET', '/flavors/2', pos=3)
               self.assert_called(
                   'POST', '/servers',
                    {
                        'server': {
                            'flavorRef': '2',
                            'name': 'server',
                            'imageRef': '1',
                            'min_count': 1,
                            'max_count': 3,
                        }
                    }, pos=4)
        """
        expected = (method, url)

        assert self.client.callstack, \
            "Expected %s %s but no calls were made." % expected

        called = self.client.callstack[pos][0:2]

        assert expected == called, \
            ('\nExpected: %(expected)s'
             '\nActual: %(called)s'
             '\nCall position: %(pos)s'
             '\nCalls:\n%(calls)s' %
             {'expected': expected, 'called': called, 'pos': pos,
              'calls': '\n'.join(str(c) for c in self.client.callstack)})

        if body is not None:
            if self.client.callstack[pos][2] != body:
                raise AssertionError('%r != %r' %
                                     (self.client.callstack[pos][2], body))

    def assert_called_anytime(self, method, url, body=None):
        """Assert that an HTTP method was called anytime in the test.

        :param method: HTTP method name which is expected to be called
        :param url: Expected request url to be called with given method
        :param body: Expected request body to be called with given method
                     and url. Default is None.
        Usage::
            self.run_command('flavor-list --extra-specs')
            self.assert_called_anytime('GET', '/flavors/detail')
        """
        expected = (method, url)

        assert self.client.callstack, \
            "Expected %s %s but no calls were made." % expected

        found = False
        for entry in self.client.callstack:
            if expected == entry[0:2]:
                found = True
                break

        assert found, 'Expected %s; got %s' % (expected, self.client.callstack)
        if body is not None:
            try:
                assert entry[2] == body
            except AssertionError:
                print(entry[2])
                print("!=")
                print(body)
                raise

        self.client.callstack = []

    def assert_not_called(self, method, url, body=None):
        """Assert that an HTTP method was not called in the test.

        :param method: HTTP method name which is expected not to be called
        :param url: Expected request url not to be called with given method
        :param body: Expected request body not to be called with given method
                     and url. Default is None.
        """
        not_expected = (method, url, body)
        for entry in self.client.callstack:
            assert not_expected != entry[0:3], (
                'API %s %s body=%s was called.' % not_expected)

    def clear_callstack(self):
        self.client.callstack = []

    def authenticate(self):
        pass


# Fake class that will be used as an extension
class FakeManager(base.Manager):
    pass

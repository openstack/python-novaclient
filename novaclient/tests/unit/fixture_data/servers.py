# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from novaclient import api_versions
from novaclient.tests.unit import fakes
from novaclient.tests.unit.fixture_data import base
from novaclient.tests.unit.v2 import fakes as v2_fakes


class Base(base.Fixture):

    base_url = 'servers'

    def setUp(self):
        super(Base, self).setUp()

        get_servers = {
            "servers": [
                {'id': 1234, 'name': 'sample-server'},
                {'id': 5678, 'name': 'sample-server2'}
            ]
        }

        self.requests_mock.get(self.url(),
                               json=get_servers,
                               headers=self.json_headers)

        self.server_1234 = {
            "id": 1234,
            "name": "sample-server",
            "image": {
                "id": 2,
                "name": "sample image",
            },
            "flavor": {
                "id": 1,
                "name": "256 MiB Server",
            },
            "hostId": "e4d909c290d0fb1ca068ffaddf22cbd0",
            "status": "BUILD",
            "progress": 60,
            "addresses": {
                "public": [
                    {
                        "version": 4,
                        "addr": "1.2.3.4",
                    },
                    {
                        "version": 4,
                        "addr": "5.6.7.8",
                    }],
                "private": [{
                    "version": 4,
                    "addr": "10.11.12.13",
                }],
            },
            "metadata": {
                "Server Label": "Web Head 1",
                "Image Version": "2.1"
            },
            "OS-EXT-SRV-ATTR:host": "computenode1",
            "security_groups": [{
                'id': 1, 'name': 'securitygroup1',
                'description': 'FAKE_SECURITY_GROUP',
                'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
            }],
            "OS-EXT-MOD:some_thing": "mod_some_thing_value",
        }

        self.server_5678 = {
            "id": 5678,
            "name": "sample-server2",
            "image": {
                "id": 2,
                "name": "sample image",
            },
            "flavor": {
                "id": 1,
                "name": "256 MiB Server",
            },
            "hostId": "9e107d9d372bb6826bd81d3542a419d6",
            "status": "ACTIVE",
            "addresses": {
                "public": [
                    {
                        "version": 4,
                        "addr": "4.5.6.7",
                    },
                    {
                        "version": 4,
                        "addr": "5.6.9.8",
                    }],
                "private": [{
                    "version": 4,
                    "addr": "10.13.12.13",
                }],
            },
            "metadata": {
                "Server Label": "DB 1"
            },
            "OS-EXT-SRV-ATTR:host": "computenode2",
            "security_groups": [
                {
                    'id': 1, 'name': 'securitygroup1',
                    'description': 'FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                },
                {
                    'id': 2, 'name': 'securitygroup2',
                    'description': 'ANOTHER_FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                }],
        }

        self.server_9012 = {
            "id": 9012,
            "name": "sample-server3",
            "image": "",
            "flavor": {
                "id": 1,
                "name": "256 MiB Server",
            },
            "hostId": "9e107d9d372bb6826bd81d3542a419d6",
            "status": "ACTIVE",
            "addresses": {
                "public": [
                    {
                        "version": 4,
                        "addr": "4.5.6.7",
                    },
                    {
                        "version": 4,
                        "addr": "5.6.9.8",
                    }],
                "private": [{
                    "version": 4,
                    "addr": "10.13.12.13",
                }],
            },
            "metadata": {
                "Server Label": "DB 1"
            }
        }

        servers = [self.server_1234, self.server_5678, self.server_9012]
        get_servers_detail = {"servers": servers}

        self.requests_mock.get(self.url('detail'),
                               json=get_servers_detail,
                               headers=self.json_headers)

        self.requests_mock.get(
            self.url('detail', marker=self.server_1234["id"]),
            json={"servers": [self.server_1234, self.server_5678]},
            headers=self.json_headers, complete_qs=True)

        self.requests_mock.get(
            self.url('detail', marker=self.server_5678["id"]),
            json={"servers": []},
            headers=self.json_headers, complete_qs=True)

        self.server_1235 = self.server_1234.copy()
        self.server_1235['id'] = 1235
        self.server_1235['status'] = 'error'
        self.server_1235['fault'] = {'message': 'something went wrong!'}

        for s in servers + [self.server_1235]:
            self.requests_mock.get(self.url(s['id']),
                                   json={'server': s},
                                   headers=self.json_headers)

        for s in (1234, 5678):
            self.requests_mock.delete(self.url(s),
                                      status_code=202,
                                      headers=self.json_headers)

        for k in ('test_key', 'key1', 'key2'):
            self.requests_mock.delete(self.url(1234, 'metadata', k),
                                      status_code=204,
                                      headers=self.json_headers)

        metadata1 = {'metadata': {'test_key': 'test_value'}}
        self.requests_mock.post(self.url(1234, 'metadata'),
                                json=metadata1,
                                headers=self.json_headers)
        self.requests_mock.put(self.url(1234, 'metadata', 'test_key'),
                               json=metadata1,
                               headers=self.json_headers)

        self.diagnostic = {'data': 'Fake diagnostics'}

        metadata2 = {'metadata': {'key1': 'val1'}}
        for u in ('uuid1', 'uuid2', 'uuid3', 'uuid4'):
            self.requests_mock.post(self.url(u, 'metadata'),
                                    json=metadata2, status_code=204)
            self.requests_mock.delete(self.url(u, 'metadata', 'key1'),
                                      json=self.diagnostic,
                                      headers=self.json_headers)

        get_security_groups = {
            "security_groups": [{
                'id': 1,
                'name': 'securitygroup1',
                'description': 'FAKE_SECURITY_GROUP',
                'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7',
                'rules': []}]
        }

        self.requests_mock.get(self.url('1234', 'os-security-groups'),
                               json=get_security_groups,
                               headers=self.json_headers)

        self.requests_mock.post(self.url(),
                                json=self.post_servers,
                                headers=self.json_headers)

        self.requests_mock.post(self.url('1234', 'remote-consoles'),
                                json=self.post_servers_1234_remote_consoles,
                                headers=self.json_headers)

        self.requests_mock.post(self.url('1234', 'action'),
                                json=self.post_servers_1234_action,
                                headers=self.json_headers)

        get_os_interface = {
            "interfaceAttachments": [
                {
                    "port_state": "ACTIVE",
                    "net_id": "net-id-1",
                    "port_id": "port-id-1",
                    "mac_address": "aa:bb:cc:dd:ee:ff",
                    "fixed_ips": [{"ip_address": "1.2.3.4"}],
                },
                {
                    "port_state": "ACTIVE",
                    "net_id": "net-id-1",
                    "port_id": "port-id-1",
                    "mac_address": "aa:bb:cc:dd:ee:ff",
                    "fixed_ips": [{"ip_address": "1.2.3.4"}],
                }
            ]
        }

        self.requests_mock.get(self.url('1234', 'os-interface'),
                               json=get_os_interface,
                               headers=self.json_headers)

        interface_data = {'interfaceAttachment': {}}
        self.requests_mock.post(self.url('1234', 'os-interface'),
                                json=interface_data,
                                headers=self.json_headers)

        def put_servers_1234(request, context):
            body = request.json()
            assert list(body) == ['server']
            fakes.assert_has_keys(body['server'],
                                  optional=['name', 'adminPass'])
            return request.body

        self.requests_mock.put(self.url(1234),
                               text=put_servers_1234,
                               status_code=204,
                               headers=self.json_headers)

        #
        # Server password
        #

        self.requests_mock.delete(self.url(1234, 'os-server-password'),
                                  status_code=202,
                                  headers=self.json_headers)
        #
        # Server tags
        #

        self.requests_mock.get(self.url(1234, 'tags'),
                               json={'tags': ['tag1', 'tag2']},
                               headers=self.json_headers)

        self.requests_mock.get(self.url(1234, 'tags', 'tag'),
                               status_code=204,
                               headers=self.json_headers)

        self.requests_mock.delete(self.url(1234, 'tags', 'tag'),
                                  status_code=204,
                                  headers=self.json_headers)

        self.requests_mock.delete(self.url(1234, 'tags'),
                                  status_code=204,
                                  headers=self.json_headers)

        def put_server_tag(request, context):
            assert request.text is None
            context.status_code = 201
            return None

        self.requests_mock.put(self.url(1234, 'tags', 'tag'),
                               json=put_server_tag,
                               headers=self.json_headers)

        def put_server_tags(request, context):
            body = request.json()
            assert list(body) == ['tags']
            return body

        self.requests_mock.put(self.url(1234, 'tags'),
                               json=put_server_tags,
                               headers=self.json_headers)


class V1(Base):

    def setUp(self):
        super(V1, self).setUp()

        #
        # Server Addresses
        #

        add = self.server_1234['addresses']
        self.requests_mock.get(self.url(1234, 'ips'),
                               json={'addresses': add},
                               headers=self.json_headers)

        self.requests_mock.get(self.url(1234, 'ips', 'public'),
                               json={'public': add['public']},
                               headers=self.json_headers)

        self.requests_mock.get(self.url(1234, 'ips', 'private'),
                               json={'private': add['private']},
                               headers=self.json_headers)

        self.requests_mock.delete(self.url(1234, 'ips', 'public', '1.2.3.4'),
                                  status_code=202)

        self.requests_mock.get(self.url('1234', 'diagnostics'),
                               json=self.diagnostic,
                               headers=self.json_headers)

        self.requests_mock.delete(self.url('1234', 'os-interface', 'port-id'),
                                  headers=self.json_headers)

        self.requests_mock.get(self.url('1234', 'topology'),
                               json=v2_fakes.SERVER_TOPOLOGY,
                               headers=self.json_headers)

        # Testing with the following password and key
        #
        # Clear password: FooBar123
        #
        # RSA Private Key: novaclient/tests/unit/idfake.pem
        #
        # Encrypted password
        # OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r
        # qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho
        # QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw
        # /y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N
        # tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk
        # Hi/fmZZNQQqj1Ijq0caOIw==

        get_server_password = {
            'password':
            'OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r'
            'qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho'
            'QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw'
            '/y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N'
            'tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk'
            'Hi/fmZZNQQqj1Ijq0caOIw=='}
        self.requests_mock.get(self.url(1234, 'os-server-password'),
                               json=get_server_password,
                               headers=self.json_headers)

    def post_servers(self, request, context):
        body = request.json()
        context.status_code = 202
        assert (set(body.keys()) <=
                set(['server', 'os:scheduler_hints']))
        fakes.assert_has_keys(body['server'],
                              required=['name', 'imageRef', 'flavorRef'],
                              optional=['metadata', 'personality'])
        if 'personality' in body['server']:
            for pfile in body['server']['personality']:
                fakes.assert_has_keys(pfile, required=['path', 'contents'])
        if ('return_reservation_id' in body['server'].keys() and
                body['server']['return_reservation_id']):
            return {'reservation_id': 'r-3fhpjulh'}
        if body['server']['name'] == 'some-bad-server':
            body = self.server_1235
        else:
            body = self.server_1234

        return {'server': body}

    def post_servers_1234_remote_consoles(self, request, context):
        _body = ''
        body = request.json()
        context.status_code = 202
        assert len(body.keys()) == 1
        assert 'remote_console' in body.keys()
        assert 'protocol' in body['remote_console'].keys()
        protocol = body['remote_console']['protocol']

        _body = {'protocol': protocol, 'type': 'novnc',
                 'url': 'http://example.com:6080/vnc_auto.html?token=XYZ'}

        return {'remote_console': _body}

    def post_servers_1234_action(self, request, context):
        _body = ''
        body = request.json()
        context.status_code = 202
        assert len(body.keys()) == 1
        action = list(body)[0]
        api_version = api_versions.APIVersion(
            request.headers.get('X-OpenStack-Nova-API-Version', '2.1'))

        if v2_fakes.FakeSessionClient.check_server_actions(body):
            # NOTE(snikitin): No need to do any operations here. This 'pass'
            # is needed to avoid AssertionError in the last 'else' statement
            # if we found 'action' in method check_server_actions and
            # raise AssertionError if we didn't find 'action' at all.
            pass
        elif action == 'os-migrateLive':
            # Fixme(eliqiao): body of os-migrateLive changes from v2.25
            # but we can not specify version in data_fixture now and this is
            # V1 data, so just let it pass
            pass
        elif action == 'migrate':
            return None
        elif action == 'lock':
            return None
        elif action == 'unshelve':
            if api_version >= api_versions.APIVersion("2.91"):
                # In 2.91 and above, we allow body to be one of these:
                # {'unshelve': None}
                # {'unshelve': {'availability_zone': <string>}}
                # {'unshelve': {'availability_zone': None}}   (Unpin az)
                # {'unshelve': {'host': <fqdn>}}
                # {'unshelve': {'availability_zone': <string>, 'host': <fqdn>}}
                # {'unshelve': {'availability_zone': None, 'host': <fqdn>}}
                if body[action] is not None:
                    for key in body[action].keys():
                        key in ['availability_zone', 'host']
            return None
        elif action == 'rebuild':
            body = body[action]
            adminPass = body.get('adminPass', 'randompassword')
            assert 'imageRef' in body
            _body = self.server_1234.copy()
            _body['adminPass'] = adminPass
        elif action == 'confirmResize':
            assert body[action] is None
            # This one method returns a different response code
            context.status_code = 204
            return None
        elif action == 'rescue':
            if body[action]:
                keys = set(body[action].keys())
                assert not (keys - set(['adminPass', 'rescue_image_ref']))
            else:
                assert body[action] is None
            _body = {'adminPass': 'RescuePassword'}
        elif action == 'createImage':
            assert set(body[action].keys()) == set(['name', 'metadata'])
            if api_version >= api_versions.APIVersion('2.45'):
                return {'image_id': '456'}
            context.headers['location'] = "http://blah/images/456"
        elif action == 'createBackup':
            assert set(body[action].keys()) == set(['name', 'backup_type',
                                                    'rotation'])
            if api_version >= api_versions.APIVersion('2.45'):
                return {'image_id': '456'}
            context.headers['location'] = "http://blah/images/456"
        elif action == 'os-getConsoleOutput':
            assert list(body[action]) == ['length']
            context.status_code = 202
            return {'output': 'foo'}
        elif action == 'os-getSerialConsole':
            assert list(body[action]) == ['type']
        elif action == 'evacuate':
            keys = list(body[action])
            if 'adminPass' in keys:
                keys.remove('adminPass')
            assert 'host' in keys
        else:
            raise AssertionError("Unexpected server action: %s" % action)
        return {'server': _body}

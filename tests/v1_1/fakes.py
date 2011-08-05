import httplib2
import urllib
import urlparse

from novaclient import client as base_client
from novaclient.v1_1 import client
from tests import fakes


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'apikey',
                               'project_id', 'auth_url')
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(base_client.HTTPClient):

    def __init__(self, **kwargs):
        self.username = 'username'
        self.apikey = 'apikey'
        self.auth_url = 'auth_url'
        self.callstack = []

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method in ['PUT', 'POST']:
            assert 'body' in kwargs

        # Call the method
        munged_url = url.strip('/').replace('/', '_').replace('.', '_')
        callback = "%s_%s" % (method.lower(), munged_url)
        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s' % (method, url))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body', None)))

        status, body = getattr(self, callback)(**kwargs)
        return httplib2.Response({"status": status}), body

    def _munge_get_url(self, url):
        return url

    #
    # Limits
    #

    def get_limits(self, **kw):
        return (200, {"limits": {
            "rate": [
                {
                    "verb": "POST",
                    "URI": "*",
                    "regex": ".*",
                    "value": 10,
                    "remaining": 2,
                    "unit": "MINUTE",
                    "resetTime": 1244425439
                },
                {
                    "verb": "POST",
                    "URI": "*/servers",
                    "regex": "^/servers",
                    "value": 50,
                    "remaining": 49,
                    "unit": "DAY", "resetTime": 1244511839
                },
                {
                    "verb": "PUT",
                    "URI": "*",
                    "regex": ".*",
                    "value": 10,
                    "remaining": 2,
                    "unit": "MINUTE",
                    "resetTime": 1244425439
                },
                {
                    "verb": "GET",
                    "URI": "*changes-since*",
                    "regex": "changes-since",
                    "value": 3,
                    "remaining": 3,
                    "unit": "MINUTE",
                    "resetTime": 1244425439
                },
                {
                    "verb": "DELETE",
                    "URI": "*",
                    "regex": ".*",
                    "value": 100,
                    "remaining": 100,
                    "unit": "MINUTE",
                    "resetTime": 1244425439
                }
            ],
            "absolute": {
                "maxTotalRAMSize": 51200,
                "maxIPGroups": 50,
                "maxIPGroupMembers": 25
            }
        }})

    #
    # Servers
    #

    def get_servers(self, **kw):
        return (200, {"servers": [
            {'id': 1234, 'name': 'sample-server'},
            {'id': 5678, 'name': 'sample-server2'}
        ]})

    def get_servers_detail(self, **kw):
        return (200, {"servers": [
            {
                "id": 1234,
                "name": "sample-server",
                "image": {
                    "id": 2,
                    "name": "sample image",
                },
                "flavor": {
                    "id": 1,
                    "name": "256 MB Server",
                },
                "hostId": "e4d909c290d0fb1ca068ffaddf22cbd0",
                "status": "BUILD",
                "progress": 60,
                "addresses": {
                    "public": [{
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
                }
            },
            {
                "id": 5678,
                "name": "sample-server2",
                "image": {
                    "id": 2,
                    "name": "sample image",
                },
                "flavor": {
                    "id": 1,
                    "name": "256 MB Server",
                },
                "hostId": "9e107d9d372bb6826bd81d3542a419d6",
                "status": "ACTIVE",
                "addresses": {
                    "public": [{
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
        ]})

    def post_servers(self, body, **kw):
        assert body.keys() == ['server']
        fakes.assert_has_keys(body['server'],
                        required=['name', 'imageRef', 'flavorRef'],
                        optional=['metadata', 'personality'])
        if 'personality' in body['server']:
            for pfile in body['server']['personality']:
                fakes.assert_has_keys(pfile, required=['path', 'contents'])
        return (202, self.get_servers_1234()[1])

    def get_servers_1234(self, **kw):
        r = {'server': self.get_servers_detail()[1]['servers'][0]}
        return (200, r)

    def get_servers_5678(self, **kw):
        r = {'server': self.get_servers_detail()[1]['servers'][1]}
        return (200, r)

    def put_servers_1234(self, body, **kw):
        assert body.keys() == ['server']
        fakes.assert_has_keys(body['server'], optional=['name', 'adminPass'])
        return (204, None)

    def delete_servers_1234(self, **kw):
        return (202, None)

    #
    # Server Addresses
    #

    def get_servers_1234_ips(self, **kw):
        return (200, {'addresses':
                      self.get_servers_1234()[1]['server']['addresses']})

    def get_servers_1234_ips_public(self, **kw):
        return (200, {'public':
                      self.get_servers_1234_ips()[1]['addresses']['public']})

    def get_servers_1234_ips_private(self, **kw):
        return (200, {'private':
                      self.get_servers_1234_ips()[1]['addresses']['private']})

    def delete_servers_1234_ips_public_1_2_3_4(self, **kw):
        return (202, None)

    #
    # Server actions
    #

    def post_servers_1234_action(self, body, **kw):
        assert len(body.keys()) == 1
        action = body.keys()[0]
        if action == 'reboot':
            assert body[action].keys() == ['type']
            assert body[action]['type'] in ['HARD', 'SOFT']
        elif action == 'rebuild':
            assert body[action].keys() == ['imageRef']
        elif action == 'resize':
            assert body[action].keys() == ['flavorRef']
        elif action == 'confirmResize':
            assert body[action] is None
            # This one method returns a different response code
            return (204, None)
        elif action == 'revertResize':
            assert body[action] is None
        elif action == 'migrate':
            assert body[action] is None
        elif action == 'addFixedIp':
            assert body[action].keys() == ['networkId']
        elif action == 'removeFixedIp':
            assert body[action].keys() == ['address']
        elif action == 'createImage':
            assert set(body[action].keys()) == set(['name', 'metadata'])
        elif action == 'changePassword':
            assert body[action].keys() == ['adminPass']
        else:
            raise AssertionError("Unexpected server action: %s" % action)
        return (202, None)

    #
    # Flavors
    #

    def get_flavors(self, **kw):
        return (200, {'flavors': [
            {'id': 1, 'name': '256 MB Server'},
            {'id': 2, 'name': '512 MB Server'}
        ]})

    def get_flavors_detail(self, **kw):
        return (200, {'flavors': [
            {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10},
            {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20}
        ]})

    def get_flavors_1(self, **kw):
        return (200, {'flavor': self.get_flavors_detail()[1]['flavors'][0]})

    def get_flavors_2(self, **kw):
        return (200, {'flavor': self.get_flavors_detail()[1]['flavors'][1]})

    #
    # Images
    #
    def get_images(self, **kw):
        return (200, {'images': [
            {'id': 1, 'name': 'CentOS 5.2'},
            {'id': 2, 'name': 'My Server Backup'}
        ]})

    def get_images_detail(self, **kw):
        return (200, {'images': [
            {
                'id': 1,
                'name': 'CentOS 5.2',
                "updated": "2010-10-10T12:00:00Z",
                "created": "2010-08-10T12:00:00Z",
                "status": "ACTIVE"
            },
            {
                "id": 743,
                "name": "My Server Backup",
                "serverId": 12,
                "updated": "2010-10-10T12:00:00Z",
                "created": "2010-08-10T12:00:00Z",
                "status": "SAVING",
                "progress": 80
            }
        ]})

    def get_images_1(self, **kw):
        return (200, {'image': self.get_images_detail()[1]['images'][0]})

    def get_images_2(self, **kw):
        return (200, {'image': self.get_images_detail()[1]['images'][1]})

    def post_images(self, body, **kw):
        assert body.keys() == ['image']
        fakes.assert_has_keys(body['image'], required=['serverId', 'name'])
        return (202, self.get_images_1()[1])

    def delete_images_1(self, **kw):
        return (204, None)

    #
    # Zones
    #
    def get_zones(self, **kw):
        return (200, {'zones': [
            {'id': 1, 'api_url': 'http://foo.com', 'username': 'bob'},
            {'id': 2, 'api_url': 'http://foo.com', 'username': 'alice'},
        ]})

    def get_zones_detail(self, **kw):
        return (200, {'zones': [
            {'id': 1, 'api_url': 'http://foo.com', 'username': 'bob',
                                                   'password': 'qwerty'},
            {'id': 2, 'api_url': 'http://foo.com', 'username': 'alice',
                                                   'password': 'password'}
        ]})

    def get_zones_1(self, **kw):
        r = {'zone': self.get_zones_detail()[1]['zones'][0]}
        return (200, r)

    def get_zones_2(self, **kw):
        r = {'zone': self.get_zones_detail()[1]['zones'][1]}
        return (200, r)

    def post_zones(self, body, **kw):
        assert body.keys() == ['zone']
        fakes.assert_has_keys(body['zone'],
                        required=['api_url', 'username', 'password'],
                        optional=['weight_offset', 'weight_scale'])

        return (202, self.get_zones_1()[1])

    def put_zones_1(self, body, **kw):
        assert body.keys() == ['zone']
        fakes.assert_has_keys(body['zone'], optional=['api_url', 'username',
                                                'password',
                                                'weight_offset',
                                                'weight_scale'])
        return (204, None)

    def delete_zones_1(self, **kw):
        return (202, None)



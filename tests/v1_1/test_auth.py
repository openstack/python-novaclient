import httplib2
import json
import mock
import urlparse


from novaclient.v1_1 import client
from novaclient import exceptions
from tests import utils


class AuthenticateAgainstKeystoneTests(utils.TestCase):
    def test_authenticate_success(self):
        cs = client.Client("username", "apikey", "project_id", "auth_url/v2.0")
        resp = {"auth": {"token": {"expires": "12345", "id": "FAKE_ID"}, 
                         "serviceCatalog": {
                            "nova": [{"adminURL": "http://localhost:8774/v1.1",
                                      "region": "RegionOne",
                                      "internalURL": "http://localhost:8774/v1.1",
                                      "publicURL": "http://localhost:8774/v1.1/"}]}}}
        auth_response = httplib2.Response({
            "status": 204, 
            "body": json.dumps(resp),
            })

        mock_request = mock.Mock(return_value=(auth_response, json.dumps(resp)))

        @mock.patch.object(httplib2.Http, "request", mock_request)
        def test_auth_call():
            cs.client.authenticate()
            headers = {'User-Agent': cs.client.USER_AGENT,
                       'Content-Type': 'application/json',}
            body = {'passwordCredentials': {'username': cs.client.user,
                                            'password': cs.client.apikey,
                                            'tenantId': cs.client.projectid,}}

            token_url = urlparse.urljoin(cs.client.auth_url, "tokens")
            mock_request.assert_called_with(token_url, "POST",
                                            headers=headers,
                                            body=json.dumps(body))

            self.assertEqual(cs.client.management_url,
                            resp["auth"]["serviceCatalog"]["nova"][0]["publicURL"])
            self.assertEqual(cs.client.auth_token, resp["auth"]["token"]["id"])

        test_auth_call()


    def test_authenticate_failure(self):
        cs = client.Client("username", "apikey", "project_id", "auth_url/v2.0")
        resp = {"unauthorized": {"message": "Unauthorized", "code": "401"}}
        auth_response = httplib2.Response({
            "status": 401,
            "body": json.dumps(resp),
            })

        mock_request = mock.Mock(return_value=(auth_response, json.dumps(resp)))

        @mock.patch.object(httplib2.Http, "request", mock_request)
        def test_auth_call():
            self.assertRaises(exceptions.Unauthorized, cs.client.authenticate)

        test_auth_call()


class AuthenticationTests(utils.TestCase):
    def test_authenticate_success(self):
        cs = client.Client("username", "apikey", "project_id", "auth_url")
        management_url = 'https://servers.api.rackspacecloud.com/v1.1/443470'
        auth_response = httplib2.Response({
            'status': 204,
            'x-server-management-url': management_url,
            'x-auth-token': '1b751d74-de0c-46ae-84f0-915744b582d1',
        })
        mock_request = mock.Mock(return_value=(auth_response, None))

        @mock.patch.object(httplib2.Http, "request", mock_request)
        def test_auth_call():
            cs.client.authenticate()
            headers={
                'X-Auth-User': 'username',
                'X-Auth-Key': 'apikey',
                'X-Auth-Project-Id': 'project_id',
                'User-Agent': cs.client.USER_AGENT
            }
            mock_request.assert_called_with(cs.client.auth_url, 'GET',
                                            headers=headers)
            self.assertEqual(cs.client.management_url,
                             auth_response['x-server-management-url'])
            self.assertEqual(cs.client.auth_token,
                             auth_response['x-auth-token'])

        test_auth_call()

    def test_authenticate_failure(self):
        cs = client.Client("username", "apikey", "project_id", "auth_url")
        auth_response = httplib2.Response({'status': 401})
        mock_request = mock.Mock(return_value=(auth_response, None))

        @mock.patch.object(httplib2.Http, "request", mock_request)
        def test_auth_call():
            self.assertRaises(exceptions.Unauthorized, cs.client.authenticate)

        test_auth_call()

    def test_auth_automatic(self):
        cs = client.Client("username", "apikey", "project_id", "auth_url")
        http_client = cs.client
        http_client.management_url = ''
        mock_request = mock.Mock(return_value=(None, None))

        @mock.patch.object(http_client, 'request', mock_request)
        @mock.patch.object(http_client, 'authenticate')
        def test_auth_call(m):
            http_client.get('/')
            m.assert_called()
            mock_request.assert_called()

        test_auth_call()

    def test_auth_manual(self):
        cs = client.Client("username", "apikey", "project_id", "auth_url")

        @mock.patch.object(cs.client, 'authenticate')
        def test_auth_call(m):
            cs.authenticate()
            m.assert_called()

        test_auth_call()

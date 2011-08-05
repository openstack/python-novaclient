
import httplib2
import mock

from novaclient.v1_0 import client
from novaclient import exceptions
from tests import utils


class AuthenticationTests(utils.TestCase):

    def test_authenticate_success(self):
        cs = client.Client("username", "apikey", "project_id")
        management_url = 'https://servers.api.rackspacecloud.com/v1.0/443470'
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
        cs = client.Client("username", "apikey", "project_id")
        auth_response = httplib2.Response({'status': 401})
        mock_request = mock.Mock(return_value=(auth_response, None))

        @mock.patch.object(httplib2.Http, "request", mock_request)
        def test_auth_call():
            self.assertRaises(exceptions.Unauthorized, cs.client.authenticate)

        test_auth_call()

    def test_auth_automatic(self):
        cs = client.Client("username", "apikey", "project_id")
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
        cs = client.Client("username", "apikey", "project_id")

        @mock.patch.object(cs.client, 'authenticate')
        def test_auth_call(m):
            cs.authenticate()
            m.assert_called()

        test_auth_call()

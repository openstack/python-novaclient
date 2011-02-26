import mock
import novaclient
import httplib2
from nose.tools import assert_raises, assert_equal


def test_authenticate_success():
    cs = novaclient.OpenStack("username", "apikey")
    auth_response = httplib2.Response({
        'status': 204,
        'x-server-management-url':
                    'https://servers.api.rackspacecloud.com/v1.0/443470',
        'x-auth-token': '1b751d74-de0c-46ae-84f0-915744b582d1',
    })
    mock_request = mock.Mock(return_value=(auth_response, None))

    @mock.patch.object(httplib2.Http, "request", mock_request)
    def test_auth_call():
        cs.client.authenticate()
        mock_request.assert_called_with(cs.client.auth_url, 'GET',
            headers={
                'X-Auth-User': 'username',
                'X-Auth-Key': 'apikey',
                'User-Agent': cs.client.USER_AGENT
            })
        assert_equal(cs.client.management_url,
                     auth_response['x-server-management-url'])
        assert_equal(cs.client.auth_token, auth_response['x-auth-token'])

    test_auth_call()


def test_authenticate_failure():
    cs = novaclient.OpenStack("username", "apikey")
    auth_response = httplib2.Response({'status': 401})
    mock_request = mock.Mock(return_value=(auth_response, None))

    @mock.patch.object(httplib2.Http, "request", mock_request)
    def test_auth_call():
        assert_raises(novaclient.Unauthorized, cs.client.authenticate)

    test_auth_call()


def test_auth_automatic():
    client = novaclient.OpenStack("username", "apikey").client
    client.management_url = ''
    mock_request = mock.Mock(return_value=(None, None))

    @mock.patch.object(client, 'request', mock_request)
    @mock.patch.object(client, 'authenticate')
    def test_auth_call(m):
        client.get('/')
        m.assert_called()
        mock_request.assert_called()

    test_auth_call()


def test_auth_manual():
    cs = novaclient.OpenStack("username", "apikey")

    @mock.patch.object(cs.client, 'authenticate')
    def test_auth_call(m):
        cs.authenticate()
        m.assert_called()

    test_auth_call()

import httplib2
import mock

from novaclient import client
from novaclient import exceptions
from tests import utils


fake_response = httplib2.Response({"status": 200})
fake_body = '{"hi": "there"}'
mock_request = mock.Mock(return_value=(fake_response, fake_body))


def get_client():
    cl = client.HTTPClient("username", "password",
                           "project_id", "auth_test")
    return cl


def get_authed_client():
    cl = get_client()
    cl.management_url = "http://example.com"
    cl.auth_token = "token"
    return cl


class ClientTest(utils.TestCase):

    def test_get(self):
        cl = get_authed_client()

        @mock.patch.object(httplib2.Http, "request", mock_request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")
            headers = {"X-Auth-Token": "token",
                       "X-Auth-Project-Id": "project_id",
                       "User-Agent": cl.USER_AGENT,
                       'Accept': 'application/json',
            }
            mock_request.assert_called_with("http://example.com/hi",
                                            "GET", headers=headers)
            # Automatic JSON parsing
            self.assertEqual(body, {"hi": "there"})

        test_get_call()

    def test_post(self):
        cl = get_authed_client()

        @mock.patch.object(httplib2.Http, "request", mock_request)
        def test_post_call():
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "X-Auth-Project-Id": "project_id",
                "Content-Type": "application/json",
                'Accept': 'application/json',
                "User-Agent": cl.USER_AGENT
            }
            mock_request.assert_called_with("http://example.com/hi", "POST",
                                            headers=headers, body='[1, 2, 3]')

        test_post_call()

    def test_auth_failure(self):
        cl = get_client()

        # response must not have x-server-management-url header
        @mock.patch.object(httplib2.Http, "request", mock_request)
        def test_auth_call():
            self.assertRaises(exceptions.AuthorizationFailure, cl.authenticate)

        test_auth_call()

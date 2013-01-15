
import novaclient.client
import novaclient.v1_1.client
from tests import utils


class ClientTest(utils.TestCase):

    def test_get_client_class_v2(self):
        output = novaclient.client.get_client_class('2')
        self.assertEqual(output, novaclient.v1_1.client.Client)

    def test_get_client_class_v2_int(self):
        output = novaclient.client.get_client_class(2)
        self.assertEqual(output, novaclient.v1_1.client.Client)

    def test_get_client_class_v1_1(self):
        output = novaclient.client.get_client_class('1.1')
        self.assertEqual(output, novaclient.v1_1.client.Client)

    def test_get_client_class_unknown(self):
        self.assertRaises(novaclient.exceptions.UnsupportedVersion,
                          novaclient.client.get_client_class, '0')

    def test_client_with_os_cache_enabled(self):
        cs = novaclient.v1_1.client.Client("user", "password", "project_id",
                                           auth_url="foo/v2", os_cache=True)
        self.assertEqual(True, cs.os_cache)
        self.assertEqual(True, cs.client.os_cache)

    def test_client_with_os_cache_disabled(self):
        cs = novaclient.v1_1.client.Client("user", "password", "project_id",
                                           auth_url="foo/v2", os_cache=False)
        self.assertEqual(False, cs.os_cache)
        self.assertEqual(False, cs.client.os_cache)

    def test_client_with_no_cache_enabled(self):
        cs = novaclient.v1_1.client.Client("user", "password", "project_id",
                                           auth_url="foo/v2", no_cache=True)
        self.assertEqual(False, cs.os_cache)
        self.assertEqual(False, cs.client.os_cache)

    def test_client_with_no_cache_disabled(self):
        cs = novaclient.v1_1.client.Client("user", "password", "project_id",
                                           auth_url="foo/v2", no_cache=False)
        self.assertEqual(True, cs.os_cache)
        self.assertEqual(True, cs.client.os_cache)

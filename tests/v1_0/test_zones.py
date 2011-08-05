
import StringIO

from novaclient.v1_0 import zones
from tests.v1_0 import fakes
from tests import utils


os = fakes.FakeClient()


class ZonesTest(utils.TestCase):

    def test_list_zones(self):
        sl = os.zones.list()
        os.assert_called('GET', '/zones/detail')
        [self.assertTrue(isinstance(s, zones.Zone)) for s in sl]

    def test_list_zones_undetailed(self):
        sl = os.zones.list(detailed=False)
        os.assert_called('GET', '/zones')
        [self.assertTrue(isinstance(s, zones.Zone)) for s in sl]

    def test_get_zone_details(self):
        s = os.zones.get(1)
        os.assert_called('GET', '/zones/1')
        self.assertTrue(isinstance(s, zones.Zone))
        self.assertEqual(s.id, 1)
        self.assertEqual(s.api_url, 'http://foo.com')

    def test_create_zone(self):
        s = os.zones.create(api_url="http://foo.com", username='bob',
                            password='xxx')
        os.assert_called('POST', '/zones')
        self.assertTrue(isinstance(s, zones.Zone))

    def test_update_zone(self):
        s = os.zones.get(1)

        # Update via instance
        s.update(api_url='http://blah.com')
        os.assert_called('PUT', '/zones/1')
        s.update(api_url='http://blah.com', username='alice', password='xxx')
        os.assert_called('PUT', '/zones/1')

        # Silly, but not an error
        s.update()

        # Update via manager
        os.zones.update(s, api_url='http://blah.com')
        os.assert_called('PUT', '/zones/1')
        os.zones.update(1, api_url='http://blah.com')
        os.assert_called('PUT', '/zones/1')
        os.zones.update(s, api_url='http://blah.com', username='fred',
                           password='zip')
        os.assert_called('PUT', '/zones/1')

    def test_delete_zone(self):
        s = os.zones.get(1)
        s.delete()
        os.assert_called('DELETE', '/zones/1')
        os.zones.delete(1)
        os.assert_called('DELETE', '/zones/1')
        os.zones.delete(s)
        os.assert_called('DELETE', '/zones/1')

    def test_find_zone(self):
        s = os.zones.find(password='qwerty')
        os.assert_called('GET', '/zones/detail')
        self.assertEqual(s.username, 'bob')

        # Find with multiple results returns the first item
        s = os.zones.find(api_url='http://foo.com')
        sl = os.zones.findall(api_url='http://foo.com')
        self.assertEqual(sl[0], s)
        self.assertEqual([s.id for s in sl], [1, 2])

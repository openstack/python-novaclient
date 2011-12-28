from novaclient import exceptions
from novaclient.v1_1 import floating_ip_dns
from tests.v1_1 import fakes
from tests import utils


cs = fakes.FakeClient()


def _quote_zone(zone):
    """
    Zone names tend to have .'s in them.  Urllib doesn't quote dots,
    but Routes tends to choke on them, so we need an extra level of
    by-hand quoting here.  This function needs to duplicate the one in
    python-novaclient/novaclient/v1_1/floating_ip_dns.py
    """
    return urllib.quote(zone.replace('.', '%2E'))


class FloatingIPDNSTest(utils.TestCase):

    testname = "somehostname"
    testip = "1.2.3.4"
    testzone = "zone1"
    testtype = "A"

    def test_dns_zones(self):
        zonelist = cs.floating_ip_dns.zones()
        self.assertEqual(len(zonelist), 2)

        for entry in zonelist:
            self.assertTrue(isinstance(entry, floating_ip_dns.FloatingIPDNS))

        self.assertEqual(zonelist[1].zone, 'example.com')

    def test_get_dns_entries_by_ip(self):
        entries = cs.floating_ip_dns.get_entries(self.testzone, ip=self.testip)
        self.assertEqual(len(entries), 2)

        for entry in entries:
            self.assertTrue(isinstance(entry, floating_ip_dns.FloatingIPDNS))

        self.assertEqual(entries[1].dns_entry['name'], 'host2')
        self.assertEqual(entries[1].dns_entry['ip'], self.testip)

    def test_get_dns_entries_by_name(self):
        entries = cs.floating_ip_dns.get_entries(self.testzone,
                                                 name=self.testname)

        self.assertEqual(len(entries), 1)
        self.assertTrue(isinstance(entries[0], floating_ip_dns.FloatingIPDNS))

        self.assertEqual(entries[0].dns_entry['name'], self.testname)

    def test_create_entry(self):
        response = cs.floating_ip_dns.create_entry(self.testzone,
                                                   self.testname,
                                                   self.testip,
                                                   self.testtype)
        self.assertEqual(response.name, self.testname)
        self.assertEqual(response.ip, self.testip)
        self.assertEqual(response.zone, self.testzone)
        self.assertEqual(response.type, self.testtype)

    def test_delete_entry(self):
        response = cs.floating_ip_dns.delete_entry(self.testzone,
                                                   self.testname)
        cs.assert_called('DELETE', '/os-floating-ip-dns/%s?name=%s' %
                         (self.testzone, self.testname))

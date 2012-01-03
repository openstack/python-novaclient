# Copyright 2011 Andrew Bogott for The Wikimedia Foundation
# All Rights Reserved.
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

import urllib

from novaclient import base


def _quote_zone(zone):
    """Special quoting rule for placing zone names on a url line.

    Zone names tend to have .'s in them.  Urllib doesn't quote dots,
    but Routes tends to choke on them, so we need an extra level of
    by-hand quoting here.
    """
    return urllib.quote(zone.replace('.', '%2E'))


class FloatingIPDNS(base.Resource):
    def delete(self):
        self.manager.delete_entry(self.name, self.zone)


class FloatingIPDNSManager(base.ManagerWithFind):
    resource_class = FloatingIPDNS

    def zones(self):
        """Return the list of available dns zones."""
        return self._list("/os-floating-ip-dns", "zones")

    def get_entries(self, zone, name=None, ip=None):
        """Return a list of entries for the given zone and ip or name."""
        qparams = {}
        if name:
            qparams['name'] = name
        if ip:
            qparams['ip'] = ip

        params = "?%s" % urllib.urlencode(qparams) if qparams else ""

        return self._list("/os-floating-ip-dns/%s%s" %
                              (_quote_zone(zone), params),
                          "dns_entries")

    def create_entry(self, zone, name, ip, dns_type):
        """Add a new DNS entry."""
        body = {'dns_entry':
                 {'name': name,
                  'ip': ip,
                  'dns_type': dns_type,
                  'zone': zone}}

        return self._create("/os-floating-ip-dns", body, "dns_entry")

    def delete_entry(self, zone, name):
        """Delete entry specified by name and zone."""
        qparams = {'name': name}
        params = "?%s" % urllib.urlencode(qparams) if qparams else ""

        self._delete("/os-floating-ip-dns/%s%s" %
                                (_quote_zone(zone), params))

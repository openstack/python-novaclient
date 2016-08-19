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

from six.moves.urllib import parse

from novaclient import api_versions
from novaclient import base


def _quote_domain(domain):
    """Special quoting rule for placing domain names on a url line.

    Domain names tend to have .'s in them.  Urllib doesn't quote dots,
    but Routes tends to choke on them, so we need an extra level of
    by-hand quoting here.
    """
    return parse.quote(domain.replace('.', '%2E'))


class FloatingIPDNSDomain(base.Resource):
    """DEPRECATED"""

    def delete(self):
        """
        DEPRECATED: Delete the own Floating IP DNS domain.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(self.domain)

    def create(self):
        """
        DEPRECATED: Create a Floating IP DNS domain.

        :returns: An instance of novaclient.base.DictWithMeta
        """
        if self.scope == 'public':
            return self.manager.create_public(self.domain, self.project)
        else:
            return self.manager.create_private(self.domain,
                                               self.availability_zone)

    def get(self):
        """
        DEPRECATED: Get the own Floating IP DNS domain.

        :returns: An instance of novaclient.base.TupleWithMeta or
                  novaclient.base.ListWithMeta
        """
        entries = self.manager.domains()
        for entry in entries:
            if entry.get('domain') == self.domain:
                return entry

        return base.TupleWithMeta((), entries.request_ids)


class FloatingIPDNSDomainManager(base.Manager):
    """DEPRECATED"""

    resource_class = FloatingIPDNSDomain

    @api_versions.deprecated_after('2.35')
    def domains(self):
        """DEPRECATED: Return the list of available dns domains."""
        return self._list("/os-floating-ip-dns", "domain_entries")

    @api_versions.deprecated_after('2.35')
    def create_private(self, fqdomain, availability_zone):
        """DEPRECATED: Add or modify a private DNS domain."""
        body = {'domain_entry': {'scope': 'private',
                                 'availability_zone': availability_zone}}
        return self._update('/os-floating-ip-dns/%s' % _quote_domain(fqdomain),
                            body,
                            'domain_entry')

    @api_versions.deprecated_after('2.35')
    def create_public(self, fqdomain, project):
        """DEPRECATED: Add or modify a public DNS domain."""
        body = {'domain_entry': {'scope': 'public', 'project': project}}

        return self._update('/os-floating-ip-dns/%s' % _quote_domain(fqdomain),
                            body, 'domain_entry')

    @api_versions.deprecated_after('2.35')
    def delete(self, fqdomain):
        """
        DEPRECATED: Delete the specified domain.

        :param fqdomain: The domain to delete
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete("/os-floating-ip-dns/%s" % _quote_domain(fqdomain))


class FloatingIPDNSEntry(base.Resource):
    """DEPRECATED"""

    def delete(self):
        """
        DEPRECATED: Delete the own Floating IP DNS entry.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(self.name, self.domain)

    def create(self):
        """
        DEPRECATED: Create a Floating IP DNS entry.

        :returns: :class:`FloatingIPDNSEntry`
        """
        return self.manager.create(self.domain, self.name, self.ip,
                                   self.dns_type)

    def get(self):
        """DEPRECATED"""
        return self.manager.get(self.domain, self.name)


class FloatingIPDNSEntryManager(base.Manager):
    """DEPRECATED"""
    resource_class = FloatingIPDNSEntry

    @api_versions.deprecated_after('2.35')
    def get(self, domain, name):
        """
        DEPRECATED: Return a list of entries for the given domain and IP or
        name.
        """
        return self._get("/os-floating-ip-dns/%s/entries/%s" %
                         (_quote_domain(domain), name), "dns_entry")

    @api_versions.deprecated_after('2.35')
    def get_for_ip(self, domain, ip):
        """
        DEPRECATED: Return a list of entries for the given domain and IP or
        name.
        """
        qparams = {'ip': ip}
        params = "?%s" % parse.urlencode(qparams)

        return self._list("/os-floating-ip-dns/%s/entries%s" %
                          (_quote_domain(domain), params), "dns_entries")

    @api_versions.deprecated_after('2.35')
    def create(self, domain, name, ip, dns_type):
        """DEPRECATED: Add a new DNS entry."""
        body = {'dns_entry': {'ip': ip, 'dns_type': dns_type}}

        return self._update("/os-floating-ip-dns/%s/entries/%s" %
                            (_quote_domain(domain), name), body, "dns_entry")

    @api_versions.deprecated_after('2.35')
    def modify_ip(self, domain, name, ip):
        """DEPRECATED: Add a new DNS entry."""
        body = {'dns_entry': {'ip': ip, 'dns_type': 'A'}}

        return self._update("/os-floating-ip-dns/%s/entries/%s" %
                            (_quote_domain(domain), name), body, "dns_entry")

    @api_versions.deprecated_after('2.35')
    def delete(self, domain, name):
        """
        DEPRECATED: Delete entry specified by name and domain.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete("/os-floating-ip-dns/%s/entries/%s" %
                            (_quote_domain(domain), name))

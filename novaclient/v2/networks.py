# Copyright 2012 OpenStack Foundation
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

"""
Network interface.
"""
from novaclient import api_versions
from novaclient import base
from novaclient import exceptions
from novaclient.i18n import _


class Network(base.Resource):
    """
    A network.
    """
    HUMAN_ID = True
    NAME_ATTR = "label"

    def __repr__(self):
        return "<Network: %s>" % self.label

    def delete(self):
        """
        DEPRECATED: Delete this network.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(self)


class NeutronManager(base.Manager):
    """A manager for name -> id lookups for neutron networks.

    This uses neutron directly from service catalog. Do not use it
    for anything else besides that. You have been warned.
    """

    resource_class = Network

    def find_network(self, name):
        """Find a network by name (user provided input)."""

        with self.alternate_service_type(
                'network', allowed_types=('network',)):

            matches = self._list('/v2.0/networks?name=%s' % name, 'networks')

            num_matches = len(matches)
            if num_matches == 0:
                msg = "No %s matching %s." % (
                    self.resource_class.__name__, name)
                raise exceptions.NotFound(404, msg)
            elif num_matches > 1:
                msg = (_("Multiple %(class)s matches found for "
                         "'%(name)s', use an ID to be more specific.") %
                       {'class': self.resource_class.__name__.lower(),
                        'name': name})
                raise exceptions.NoUniqueMatch(msg)
            else:
                matches[0].append_request_ids(matches.request_ids)
                return matches[0]


class NetworkManager(base.ManagerWithFind):
    """
    DEPRECATED: Manage :class:`Network` resources.
    """
    resource_class = Network

    @api_versions.deprecated_after('2.35')
    def list(self):
        """
        DEPRECATED: Get a list of all networks.

        :rtype: list of :class:`Network`.
        """
        return self._list("/os-networks", "networks")

    @api_versions.deprecated_after('2.35')
    def get(self, network):
        """
        DEPRECATED: Get a specific network.

        :param network: The ID of the :class:`Network` to get.
        :rtype: :class:`Network`
        """
        return self._get("/os-networks/%s" % base.getid(network),
                         "network")

    @api_versions.deprecated_after('2.35')
    def delete(self, network):
        """
        DEPRECATED: Delete a specific network.

        :param network: The ID of the :class:`Network` to delete.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete("/os-networks/%s" % base.getid(network))

    @api_versions.deprecated_after('2.35')
    def create(self, **kwargs):
        """
        DEPRECATED: Create (allocate) a network. The following parameters are
        optional except for label; cidr or cidr_v6 must be specified, too.

        :param label: str
        :param bridge: str
        :param bridge_interface: str
        :param cidr: str
        :param cidr_v6: str
        :param dns1: str
        :param dns2: str
        :param fixed_cidr: str
        :param gateway: str
        :param gateway_v6: str
        :param multi_host: str
        :param priority: str
        :param project_id: str
        :param vlan: int
        :param vlan_start: int
        :param vpn_start: int
        :param mtu: int
        :param enable_dhcp: int
        :param dhcp_server: str
        :param share_address: int
        :param allowed_start: str
        :param allowed_end: str

        :rtype: object of :class:`Network`
        """
        body = {"network": kwargs}
        return self._create('/os-networks', body, 'network')

    @api_versions.deprecated_after('2.35')
    def disassociate(self, network, disassociate_host=True,
                     disassociate_project=True):
        """
        DEPRECATED: Disassociate a specific network from project and/or host.

        :param network: The ID of the :class:`Network`.
        :param disassociate_host: Whether to disassociate the host
        :param disassociate_project: Whether to disassociate the project
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        if disassociate_host and disassociate_project:
            body = {"disassociate": None}
        elif disassociate_project:
            body = {"disassociate_project": None}
        elif disassociate_host:
            body = {"disassociate_host": None}
        else:
            raise exceptions.CommandError(
                _("Must disassociate either host or project or both"))

        resp, body = self.api.client.post("/os-networks/%s/action" %
                                          base.getid(network), body=body)

        return self.convert_into_with_meta(body, resp)

    @api_versions.deprecated_after('2.35')
    def associate_host(self, network, host):
        """
        DEPRECATED: Associate a specific network with a host.

        :param network: The ID of the :class:`Network`.
        :param host: The name of the host to associate the network with
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        resp, body = self.api.client.post("/os-networks/%s/action" %
                                          base.getid(network),
                                          body={"associate_host": host})

        return self.convert_into_with_meta(body, resp)

    @api_versions.deprecated_after('2.35')
    def associate_project(self, network):
        """
        DEPRECATED: Associate a specific network with a project.

        The project is defined by the project authenticated against

        :param network: The ID of the :class:`Network`.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        resp, body = self.api.client.post("/os-networks/add",
                                          body={"id": network})

        return self.convert_into_with_meta(body, resp)

    @api_versions.deprecated_after('2.35')
    def add(self, network=None):
        """
        DEPRECATED: Associates the current project with a network. Network can
        be chosen automatically or provided explicitly.

        :param network: The ID of the :class:`Network` to associate (optional).
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        resp, body = self.api.client.post("/os-networks/add",
                                          body={"id": base.getid(network)
                                                if network else None})

        return self.convert_into_with_meta(body, resp)

# Copyright 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from novaclient import api_versions
from novaclient import base
from novaclient.i18n import _
from novaclient import utils
from novaclient.v2 import shell


class TenantNetwork(base.Resource):
    def delete(self):
        """
        DEPRECATED: Delete this project network.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(network=self)


class TenantNetworkManager(base.ManagerWithFind):
    """DEPRECATED"""
    resource_class = base.Resource

    @api_versions.deprecated_after('2.35')
    def list(self):
        """DEPRECATED"""
        return self._list('/os-tenant-networks', 'networks')

    @api_versions.deprecated_after('2.35')
    def get(self, network):
        """DEPRECATED"""
        return self._get('/os-tenant-networks/%s' % base.getid(network),
                         'network')

    @api_versions.deprecated_after('2.35')
    def delete(self, network):
        """
        DEPRECATED: Delete a specified project network.

        :param network: a project network to delete
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete('/os-tenant-networks/%s' % base.getid(network))

    @api_versions.deprecated_after('2.35')
    def create(self, label, cidr):
        """DEPRECATED"""
        body = {'network': {'label': label, 'cidr': cidr}}
        return self._create('/os-tenant-networks', body, 'network')


@utils.arg('network_id', metavar='<network_id>', help='ID of network')
def do_net(cs, args):
    """
    DEPRECATED, use tenant-network-show instead.
    """
    do_tenant_network_show(cs, args)


@utils.arg('network_id', metavar='<network_id>', help='ID of network')
@shell.deprecated_network
def do_tenant_network_show(cs, args):
    """
    Show a tenant network.
    """
    network = cs.tenant_networks.get(args.network_id)
    utils.print_dict(network._info)


def do_net_list(cs, args):
    """
    DEPRECATED, use tenant-network-list instead.
    """
    do_tenant_network_list(cs, args)


@shell.deprecated_network
def do_tenant_network_list(cs, args):
    """
    List tenant networks.
    """
    networks = cs.tenant_networks.list()
    utils.print_list(networks, ['ID', 'Label', 'CIDR'])


@utils.arg(
    'label',
    metavar='<network_label>',
    help=_('Network label (ex. my_new_network)'))
@utils.arg(
    'cidr',
    metavar='<cidr>',
    help=_('IP block to allocate from (ex. 172.16.0.0/24 or 2001:DB8::/64)'))
def do_net_create(cs, args):
    """
    DEPRECATED, use tenant-network-create instead.
    """
    do_tenant_network_create(cs, args)


@utils.arg(
    'label',
    metavar='<network_label>',
    help=_('Network label (ex. my_new_network)'))
@utils.arg(
    'cidr',
    metavar='<cidr>',
    help=_('IP block to allocate from (ex. 172.16.0.0/24 or 2001:DB8::/64)'))
@shell.deprecated_network
def do_tenant_network_create(cs, args):
    """
    Create a tenant network.
    """
    network = cs.tenant_networks.create(args.label, args.cidr)
    utils.print_dict(network._info)


@utils.arg('network_id', metavar='<network_id>', help='ID of network')
def do_net_delete(cs, args):
    """
    DEPRECATED, use tenant-network-delete instead.
    """
    do_tenant_network_delete(cs, args)


@utils.arg('network_id', metavar='<network_id>', help='ID of network')
@shell.deprecated_network
def do_tenant_network_delete(cs, args):
    """
    Delete a tenant network.
    """
    cs.tenant_networks.delete(args.network_id)

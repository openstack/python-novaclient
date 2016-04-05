# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
Baremetal interface (v2 extension).
"""

from novaclient import base
from novaclient.i18n import _
from novaclient import utils


class BareMetalNode(base.Resource):
    """
    A baremetal node (typically a physical server or an empty VM).
    """

    def __repr__(self):
        return "<BareMetalNode: %s>" % self.id


class BareMetalNodeInterface(base.Resource):
    """
    An interface belonging to a baremetal node.
    """

    def __repr__(self):
        return "<BareMetalNodeInterface: %s>" % self.id


class BareMetalNodeManager(base.ManagerWithFind):
    """
    Manage :class:`BareMetalNode` resources.
    """
    resource_class = BareMetalNode

    def get(self, node_id):
        """
        Get a baremetal node.

        :param node_id: The ID of the node to delete.
        :rtype: :class:`BareMetalNode`
        """
        return self._get("/os-baremetal-nodes/%s" % node_id, 'node')

    def list(self):
        """
        Get a list of all baremetal nodes.

        :rtype: list of :class:`BareMetalNode`
        """
        return self._list('/os-baremetal-nodes', 'nodes')

    def list_interfaces(self, node_id):
        """
        List the interfaces on a baremetal node.

        :param node_id: The ID of the node to list.
        :rtype: novaclient.base.ListWithMeta
        """
        interfaces = base.ListWithMeta([], None)
        node = self._get("/os-baremetal-nodes/%s" % node_id, 'node')
        interfaces.append_request_ids(node.request_ids)
        for interface in node.interfaces:
            interface_object = BareMetalNodeInterface(self, interface)
            interfaces.append(interface_object)
        return interfaces


def _translate_baremetal_node_keys(collection):
    convert = [('service_host', 'host'),
               ('local_gb', 'disk_gb'),
               ('prov_mac_address', 'mac_address'),
               ('pm_address', 'pm_address'),
               ('pm_user', 'pm_username'),
               ('pm_password', 'pm_password'),
               ('terminal_port', 'terminal_port'),
               ]
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _print_baremetal_nodes_list(nodes):
    """Print the list of baremetal nodes."""

    def _parse_address(fields):
        macs = []
        for interface in fields.interfaces:
            macs.append(interface['address'])
        return ', '.join("%s" % i for i in macs)

    formatters = {
        'MAC Address': _parse_address
    }

    _translate_baremetal_node_keys(nodes)
    utils.print_list(nodes, [
        'ID',
        'Host',
        'Task State',
        'CPUs',
        'Memory_MB',
        'Disk_GB',
        'MAC Address',
        'PM Address',
        'PM Username',
        'PM Password',
        'Terminal Port',
    ], formatters=formatters)


def do_baremetal_node_list(cs, _args):
    """Print list of available baremetal nodes."""
    nodes = cs.baremetal.list()
    _print_baremetal_nodes_list(nodes)


def _find_baremetal_node(cs, node):
    """Get a node by ID."""
    return utils.find_resource(cs.baremetal, node)


def _print_baremetal_resource(resource):
    """Print details of a baremetal resource."""
    info = resource._info.copy()
    utils.print_dict(info)


def _print_baremetal_node_interfaces(interfaces):
    """Print interfaces of a baremetal node."""
    utils.print_list(interfaces, [
        'ID',
        'Datapath_ID',
        'Port_No',
        'Address',
    ])


@utils.arg(
    'node',
    metavar='<node>',
    help=_("ID of node"))
def do_baremetal_node_show(cs, args):
    """Show information about a baremetal node."""
    node = _find_baremetal_node(cs, args.node)
    _print_baremetal_resource(node)


@utils.arg('node', metavar='<node>', help=_("ID of node"))
def do_baremetal_interface_list(cs, args):
    """List network interfaces associated with a baremetal node."""
    interfaces = cs.baremetal.list_interfaces(args.node)
    _print_baremetal_node_interfaces(interfaces)

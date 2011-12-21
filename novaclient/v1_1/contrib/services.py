# Copyright 2011 OpenStack, LLC
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

"""Services Interface"""

from novaclient import base
from novaclient import utils
from novaclient.v1_1 import servers


class Service(base.Resource):
    """A service."""

    def details(self):
        return self.manager.details(self)

    def version(self, service):
        return self.manager.version(self)

    def config(self, service):
        return self.manager.config(self)

    def servers(self, service):
        return self.manager.servers(self)


class ServiceManager(base.ManagerWithFind):
    """Manage :class:`Service` resources."""
    resource_class = Service

    def list(self):
        """Return a list of all services."""
        return self._list("/services", "services")

    def get(self, service):
        """Return a specified service."""
        return self._get("/services/%s" % base.getid(service), "service")

    def details(self, service):
        """Return service-type specific information for service."""
        res, body = self.api.client.get(
                "/services/%s/details" % base.getid(service))
        return body['details']

    def version(self, service):
        """Return version information for a service."""
        res, body = self.api.client.get(
                "/services/%s/version" % base.getid(service))
        return body['version']['string']

    def config(self, service):
        """Return configuration information for a service."""
        res, body = self.api.client.get(
                "/services/%s/config" % base.getid(service))
        return body['config']

    def servers(self, service):
        """Return list of servers associated with compute service."""
        res, body = self.api.client.get(
                "/services/%s/servers" % base.getid(service))
        obj_class = servers.Server
        data = body['servers']
        with self.uuid_cache(obj_class, mode="w"):
            return [obj_class(self, res, loaded=True) for res in data if res]


def do_service_list(cs, args):
    """List available service attributes."""
    services = cs.services.list()
    columns = ['ID', 'topic', 'host', 'disabled', 'report_count', 'updated_at']
    utils.print_list(services, columns)


@utils.arg('id', metavar='<ID>', help='Service ID to show.')
def do_service_show(cs, args):
    """List available service attributes."""
    service = cs.services.get(args.id)
    utils.print_dict(service._info)


@utils.arg('id', metavar='<ID>', help='Service ID to show details for.')
def do_service_details(cs, args):
    """List available service attributes."""
    details = cs.services.details(args.id)
    utils.print_dict(details)


@utils.arg('id', metavar='<ID>', help='Service ID to show details for.')
def do_service_details(cs, args):
    """List available service attributes."""
    details = cs.services.details(args.id)
    utils.print_dict(details)


@utils.arg('id', metavar='<ID>', help='Service ID to show version for.')
def do_service_version(cs, args):
    """List available service attributes."""
    version = cs.services.version(args.id)
    print version


@utils.arg('id', metavar='<ID>', help='Service ID to show config info for.')
def do_service_config(cs, args):
    """List available service attributes."""
    config = cs.services.config(args.id)
    utils.print_dict(config)


@utils.arg('id', metavar='<ID>', help='Service ID to show config info for.')
def do_service_servers(cs, args):
    """List available service attributes."""
    servers = cs.services.servers(args.id)
    columns = ['ID', 'Name', 'Status', 'Networks']
    formatters = {'Networks': utils._format_servers_list_networks}
    utils.print_list(servers, columns, formatters)

# Copyright 2011 OpenStack Foundation
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
DEPRECATED host interface
"""
import warnings

from novaclient import api_versions
from novaclient import base
from novaclient.i18n import _


HOSTS_DEPRECATION_WARNING = (
    _('The os-hosts API is deprecated. This API binding will be removed '
      'in the first major release after the Nova server 16.0.0 Pike release.')
)


class Host(base.Resource):
    """DEPRECATED"""
    def __repr__(self):
        return "<Host: %s>" % self.host

    def _add_details(self, info):
        dico = 'resource' in info and info['resource'] or info
        for (k, v) in dico.items():
            setattr(self, k, v)

    @api_versions.wraps("2.0", "2.42")
    def update(self, values):
        return self.manager.update(self.host, values)

    @api_versions.wraps("2.0", "2.42")
    def startup(self):
        return self.manager.host_action(self.host, 'startup')

    @api_versions.wraps("2.0", "2.42")
    def shutdown(self):
        return self.manager.host_action(self.host, 'shutdown')

    @api_versions.wraps("2.0", "2.42")
    def reboot(self):
        return self.manager.host_action(self.host, 'reboot')

    @property
    def host_name(self):
        return self.host

    @host_name.setter
    def host_name(self, value):
        # A host from hosts.list() has the attribute "host_name" instead of
        # "host." This sets "host" if that's the case. Even though it doesn't
        # exactly mirror the response format, it enables users to work with
        # host objects from list and non-list operations interchangeably.
        self.host = value


class HostManager(base.ManagerWithFind):
    resource_class = Host

    @api_versions.wraps("2.0", "2.42")
    def get(self, host):
        """
        DEPRECATED Describes cpu/memory/hdd info for host.

        :param host: destination host name.
        """
        warnings.warn(HOSTS_DEPRECATION_WARNING, DeprecationWarning)
        return self._list("/os-hosts/%s" % host, "host")

    @api_versions.wraps("2.0", "2.42")
    def update(self, host, values):
        """DEPRECATED Update status or maintenance mode for the host."""
        warnings.warn(HOSTS_DEPRECATION_WARNING, DeprecationWarning)
        return self._update("/os-hosts/%s" % host, values)

    @api_versions.wraps("2.0", "2.42")
    def host_action(self, host, action):
        """
        DEPRECATED Perform an action on a host.

        :param host: The host to perform an action
        :param action: The action to perform
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        warnings.warn(HOSTS_DEPRECATION_WARNING, DeprecationWarning)
        url = '/os-hosts/%s/%s' % (host, action)
        resp, body = self.api.client.get(url)
        return base.TupleWithMeta((resp, body), resp)

    @api_versions.wraps("2.0", "2.42")
    def list(self, zone=None):
        warnings.warn(HOSTS_DEPRECATION_WARNING, DeprecationWarning)
        url = '/os-hosts'
        if zone:
            url = '/os-hosts?zone=%s' % zone
        return self._list(url, "hosts")

    list_all = list

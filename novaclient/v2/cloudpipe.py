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

"""DEPRECATED Cloudpipe interface."""

import warnings

from novaclient import base
from novaclient.i18n import _


DEPRECATION_WARNING = (
    _('The os-cloudpipe Nova API has been removed. This API binding will be '
      'removed in the first major release after the Nova server 16.0.0 Pike '
      'release.')
)


class Cloudpipe(base.Resource):
    """A cloudpipe instance is a VPN attached to a project's VLAN."""

    def __repr__(self):
        return "<Cloudpipe: %s>" % self.project_id

    def delete(self):
        """
        DEPRECATED Delete the own cloudpipe instance

        :returns: An instance of novaclient.base.TupleWithMeta
        """

        warnings.warn(DEPRECATION_WARNING)

        return self.manager.delete(self)


class CloudpipeManager(base.ManagerWithFind):
    """DEPRECATED"""

    resource_class = Cloudpipe

    def create(self, project):
        """DEPRECATED Launch a cloudpipe instance.

        :param project: UUID of the project (tenant) for the cloudpipe
        """

        warnings.warn(DEPRECATION_WARNING)

        body = {'cloudpipe': {'project_id': project}}
        return self._create('/os-cloudpipe', body, 'instance_id',
                            return_raw=True)

    def list(self):
        """DEPRECATED Get a list of cloudpipe instances."""

        warnings.warn(DEPRECATION_WARNING)

        return self._list('/os-cloudpipe', 'cloudpipes')

    def update(self, address, port):
        """DEPRECATED Configure cloudpipe parameters for the project.

        Update VPN address and port for all networks associated
        with the project defined by authentication

        :param address: IP address
        :param port: Port number
        :returns: An instance of novaclient.base.TupleWithMeta
        """

        warnings.warn(DEPRECATION_WARNING)

        body = {'configure_project': {'vpn_ip': address,
                                      'vpn_port': port}}
        return self._update("/os-cloudpipe/configure-project", body)

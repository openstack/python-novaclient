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
DEPRECATED Virtual Interfaces
"""

import warnings

from novaclient import api_versions
from novaclient import base
from novaclient.i18n import _


class VirtualInterface(base.Resource):
    def __repr__(self):
        return "<VirtualInterface>"


class VirtualInterfaceManager(base.ManagerWithFind):
    """DEPRECATED"""
    resource_class = VirtualInterface

    @api_versions.wraps('2.0', '2.43')
    def list(self, instance_id):
        """DEPRECATED"""
        warnings.warn(_('The os-virtual-interfaces API is deprecated. This '
                        'API binding will be removed in the first major '
                        'release after the Nova server 16.0.0 Pike release.'),
                      DeprecationWarning)
        return self._list('/servers/%s/os-virtual-interfaces' % instance_id,
                          'virtual_interfaces')

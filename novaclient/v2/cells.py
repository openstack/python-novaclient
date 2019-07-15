# Copyright 2013 Rackspace Hosting
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

import warnings

from novaclient import base
from novaclient.i18n import _

CELL_V1_DEPRECATION_WARNING = _(
    'The cells v1 interface has been deprecated in Nova since 16.0.0 Pike '
    'Release. This API binding will be removed in the first major release '
    'after the Nova server 20.0.0 Train release.')


class Cell(base.Resource):
    """DEPRECATED"""
    def __repr__(self):
        return "<Cell: %s>" % self.name


class CellsManager(base.Manager):
    """DEPRECATED"""
    resource_class = Cell

    def get(self, cell_name):
        """
        DEPRECATED Get a cell.

        :param cell_name: Name of the :class:`Cell` to get.
        :rtype: :class:`Cell`
        """
        warnings.warn(CELL_V1_DEPRECATION_WARNING, DeprecationWarning)
        return self._get("/os-cells/%s" % cell_name, "cell")

    def capacities(self, cell_name=None):
        """
        DEPRECATED Get capacities for a cell.

        :param cell_name: Name of the :class:`Cell` to get capacities for.
        :rtype: :class:`Cell`
        """
        warnings.warn(CELL_V1_DEPRECATION_WARNING, DeprecationWarning)
        path = ["%s/capacities" % cell_name, "capacities"][cell_name is None]
        return self._get("/os-cells/%s" % path, "cell")

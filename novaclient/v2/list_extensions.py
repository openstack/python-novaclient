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

import warnings

from novaclient import base
from novaclient.i18n import _

EXTENSION_DEPRECATION_WARNING = _(
    'The API extension interface has been deprecated since 12.0.0 Liberty '
    'Release. This API binding will be removed in the first major release '
    'after the Nova server 20.0.0 Train release.')


class ListExtResource(base.Resource):
    """DEPRECATED"""
    @property
    def summary(self):
        """DEPRECATED"""
        warnings.warn(EXTENSION_DEPRECATION_WARNING, DeprecationWarning)
        descr = self.description.strip()
        if not descr:
            return '??'
        lines = descr.split("\n")
        if len(lines) == 1:
            return lines[0]
        else:
            return lines[0] + "..."


class ListExtManager(base.Manager):
    """DEPRECATED"""
    resource_class = ListExtResource

    def show_all(self):
        """DEPRECATED"""
        warnings.warn(EXTENSION_DEPRECATION_WARNING, DeprecationWarning)
        return self._list("/extensions", 'extensions')

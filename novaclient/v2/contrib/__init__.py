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

import inspect
import warnings

from novaclient.i18n import _LW

# NOTE(andreykurilin): "baremetal" and "tenant_networks" extensions excluded
#   here deliberately. They were deprecated separately from deprecation
#   extension mechanism and I prefer to not auto-load them by default
#   (V2_0_EXTENSIONS is designed for such behaviour).
V2_0_EXTENSIONS = {
    'assisted_volume_snapshots':
        'novaclient.v2.assisted_volume_snapshots',
    'cells': 'novaclient.v2.cells',
    'instance_action': 'novaclient.v2.instance_action',
    'list_extensions': 'novaclient.v2.list_extensions',
    'migrations': 'novaclient.v2.migrations',
    'server_external_events': 'novaclient.v2.server_external_events',
}


def warn(alternative=True):
    """Prints warning msg for contrib modules."""
    frm = inspect.stack()[1]
    module_name = inspect.getmodule(frm[0]).__name__
    if module_name.startswith("novaclient.v2.contrib."):
        msg = (_LW("Module `%s` is deprecated as of OpenStack Ocata") %
               module_name)
        if alternative:
            new_module_name = module_name.replace("contrib.", "")
            msg += _LW(" in favor of `%s`") % new_module_name

        msg += (_LW(" and will be removed after OpenStack Pike."))

        if not alternative:
            msg += _LW(" All shell commands were moved to "
                       "`novaclient.v2.shell` and will be automatically "
                       "loaded.")

        warnings.warn(msg)

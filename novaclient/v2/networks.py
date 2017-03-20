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
from novaclient import base
from novaclient import exceptions
from novaclient.i18n import _


class Network(base.Resource):
    """
    A network as defined in the Networking (Neutron) API.
    """
    HUMAN_ID = True
    NAME_ATTR = "name"

    def __repr__(self):
        return "<Network: %s>" % self.name


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

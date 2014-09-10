# Copyright 2011 OpenStack Foundation
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

from six.moves.urllib import parse

from novaclient.v1_1 import limits


class Limits(limits.Limits):
    pass


class RateLimit(limits.RateLimit):
    pass


class AbsoluteLimit(limits.AbsoluteLimit):
    pass


class LimitsManager(limits.LimitsManager):
    """Manager object used to interact with limits resource."""

    resource_class = Limits

    def get(self, reserved=False, tenant_id=None):
        """
        Get a specific extension.

        :rtype: :class:`Limits`
        """
        opts = {}
        if reserved:
            opts['reserved'] = 1
        if tenant_id:
            opts['tenant_id'] = tenant_id
        query_string = "?%s" % parse.urlencode(opts) if opts else ""

        return self._get("/limits%s" % query_string, "limits")

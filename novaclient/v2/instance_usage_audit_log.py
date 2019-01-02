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

from oslo_utils import encodeutils
import six
from six.moves.urllib import parse

from novaclient import base


class InstanceUsageAuditLog(base.Resource):
    pass


class InstanceUsageAuditLogManager(base.Manager):
    resource_class = InstanceUsageAuditLog

    def get(self, before=None):
        """Get server usage audits.

        :param before: Filters the response by the date and time
                       before which to list usage audits.
        """
        if before:
            if six.PY2:
                before = encodeutils.safe_encode(before)
            return self._get('/os-instance_usage_audit_log/%s' %
                             parse.quote(before, safe=''),
                             'instance_usage_audit_log')
        else:
            return self._get('/os-instance_usage_audit_log',
                             'instance_usage_audit_logs')

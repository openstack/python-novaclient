# Copyright 2010 Jacob Kaplan-Moss

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
DEPRECATED Certificate interface.
"""

import warnings

from novaclient import base
from novaclient.i18n import _

CERT_DEPRECATION_WARNING = (
    _('The nova-cert service is deprecated. This API binding will be removed '
      'in the first major release after the Nova server 16.0.0 Pike release.')
)


class Certificate(base.Resource):
    """DEPRECATED"""
    def __repr__(self):
        return ("<Certificate: private_key=[%s bytes] data=[%s bytes]>" %
                (len(self.private_key) if self.private_key else 0,
                 len(self.data)))


class CertificateManager(base.Manager):
    """DEPRECATED Manage :class:`Certificate` resources."""
    resource_class = Certificate

    def create(self):
        """DEPRECATED Create a x509 certificate for a user in tenant."""
        warnings.warn(CERT_DEPRECATION_WARNING, DeprecationWarning)
        return self._create('/os-certificates', {}, 'certificate')

    def get(self):
        """DEPRECATED Get root certificate."""
        warnings.warn(CERT_DEPRECATION_WARNING, DeprecationWarning)
        return self._get("/os-certificates/root", 'certificate')

# Copyright 2011 OpenStack LLC.
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

import copy

from novaclient.keystone import tenants
from novaclient.keystone import users


class Client(object):
    """
    Top-level object to access the OpenStack Keystone API.

    Create an instance with your creds::

        >>> from novaclient import client
        >>> conn = client.HTTPClient(USER, PASS, TENANT, KEYSTONE_URL)
        >>> from novaclient import keystone
        >>> kc = keystone.Client(conn)

    Then call methods on its managers::

        >>> kc.tenants.list()
        ...
        >>> kc.users.list()
        ...

    """

    def __init__(self, client):
        # FIXME(ja): managers work by making calls against self.client
        #            which assumes management_url is set for the service.
        #            with keystone you get a token/endpoints for multiple
        #            services - so we have to clone and override the endpoint
        # NOTE(ja): need endpoint from service catalog...  no lazy auth
        client.authenticate()
        self.client = copy.copy(client)
        endpoint = client.service_catalog.url_for(service_type='identity',
                                                    endpoint_type='adminURL')
        self.client.management_url = endpoint

        self.tenants = tenants.TenantManager(self)
        self.users = users.UserManager(self)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

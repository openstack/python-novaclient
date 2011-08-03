# Copyright 2010 Jacob Kaplan-Moss
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

from novaclient.v1_1 import client
from novaclient.v1_1 import exceptions
from novaclient.v1_1 import flavors
from novaclient.v1_1 import images
from novaclient.v1_1 import servers


class Client(object):
    """
    Top-level object to access the OpenStack Compute v1.0 API.

    Create an instance with your creds::

        >>> os = novaclient.v1_1.Client(USERNAME, API_KEY, PROJECT_ID, AUTH_URL)

    Then call methods on its managers::

        >>> os.servers.list()
        ...
        >>> os.flavors.list()
        ...

    &c.
    """

    def __init__(self, username, apikey, projectid, auth_url=None, timeout=None):
        """Initialize v1.0 Openstack Client."""
        self.flavors = flavors.FlavorManager(self)
        self.images = images.ImageManager(self)
        self.servers = servers.ServerManager(self)

        auth_url = auth_url or "https://auth.api.rackspacecloud.com/v1.0"

        self.client = client.HTTPClient(username,
                                        apikey,
                                        projectid,
                                        auth_url,
                                        timeout=timeout)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`novaclient.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

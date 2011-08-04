

from novaclient import client
from novaclient.v1_1 import flavors
from novaclient.v1_1 import images
from novaclient.v1_1 import servers
from novaclient.v1_1 import zones



class Client(object):
    """
    Top-level object to access the OpenStack Compute API.

    Create an instance with your creds::

        >>> client = Client(USERNAME, API_KEY, PROJECT_ID, AUTH_URL)

    Then call methods on its managers::

        >>> client.servers.list()
        ...
        >>> client.flavors.list()
        ...

    """

    def __init__(self, username, api_key, project_id, auth_url, timeout=None):
        self.flavors = flavors.FlavorManager(self)
        self.images = images.ImageManager(self)
        self.servers = servers.ServerManager(self)
        self.zones = zones.ZoneManager(self)

        self.client = client.HTTPClient(username,
                                        api_key,
                                        project_id,
                                        auth_url,
                                        timeout=timeout)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

from novaclient import client
from novaclient.v1_1 import flavors
from novaclient.v1_1 import floating_ips
from novaclient.v1_1 import images
from novaclient.v1_1 import keypairs
from novaclient.v1_1 import security_group_rules
from novaclient.v1_1 import security_groups
from novaclient.v1_1 import servers
from novaclient.v1_1 import quotas
from novaclient.v1_1 import volumes
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

    # FIXME(jesse): project_id isn't required to autenticate
    def __init__(self, username, api_key, project_id, auth_url,
                  insecure=False, timeout=None, token=None, region_name=None):
        self.flavors = flavors.FlavorManager(self)
        self.floating_ips = floating_ips.FloatingIPManager(self)
        self.images = images.ImageManager(self)
        self.servers = servers.ServerManager(self)

        # extensions
        self.volumes = volumes.VolumeManager(self)
        self.keypairs = keypairs.KeypairManager(self)
        self.zones = zones.ZoneManager(self)
        self.quotas = quotas.QuotaSetManager(self)
        self.security_groups = security_groups.SecurityGroupManager(self)
        self.security_group_rules = \
            security_group_rules.SecurityGroupRuleManager(self)

        self.client = client.HTTPClient(username,
                                        api_key,
                                        project_id,
                                        auth_url,
                                        insecure=insecure,
                                        timeout=timeout,
                                        token=token,
                                        region_name=region_name)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

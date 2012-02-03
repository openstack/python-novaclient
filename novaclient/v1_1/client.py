from novaclient import client
from novaclient.v1_1 import certs
from novaclient.v1_1 import aggregates
from novaclient.v1_1 import flavors
from novaclient.v1_1 import floating_ip_dns
from novaclient.v1_1 import floating_ips
from novaclient.v1_1 import floating_ip_pools
from novaclient.v1_1 import hosts
from novaclient.v1_1 import images
from novaclient.v1_1 import keypairs
from novaclient.v1_1 import limits
from novaclient.v1_1 import quotas
from novaclient.v1_1 import security_group_rules
from novaclient.v1_1 import security_groups
from novaclient.v1_1 import servers
from novaclient.v1_1 import usage
from novaclient.v1_1 import virtual_interfaces
from novaclient.v1_1 import volumes
from novaclient.v1_1 import volume_snapshots
from novaclient.v1_1 import zones


class Client(object):
    """
    Top-level object to access the OpenStack Compute API.

    Create an instance with your creds::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

    Then call methods on its managers::

        >>> client.servers.list()
        ...
        >>> client.flavors.list()
        ...

    """

    # FIXME(jesse): project_id isn't required to authenticate
    def __init__(self, username, api_key, project_id, auth_url,
                  insecure=False, timeout=None, token=None, region_name=None,
                  endpoint_type='publicURL', extensions=None,
                  service_name=None):
        # FIXME(comstud): Rename the api_key argument above when we
        # know it's not being used as keyword argument
        password = api_key
        self.flavors = flavors.FlavorManager(self)
        self.images = images.ImageManager(self)
        self.limits = limits.LimitsManager(self)
        self.servers = servers.ServerManager(self)

        # extensions
        self.dns_domains = floating_ip_dns.FloatingIPDNSDomainManager(self)
        self.dns_entries = floating_ip_dns.FloatingIPDNSEntryManager(self)
        self.certs = certs.CertificateManager(self)
        self.floating_ips = floating_ips.FloatingIPManager(self)
        self.floating_ip_pools = floating_ip_pools.FloatingIPPoolManager(self)
        self.volumes = volumes.VolumeManager(self)
        self.volume_snapshots = volume_snapshots.SnapshotManager(self)
        self.keypairs = keypairs.KeypairManager(self)
        self.zones = zones.ZoneManager(self)
        self.quotas = quotas.QuotaSetManager(self)
        self.security_groups = security_groups.SecurityGroupManager(self)
        self.security_group_rules = \
            security_group_rules.SecurityGroupRuleManager(self)
        self.usage = usage.UsageManager(self)
        self.virtual_interfaces = \
            virtual_interfaces.VirtualInterfaceManager(self)
        self.aggregates = aggregates.AggregateManager(self)
        self.hosts = hosts.HostManager(self)

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

        self.client = client.HTTPClient(username,
                                        password,
                                        project_id,
                                        auth_url,
                                        insecure=insecure,
                                        timeout=timeout,
                                        token=token,
                                        region_name=region_name,
                                        endpoint_type=endpoint_type,
                                        service_name=service_name)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

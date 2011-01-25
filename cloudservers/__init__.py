__version__ = '1.2'

from cloudservers.backup_schedules import (
        BackupSchedule, BackupScheduleManager,
        BACKUP_WEEKLY_DISABLED, BACKUP_WEEKLY_SUNDAY, BACKUP_WEEKLY_MONDAY,
        BACKUP_WEEKLY_TUESDAY, BACKUP_WEEKLY_WEDNESDAY,
        BACKUP_WEEKLY_THURSDAY, BACKUP_WEEKLY_FRIDAY, BACKUP_WEEKLY_SATURDAY,
        BACKUP_DAILY_DISABLED, BACKUP_DAILY_H_0000_0200,
        BACKUP_DAILY_H_0200_0400, BACKUP_DAILY_H_0400_0600,
        BACKUP_DAILY_H_0600_0800, BACKUP_DAILY_H_0800_1000,
        BACKUP_DAILY_H_1000_1200, BACKUP_DAILY_H_1200_1400,
        BACKUP_DAILY_H_1400_1600, BACKUP_DAILY_H_1600_1800,
        BACKUP_DAILY_H_1800_2000, BACKUP_DAILY_H_2000_2200,
        BACKUP_DAILY_H_2200_0000)
from cloudservers.client import CloudServersClient
from cloudservers.exceptions import (CloudServersException, BadRequest,
        Unauthorized, Forbidden, NotFound, OverLimit)
from cloudservers.flavors import FlavorManager, Flavor
from cloudservers.images import ImageManager, Image
from cloudservers.ipgroups import IPGroupManager, IPGroup
from cloudservers.servers import (ServerManager, Server, REBOOT_HARD,
                                 REBOOT_SOFT)


class CloudServers(object):
    """
    Top-level object to access the Rackspace Cloud Servers API.

    Create an instance with your creds::

        >>> cs = CloudServers(USERNAME, API_KEY [, AUTH_URL])

    Then call methods on its managers::

        >>> cs.servers.list()
        ...
        >>> cs.flavors.list()
        ...

    &c.
    """

    def __init__(self, username, apikey,
                 auth_url='https://auth.api.rackspacecloud.com/v1.0'):
        self.backup_schedules = BackupScheduleManager(self)
        self.client = CloudServersClient(username, apikey, auth_url)
        self.flavors = FlavorManager(self)
        self.images = ImageManager(self)
        self.ipgroups = IPGroupManager(self)
        self.servers = ServerManager(self)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`cloudservers.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

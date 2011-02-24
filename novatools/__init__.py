# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""
novatools module.
"""

__version__ = '2.2'

from novatools.backup_schedules import (
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
from novatools.client import OpenStackClient
from novatools.exceptions import (OpenStackException, BadRequest,
        Unauthorized, Forbidden, NotFound, OverLimit)
from novatools.flavors import FlavorManager, Flavor
from novatools.images import ImageManager, Image
from novatools.ipgroups import IPGroupManager, IPGroup
from novatools.servers import (ServerManager, Server, REBOOT_HARD,
                                 REBOOT_SOFT)
from novatools.zones import Zone, ZoneManager


class OpenStack(object):
    """
    Top-level object to access the OpenStack Nova API.

    Create an instance with your creds::

        >>> os = OpenStack(USERNAME, API_KEY, AUTH_URL)

    Then call methods on its managers::

        >>> os.servers.list()
        ...
        >>> os.flavors.list()
        ...

    &c.
    """

    def __init__(self, username, apikey,
                 auth_url='https://auth.api.rackspacecloud.com/v1.0'):
        self.backup_schedules = BackupScheduleManager(self)
        self.client = OpenStackClient(username, apikey, auth_url)
        self.flavors = FlavorManager(self)
        self.images = ImageManager(self)
        self.ipgroups = IPGroupManager(self)
        self.servers = ServerManager(self)
        self.zones = ZoneManager(self)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`novatools.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

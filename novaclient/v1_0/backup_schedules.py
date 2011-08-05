# Copyright 2010 Jacob Kaplan-Moss
"""
Backup Schedule interface.
"""

from novaclient import base


BACKUP_WEEKLY_DISABLED = 'DISABLED'
BACKUP_WEEKLY_SUNDAY = 'SUNDAY'
BACKUP_WEEKLY_MONDAY = 'MONDAY'
BACKUP_WEEKLY_TUESDAY = 'TUESDAY'
BACKUP_WEEKLY_WEDNESDAY = 'WEDNESDAY'
BACKUP_WEEKLY_THURSDAY = 'THURSDAY'
BACKUP_WEEKLY_FRIDAY = 'FRIDAY'
BACKUP_WEEKLY_SATURDAY = 'SATURDAY'

BACKUP_DAILY_DISABLED = 'DISABLED'
BACKUP_DAILY_H_0000_0200 = 'H_0000_0200'
BACKUP_DAILY_H_0200_0400 = 'H_0200_0400'
BACKUP_DAILY_H_0400_0600 = 'H_0400_0600'
BACKUP_DAILY_H_0600_0800 = 'H_0600_0800'
BACKUP_DAILY_H_0800_1000 = 'H_0800_1000'
BACKUP_DAILY_H_1000_1200 = 'H_1000_1200'
BACKUP_DAILY_H_1200_1400 = 'H_1200_1400'
BACKUP_DAILY_H_1400_1600 = 'H_1400_1600'
BACKUP_DAILY_H_1600_1800 = 'H_1600_1800'
BACKUP_DAILY_H_1800_2000 = 'H_1800_2000'
BACKUP_DAILY_H_2000_2200 = 'H_2000_2200'
BACKUP_DAILY_H_2200_0000 = 'H_2200_0000'


class BackupSchedule(base.Resource):
    """
    Represents the daily or weekly backup schedule for some server.
    """
    def get(self):
        """
        Get this `BackupSchedule` again from the API.
        """
        return self.manager.get(server=self.server)

    def delete(self):
        """
        Delete (i.e. disable and remove) this scheduled backup.
        """
        self.manager.delete(server=self.server)

    def update(self, enabled=True, weekly=BACKUP_WEEKLY_DISABLED,
                                   daily=BACKUP_DAILY_DISABLED):
        """
        Update this backup schedule.

        See :meth:`BackupScheduleManager.create` for details.
        """
        self.manager.create(self.server, enabled, weekly, daily)


class BackupScheduleManager(base.Manager):
    """
    Manage server backup schedules.
    """
    resource_class = BackupSchedule

    def get(self, server):
        """
        Get the current backup schedule for a server.

        :arg server: The server (or its ID).
        :rtype: :class:`BackupSchedule`
        """
        s = base.getid(server)
        schedule = self._get('/servers/%s/backup_schedule' % s,
                             'backupSchedule')
        schedule.server = server
        return schedule

    # Backup schedules use POST for both create and update, so allow both here.
    # Unlike the rest of the API, POST here returns no body, so we can't use
    # the nice little helper methods.

    def create(self, server, enabled=True, weekly=BACKUP_WEEKLY_DISABLED,
                                           daily=BACKUP_DAILY_DISABLED):
        """
        Create or update the backup schedule for the given server.

        :arg server: The server (or its ID).
        :arg enabled: boolean; should this schedule be enabled?
        :arg weekly: Run a weekly backup on this day
                     (one of the `BACKUP_WEEKLY_*` constants)
        :arg daily: Run a daily backup at this time
                    (one of the `BACKUP_DAILY_*` constants)
        """
        s = base.getid(server)
        body = {'backupSchedule': {
            'enabled': enabled, 'weekly': weekly, 'daily': daily
        }}
        self.api.client.post('/servers/%s/backup_schedule' % s, body=body)

    update = create

    def delete(self, server):
        """
        Remove the scheduled backup for `server`.

        :arg server: The server (or its ID).
        """
        s = base.getid(server)
        self._delete('/servers/%s/backup_schedule' % s)

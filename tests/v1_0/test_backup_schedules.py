from __future__ import absolute_import

from novaclient.v1_0 import backup_schedules

from .fakes import FakeClient
from .utils import assert_isinstance

os = FakeClient()


def test_get_backup_schedule():
    s = os.servers.get(1234)

    # access via manager
    b = os.backup_schedules.get(server=s)
    assert_isinstance(b, backup_schedules.BackupSchedule)
    os.assert_called('GET', '/servers/1234/backup_schedule')

    b = os.backup_schedules.get(server=1234)
    assert_isinstance(b, backup_schedules.BackupSchedule)
    os.assert_called('GET', '/servers/1234/backup_schedule')

    # access via instance
    assert_isinstance(s.backup_schedule, backup_schedules.BackupSchedule)
    os.assert_called('GET', '/servers/1234/backup_schedule')

    # Just for coverage's sake
    b = s.backup_schedule.get()
    os.assert_called('GET', '/servers/1234/backup_schedule')


def test_create_update_backup_schedule():
    s = os.servers.get(1234)

    # create/update via manager
    os.backup_schedules.update(
        server=s,
        enabled=True,
        weekly=backup_schedules.BACKUP_WEEKLY_THURSDAY,
        daily=backup_schedules.BACKUP_DAILY_H_1000_1200
    )
    os.assert_called('POST', '/servers/1234/backup_schedule')

    # and via instance
    s.backup_schedule.update(enabled=False)
    os.assert_called('POST', '/servers/1234/backup_schedule')


def test_delete_backup_schedule():
    s = os.servers.get(1234)

    # delete via manager
    os.backup_schedules.delete(s)
    os.assert_called('DELETE', '/servers/1234/backup_schedule')
    os.backup_schedules.delete(1234)
    os.assert_called('DELETE', '/servers/1234/backup_schedule')

    # and via instance
    s.backup_schedule.delete()
    os.assert_called('DELETE', '/servers/1234/backup_schedule')

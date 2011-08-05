
from novaclient.v1_0 import backup_schedules
from tests.v1_0 import fakes
from tests import utils


cs = fakes.FakeClient()


class BackupSchedulesTest(utils.TestCase):

    def test_get_backup_schedule(self):
        s = cs.servers.get(1234)

        # access via manager
        b = cs.backup_schedules.get(server=s)
        self.assertTrue(isinstance(b, backup_schedules.BackupSchedule))
        cs.assert_called('GET', '/servers/1234/backup_schedule')

        b = cs.backup_schedules.get(server=1234)
        self.assertTrue(isinstance(b, backup_schedules.BackupSchedule))
        cs.assert_called('GET', '/servers/1234/backup_schedule')

        # access via instance
        self.assertTrue(isinstance(s.backup_schedule,
                                   backup_schedules.BackupSchedule))
        cs.assert_called('GET', '/servers/1234/backup_schedule')

        # Just for coverage's sake
        b = s.backup_schedule.get()
        cs.assert_called('GET', '/servers/1234/backup_schedule')

    def test_create_update_backup_schedule(self):
        s = cs.servers.get(1234)

        # create/update via manager
        cs.backup_schedules.update(
            server=s,
            enabled=True,
            weekly=backup_schedules.BACKUP_WEEKLY_THURSDAY,
            daily=backup_schedules.BACKUP_DAILY_H_1000_1200
        )
        cs.assert_called('POST', '/servers/1234/backup_schedule')

        # and via instance
        s.backup_schedule.update(enabled=False)
        cs.assert_called('POST', '/servers/1234/backup_schedule')

    def test_delete_backup_schedule(self):
        s = cs.servers.get(1234)

        # delete via manager
        cs.backup_schedules.delete(s)
        cs.assert_called('DELETE', '/servers/1234/backup_schedule')
        cs.backup_schedules.delete(1234)
        cs.assert_called('DELETE', '/servers/1234/backup_schedule')

        # and via instance
        s.backup_schedule.delete()
        cs.assert_called('DELETE', '/servers/1234/backup_schedule')

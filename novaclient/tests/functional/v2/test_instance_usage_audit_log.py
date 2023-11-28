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

import datetime

from oslo_utils import timeutils

from novaclient.tests.functional import base


class TestInstanceUsageAuditLogCLI(base.ClientTestBase):
    COMPUTE_API_VERSION = '2.1'

    # NOTE(takashin): By default, 'instance_usage_audit' is False in nova.
    # So the instance usage audit log is not recorded.
    # Therefore an empty result can be got.
    # But it is tested here to call APIs and get responses normally.

    @staticmethod
    def _get_begin_end_time():
        current = timeutils.utcnow()

        end = datetime.datetime(day=1, month=current.month, year=current.year)
        year = end.year

        if current.month == 1:
            year -= 1
            month = 12
        else:
            month = current.month - 1

        begin = datetime.datetime(day=1, month=month, year=year)

        return (begin, end)

    def test_get_os_instance_usage_audit_log(self):
        (begin, end) = self._get_begin_end_time()
        expected = {
            'hosts_not_run': '[]',
            'log': '{}',
            'num_hosts': '0',
            'num_hosts_done': '0',
            'num_hosts_not_run': '0',
            'num_hosts_running': '0',
            'overall_status': 'ALL hosts done. 0 errors.',
            'total_errors': '0',
            'total_instances': '0',
            'period_beginning': str(begin),
            'period_ending': str(end)
        }

        output = self.nova('instance-usage-audit-log')

        for key in expected.keys():
            self.assertEqual(expected[key],
                             self._get_value_from_the_table(output, key))

    def test_get_os_instance_usage_audit_log_with_before(self):
        expected = {
            'hosts_not_run': '[]',
            'log': '{}',
            'num_hosts': '0',
            'num_hosts_done': '0',
            'num_hosts_not_run': '0',
            'num_hosts_running': '0',
            'overall_status': 'ALL hosts done. 0 errors.',
            'total_errors': '0',
            'total_instances': '0',
            'period_beginning': '2016-11-01 00:00:00',
            'period_ending': '2016-12-01 00:00:00'
        }

        output = self.nova(
            'instance-usage-audit-log --before "2016-12-10 13:59:59.999999"')

        for key in expected.keys():
            self.assertEqual(expected[key],
                             self._get_value_from_the_table(output, key))

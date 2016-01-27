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

from novaclient.tests.functional import base


class TestOsServicesNovaClient(base.ClientTestBase):
    """Functional tests for os-services attributes"""

    COMPUTE_API_VERSION = "2.1"

    def test_os_services_list(self):
        table = self.nova('service-list')
        for serv in self.client.services.list():
            self.assertIn(serv.binary, table)

    def test_os_service_disable_enable(self):
        # Disable and enable Nova services in accordance with list of nova
        # services returned by client
        # NOTE(sdague): service disable has the chance in racing
        # with other tests. Now functional tests for novaclient are launched
        # in serial way (https://review.openstack.org/#/c/217768/), but
        # it's a potential issue for making these tests parallel in the future
        for serv in self.client.services.list():
            host = self._get_column_value_from_single_row_table(
                self.nova('service-list --binary %s' % serv.binary), 'Host')
            service = self.nova('service-disable %s %s' % (host, serv.binary))
            self.addCleanup(self.nova, 'service-enable',
                            params="%s %s" % (host, serv.binary))
            status = self._get_column_value_from_single_row_table(
                service, 'Status')
            self.assertEqual('disabled', status)
            service = self.nova('service-enable %s %s' % (host, serv.binary))
            status = self._get_column_value_from_single_row_table(
                service, 'Status')
            self.assertEqual('enabled', status)

    def test_os_service_disable_log_reason(self):
        for serv in self.client.services.list():
            host = self._get_column_value_from_single_row_table(
                self.nova('service-list --binary %s' % serv.binary), 'Host')
            service = self.nova('service-disable --reason test_disable %s %s'
                                % (host, serv.binary))
            self.addCleanup(self.nova, 'service-enable',
                            params="%s %s" % (host, serv.binary))
            status = self._get_column_value_from_single_row_table(
                service, 'Status')
            log_reason = self._get_column_value_from_single_row_table(
                service, 'Disabled Reason')
            self.assertEqual('disabled', status)
            self.assertEqual('test_disable', log_reason)

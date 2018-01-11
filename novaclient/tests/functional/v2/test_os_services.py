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
from novaclient.tests.functional.v2.legacy import test_os_services
from novaclient import utils


class TestOsServicesNovaClientV211(test_os_services.TestOsServicesNovaClient):
    """Functional tests for os-services attributes, microversion 2.11"""

    COMPUTE_API_VERSION = "2.11"

    def test_os_services_force_down_force_up(self):
        for serv in self.client.services.list():
            # In Pike the os-services API was made multi-cell aware and it
            # looks up services by host, which uses the host mapping record
            # in the API DB which is only populated for nova-compute services,
            # effectively making it impossible to perform actions like enable
            # or disable non-nova-compute services since the API won't be able
            # to find them. So filter out anything that's not nova-compute.
            if serv.binary != 'nova-compute':
                continue
            service_list = self.nova('service-list --binary %s' % serv.binary)
            # Check the 'service-list' table has the 'Forced down' column
            status = self._get_column_value_from_single_row_table(
                service_list, 'Forced down')
            self.assertEqual('False', status)

            host = self._get_column_value_from_single_row_table(service_list,
                                                                'Host')
            service = self.nova('service-force-down %s' % host)
            self.addCleanup(self.nova, 'service-force-down --unset',
                            params=host)
            status = self._get_column_value_from_single_row_table(
                service, 'Forced down')
            self.assertEqual('True', status)
            service = self.nova('service-force-down --unset %s' % host)
            status = self._get_column_value_from_single_row_table(
                service, 'Forced down')
            self.assertEqual('False', status)


class TestOsServicesNovaClientV2_53(base.ClientTestBase):
    """Tests the nova service-* commands using the 2.53 microversion.

    The main difference with the 2.53 microversion in these commands is
    the host/binary combination is replaced with the service.id as the
    unique identifier for a service.
    """
    COMPUTE_API_VERSION = "2.53"

    def test_os_services_list(self):
        table = self.nova('service-list')
        for serv in self.client.services.list():
            self.assertIn(serv.binary, table)
            # the id should not be an integer and should be in the table
            self.assertFalse(utils.is_integer_like(serv.id))
            self.assertIn(serv.id, table)

    def test_os_service_disable_enable(self):
        # Disable and enable Nova services in accordance with list of nova
        # services returned by client
        # NOTE(sdague): service disable has the chance in racing
        # with other tests. Now functional tests for novaclient are launched
        # in serial way (https://review.openstack.org/#/c/217768/), but
        # it's a potential issue for making these tests parallel in the future
        for serv in self.client.services.list():
            # In Pike the os-services API was made multi-cell aware and it
            # looks up services by host, which uses the host mapping record
            # in the API DB which is only populated for nova-compute services,
            # effectively making it impossible to perform actions like enable
            # or disable non-nova-compute services since the API won't be able
            # to find them. So filter out anything that's not nova-compute.
            if serv.binary != 'nova-compute':
                continue
            service = self.nova('service-disable %s' % serv.id)
            self.addCleanup(self.nova, 'service-enable', params="%s" % serv.id)
            service_id = self._get_column_value_from_single_row_table(
                service, 'ID')
            self.assertEqual(serv.id, service_id)
            status = self._get_column_value_from_single_row_table(
                service, 'Status')
            self.assertEqual('disabled', status)
            service = self.nova('service-enable %s' % serv.id)
            service_id = self._get_column_value_from_single_row_table(
                service, 'ID')
            self.assertEqual(serv.id, service_id)
            status = self._get_column_value_from_single_row_table(
                service, 'Status')
            self.assertEqual('enabled', status)

    def test_os_service_disable_log_reason(self):
        for serv in self.client.services.list():
            # In Pike the os-services API was made multi-cell aware and it
            # looks up services by host, which uses the host mapping record
            # in the API DB which is only populated for nova-compute services,
            # effectively making it impossible to perform actions like enable
            # or disable non-nova-compute services since the API won't be able
            # to find them. So filter out anything that's not nova-compute.
            if serv.binary != 'nova-compute':
                continue
            service = self.nova('service-disable --reason test_disable %s'
                                % serv.id)
            self.addCleanup(self.nova, 'service-enable', params="%s" % serv.id)
            service_id = self._get_column_value_from_single_row_table(
                service, 'ID')
            self.assertEqual(serv.id, service_id)
            status = self._get_column_value_from_single_row_table(
                service, 'Status')
            log_reason = self._get_column_value_from_single_row_table(
                service, 'Disabled Reason')
            self.assertEqual('disabled', status)
            self.assertEqual('test_disable', log_reason)

    def test_os_services_force_down_force_up(self):
        for serv in self.client.services.list():
            # In Pike the os-services API was made multi-cell aware and it
            # looks up services by host, which uses the host mapping record
            # in the API DB which is only populated for nova-compute services,
            # effectively making it impossible to perform actions like enable
            # or disable non-nova-compute services since the API won't be able
            # to find them. So filter out anything that's not nova-compute.
            if serv.binary != 'nova-compute':
                continue
            service = self.nova('service-force-down %s' % serv.id)
            self.addCleanup(self.nova, 'service-force-down --unset',
                            params="%s" % serv.id)
            service_id = self._get_column_value_from_single_row_table(
                service, 'ID')
            self.assertEqual(serv.id, service_id)
            forced_down = self._get_column_value_from_single_row_table(
                service, 'Forced down')
            self.assertEqual('True', forced_down)
            service = self.nova('service-force-down --unset %s' % serv.id)
            forced_down = self._get_column_value_from_single_row_table(
                service, 'Forced down')
            self.assertEqual('False', forced_down)

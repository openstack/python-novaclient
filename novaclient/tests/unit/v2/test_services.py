# Copyright 2012 IBM Corp.
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

from novaclient import api_versions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import services


class ServicesTest(utils.TestCase):
    api_version = "2.0"

    def setUp(self):
        super(ServicesTest, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion(self.api_version))
        self.service_type = self._get_service_type()

    def _get_service_type(self):
        return services.Service

    def test_list_services(self):
        svs = self.cs.services.list()
        self.assert_request_id(svs, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-services')
        for s in svs:
            self.assertIsInstance(s, self._get_service_type())
            self.assertEqual('nova-compute', s.binary)
            self.assertEqual('host1', s.host)
            self.assertEqual('<Service: %s>' % s.id, str(s))

    def test_list_services_with_hostname(self):
        svs = self.cs.services.list(host='host2')
        self.assert_request_id(svs, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-services?host=host2')
        for s in svs:
            self.assertIsInstance(s, self._get_service_type())
            self.assertEqual('nova-compute', s.binary)
            self.assertEqual('host2', s.host)

    def test_list_services_with_binary(self):
        svs = self.cs.services.list(binary='nova-cert')
        self.assert_request_id(svs, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-services?binary=nova-cert')
        for s in svs:
            self.assertIsInstance(s, self._get_service_type())
            self.assertEqual('nova-cert', s.binary)
            self.assertEqual('host1', s.host)

    def test_list_services_with_host_binary(self):
        svs = self.cs.services.list(host='host2', binary='nova-cert')
        self.assert_request_id(svs, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET',
                              '/os-services?host=host2&binary=nova-cert')
        for s in svs:
            self.assertIsInstance(s, self._get_service_type())
            self.assertEqual('nova-cert', s.binary)
            self.assertEqual('host2', s.host)

    def _update_body(self, host, binary, disabled_reason=None):
        body = {"host": host,
                "binary": binary}
        if disabled_reason is not None:
            body["disabled_reason"] = disabled_reason
        return body

    def test_services_enable(self):
        service = self.cs.services.enable('host1', 'nova-cert')
        self.assert_request_id(service, fakes.FAKE_REQUEST_ID_LIST)
        values = self._update_body("host1", "nova-cert")
        self.cs.assert_called('PUT', '/os-services/enable', values)
        self.assertIsInstance(service, self._get_service_type())
        self.assertEqual('enabled', service.status)

    def test_services_delete(self):
        ret = self.cs.services.delete('1')
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('DELETE', '/os-services/1')

    def test_services_disable(self):
        service = self.cs.services.disable('host1', 'nova-cert')
        self.assert_request_id(service, fakes.FAKE_REQUEST_ID_LIST)
        values = self._update_body("host1", "nova-cert")
        self.cs.assert_called('PUT', '/os-services/disable', values)
        self.assertIsInstance(service, self._get_service_type())
        self.assertEqual('disabled', service.status)

    def test_services_disable_log_reason(self):
        service = self.cs.services.disable_log_reason(
            'compute1', 'nova-compute', 'disable bad host')
        self.assert_request_id(service, fakes.FAKE_REQUEST_ID_LIST)
        values = self._update_body("compute1", "nova-compute",
                                   "disable bad host")
        self.cs.assert_called('PUT', '/os-services/disable-log-reason', values)
        self.assertIsInstance(service, self._get_service_type())
        self.assertEqual('disabled', service.status)


class ServicesV211TestCase(ServicesTest):
    api_version = "2.11"

    def _update_body(self, host, binary, disabled_reason=None,
                     force_down=None):
        body = {"host": host,
                "binary": binary}
        if disabled_reason is not None:
            body["disabled_reason"] = disabled_reason
        if force_down is not None:
            body["forced_down"] = force_down
        return body

    def test_services_force_down(self):
        service = self.cs.services.force_down(
            'compute1', 'nova-compute', False)
        self.assert_request_id(service, fakes.FAKE_REQUEST_ID_LIST)
        values = self._update_body("compute1", "nova-compute",
                                   force_down=False)
        self.cs.assert_called('PUT', '/os-services/force-down', values)
        self.assertIsInstance(service, self._get_service_type())
        self.assertFalse(service.forced_down)


class ServicesV2_53TestCase(ServicesV211TestCase):
    api_version = "2.53"

    def _update_body(self, status=None, disabled_reason=None, force_down=None):
        body = {}
        if status is not None:
            body['status'] = status
        if disabled_reason is not None:
            body['disabled_reason'] = disabled_reason
        if force_down is not None:
            body['forced_down'] = force_down
        return body

    def test_services_enable(self):
        service = self.cs.services.enable(fakes.FAKE_SERVICE_UUID_1)
        self.assert_request_id(service, fakes.FAKE_REQUEST_ID_LIST)
        values = self._update_body(status='enabled')
        self.cs.assert_called(
            'PUT', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1, values)
        self.assertIsInstance(service, self._get_service_type())
        self.assertEqual('enabled', service.status)

    def test_services_delete(self):
        ret = self.cs.services.delete(fakes.FAKE_SERVICE_UUID_1)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('DELETE',
                              '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1)

    def test_services_disable(self):
        service = self.cs.services.disable(fakes.FAKE_SERVICE_UUID_1)
        self.assert_request_id(service, fakes.FAKE_REQUEST_ID_LIST)
        values = self._update_body(status='disabled')
        self.cs.assert_called(
            'PUT', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1, values)
        self.assertIsInstance(service, self._get_service_type())
        self.assertEqual('disabled', service.status)

    def test_services_disable_log_reason(self):
        service = self.cs.services.disable_log_reason(
            fakes.FAKE_SERVICE_UUID_1, 'disable bad host')
        self.assert_request_id(service, fakes.FAKE_REQUEST_ID_LIST)
        values = self._update_body(status='disabled',
                                   disabled_reason='disable bad host')
        self.cs.assert_called(
            'PUT', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1, values)
        self.assertIsInstance(service, self._get_service_type())
        self.assertEqual('disabled', service.status)
        self.assertEqual('disable bad host', service.disabled_reason)

    def test_services_force_down(self):
        service = self.cs.services.force_down(
            fakes.FAKE_SERVICE_UUID_1, False)
        self.assert_request_id(service, fakes.FAKE_REQUEST_ID_LIST)
        values = self._update_body(force_down=False)
        self.cs.assert_called(
            'PUT', '/os-services/%s' % fakes.FAKE_SERVICE_UUID_1, values)
        self.assertIsInstance(service, self._get_service_type())
        self.assertFalse(service.forced_down)

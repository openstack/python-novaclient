# Copyright 2012 OpenStack Foundation
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
from novaclient import exceptions
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import hypervisors as data
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes


class HypervisorsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.V1

    def compare_to_expected(self, expected, hyper):
        for key, value in expected.items():
            self.assertEqual(getattr(hyper, key), value)

    def test_hypervisor_index(self):
        expected = [
            dict(id=self.data_fixture.hyper_id_1,
                 hypervisor_hostname='hyper1'),
            dict(id=self.data_fixture.hyper_id_2,
                 hypervisor_hostname='hyper2')]

        result = self.cs.hypervisors.list(False)
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-hypervisors')

        for idx, hyper in enumerate(result):
            self.compare_to_expected(expected[idx], hyper)

    def test_hypervisor_detail(self):
        expected = [
            dict(id=self.data_fixture.hyper_id_1,
                 service=dict(id=self.data_fixture.service_id_1,
                              host='compute1'),
                 vcpus=4,
                 memory_mb=10 * 1024,
                 local_gb=250,
                 vcpus_used=2,
                 memory_mb_used=5 * 1024,
                 local_gb_used=125,
                 hypervisor_type="xen",
                 hypervisor_version=3,
                 hypervisor_hostname="hyper1",
                 free_ram_mb=5 * 1024,
                 free_disk_gb=125,
                 current_workload=2,
                 running_vms=2,
                 cpu_info='cpu_info',
                 disk_available_least=100,
                 state='up',
                 status='enabled'),
            dict(id=self.data_fixture.hyper_id_2,
                 service=dict(id=self.data_fixture.service_id_2,
                              host="compute2"),
                 vcpus=4,
                 memory_mb=10 * 1024,
                 local_gb=250,
                 vcpus_used=2,
                 memory_mb_used=5 * 1024,
                 local_gb_used=125,
                 hypervisor_type="xen",
                 hypervisor_version=3,
                 hypervisor_hostname="hyper2",
                 free_ram_mb=5 * 1024,
                 free_disk_gb=125,
                 current_workload=2,
                 running_vms=2,
                 cpu_info='cpu_info',
                 disk_available_least=100,
                 state='up',
                 status='enabled')]

        if self.cs.api_version >= api_versions.APIVersion('2.88'):
            for hypervisor in expected:
                del hypervisor['current_workload']
                del hypervisor['disk_available_least']
                del hypervisor['free_ram_mb']
                del hypervisor['free_disk_gb']
                del hypervisor['local_gb']
                del hypervisor['local_gb_used']
                del hypervisor['memory_mb']
                del hypervisor['memory_mb_used']
                del hypervisor['running_vms']
                del hypervisor['vcpus']
                del hypervisor['vcpus_used']
                hypervisor['uptime'] = 'fake uptime'

        result = self.cs.hypervisors.list()
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-hypervisors/detail')

        for idx, hyper in enumerate(result):
            self.compare_to_expected(expected[idx], hyper)

    def test_hypervisor_search(self):
        expected = [
            dict(id=self.data_fixture.hyper_id_1,
                 hypervisor_hostname='hyper1',
                 state='up',
                 status='enabled'),
            dict(id=self.data_fixture.hyper_id_2,
                 hypervisor_hostname='hyper2',
                 state='up',
                 status='enabled')]

        result = self.cs.hypervisors.search('hyper')
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        if self.cs.api_version >= api_versions.APIVersion('2.53'):
            self.assert_called(
                'GET', '/os-hypervisors?hypervisor_hostname_pattern=hyper')
        else:
            self.assert_called('GET', '/os-hypervisors/hyper/search')

        for idx, hyper in enumerate(result):
            self.compare_to_expected(expected[idx], hyper)

    def test_hypervisor_search_unicode(self):
        hypervisor_match = '\\u5de5\\u4f5c'
        if self.cs.api_version >= api_versions.APIVersion('2.53'):
            self.assertRaises(exceptions.BadRequest,
                              self.cs.hypervisors.search,
                              hypervisor_match)
        else:
            self.assertRaises(exceptions.NotFound,
                              self.cs.hypervisors.search,
                              hypervisor_match)

    def test_hypervisor_search_detailed(self):
        # detailed=True is not supported before 2.53
        ex = self.assertRaises(exceptions.UnsupportedVersion,
                               self.cs.hypervisors.search, 'hyper',
                               detailed=True)
        self.assertIn('Parameter "detailed" requires API version 2.53 or '
                      'greater.', str(ex))

    def test_hypervisor_servers(self):
        expected = [
            dict(id=self.data_fixture.hyper_id_1,
                 hypervisor_hostname='hyper1',
                 state='up',
                 status='enabled',
                 servers=[
                     dict(name='inst1', uuid='uuid1'),
                     dict(name='inst2', uuid='uuid2')]),
            dict(id=self.data_fixture.hyper_id_2,
                 hypervisor_hostname='hyper2',
                 state='up',
                 status='enabled',
                 servers=[
                     dict(name='inst3', uuid='uuid3'),
                     dict(name='inst4', uuid='uuid4')]),
        ]

        result = self.cs.hypervisors.search('hyper', True)
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        if self.cs.api_version >= api_versions.APIVersion('2.53'):
            self.assert_called(
                'GET', '/os-hypervisors?hypervisor_hostname_pattern=hyper&'
                       'with_servers=True')
        else:
            self.assert_called('GET', '/os-hypervisors/hyper/servers')

        for idx, hyper in enumerate(result):
            self.compare_to_expected(expected[idx], hyper)

    def test_hypervisor_get(self):
        expected = dict(
            id=self.data_fixture.hyper_id_1,
            service=dict(id=self.data_fixture.service_id_1, host='compute1'),
            vcpus=4,
            memory_mb=10 * 1024,
            local_gb=250,
            vcpus_used=2,
            memory_mb_used=5 * 1024,
            local_gb_used=125,
            hypervisor_type="xen",
            hypervisor_version=3,
            hypervisor_hostname="hyper1",
            free_ram_mb=5 * 1024,
            free_disk_gb=125,
            current_workload=2,
            running_vms=2,
            cpu_info='cpu_info',
            disk_available_least=100,
            state='up',
            status='enabled')

        if self.cs.api_version >= api_versions.APIVersion('2.88'):
            del expected['current_workload']
            del expected['disk_available_least']
            del expected['free_ram_mb']
            del expected['free_disk_gb']
            del expected['local_gb']
            del expected['local_gb_used']
            del expected['memory_mb']
            del expected['memory_mb_used']
            del expected['running_vms']
            del expected['vcpus']
            del expected['vcpus_used']
            expected['uptime'] = 'fake uptime'

        result = self.cs.hypervisors.get(self.data_fixture.hyper_id_1)
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called(
            'GET', '/os-hypervisors/%s' % self.data_fixture.hyper_id_1)

        self.compare_to_expected(expected, result)

    def test_hypervisor_uptime(self):
        expected = dict(
            id=self.data_fixture.hyper_id_1,
            hypervisor_hostname="hyper1",
            uptime="fake uptime",
            state='up',
            status='enabled')

        result = self.cs.hypervisors.uptime(self.data_fixture.hyper_id_1)
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called(
            'GET', '/os-hypervisors/%s/uptime' % self.data_fixture.hyper_id_1)

        self.compare_to_expected(expected, result)

    def test_hypervisor_statistics(self):
        expected = dict(
            count=2,
            vcpus=8,
            memory_mb=20 * 1024,
            local_gb=500,
            vcpus_used=4,
            memory_mb_used=10 * 1024,
            local_gb_used=250,
            free_ram_mb=10 * 1024,
            free_disk_gb=250,
            current_workload=4,
            running_vms=4,
            disk_available_least=200,
        )

        result = self.cs.hypervisors.statistics()
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-hypervisors/statistics')

        self.compare_to_expected(expected, result)

        # Test for Bug #1370415, the line below used to raise AttributeError
        self.assertEqual("<HypervisorStats: 2 Hypervisors>",
                         result.__repr__())


class HypervisorsV233Test(HypervisorsTest):
    def setUp(self):
        super(HypervisorsV233Test, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.33")

    def test_use_limit_marker_params(self):
        params = {'limit': '10', 'marker': 'fake-marker'}
        self.cs.hypervisors.list(**params)
        for k, v in params.items():
            self.assertEqual([v], self.requests_mock.last_request.qs[k])


class HypervisorsV253Test(HypervisorsV233Test):
    """Tests the os-hypervisors 2.53 API bindings."""
    data_fixture_class = data.V253

    def setUp(self):
        super(HypervisorsV253Test, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.53")

    def test_hypervisor_search_detailed(self):
        expected = [
            dict(id=self.data_fixture.hyper_id_1,
                 state='up',
                 status='enabled',
                 hypervisor_hostname='hyper1'),
            dict(id=self.data_fixture.hyper_id_2,
                 state='up',
                 status='enabled',
                 hypervisor_hostname='hyper2')]
        result = self.cs.hypervisors.search('hyper', detailed=True)
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called(
            'GET', '/os-hypervisors/detail?hypervisor_hostname_pattern=hyper')
        for idx, hyper in enumerate(result):
            self.compare_to_expected(expected[idx], hyper)


class HypervisorsV288Test(HypervisorsV253Test):
    data_fixture_class = data.V288

    def setUp(self):
        super().setUp()
        self.cs.api_version = api_versions.APIVersion('2.88')

    def test_hypervisor_uptime(self):
        expected = {
            'id': self.data_fixture.hyper_id_1,
            'hypervisor_hostname': 'hyper1',
            'uptime': 'fake uptime',
            'state': 'up',
            'status': 'enabled',
        }

        result = self.cs.hypervisors.uptime(self.data_fixture.hyper_id_1)
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called(
            'GET', '/os-hypervisors/%s' % self.data_fixture.hyper_id_1)

        self.compare_to_expected(expected, result)

    def test_hypervisor_statistics(self):
        exc = self.assertRaises(
            exceptions.UnsupportedVersion,
            self.cs.hypervisor_stats.statistics)
        self.assertIn(
            "The 'statistics' API is removed in API version 2.88 or later.",
            str(exc))

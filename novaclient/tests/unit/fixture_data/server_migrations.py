# Copyright 2016 OpenStack Foundation
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

from novaclient.tests.unit.fixture_data import base


class Fixture(base.Fixture):
    base_url = 'servers'

    def setUp(self):
        super(Fixture, self).setUp()
        url = self.url('1234', 'migrations', '1', 'action')
        self.requests_mock.post(url,
                                status_code=202,
                                headers=self.json_headers)

        get_migrations = {'migrations': [
            {
                "created_at": "2016-01-29T13:42:02.000000",
                "dest_compute": "compute2",
                "dest_host": "1.2.3.4",
                "dest_node": "node2",
                "id": 1,
                "server_uuid": "4cfba335-03d8-49b2-8c52-e69043d1e8fe",
                "source_compute": "compute1",
                "source_node": "node1",
                "status": "running",
                "memory_total_bytes": 123456,
                "memory_processed_bytes": 12345,
                "memory_remaining_bytes": 120000,
                "disk_total_bytes": 234567,
                "disk_processed_bytes": 23456,
                "disk_remaining_bytes": 230000,
                "updated_at": "2016-01-29T13:42:02.000000"
            }]}

        url = self.url('1234', 'migrations')
        self.requests_mock.get(url,
                               json=get_migrations,
                               headers=self.json_headers)

        get_migration = {'migration': {
            "created_at": "2016-01-29T13:42:02.000000",
            "dest_compute": "compute2",
            "dest_host": "1.2.3.4",
            "dest_node": "node2",
            "id": 1,
            "server_uuid": "4cfba335-03d8-49b2-8c52-e69043d1e8fe",
            "source_compute": "compute1",
            "source_node": "node1",
            "status": "running",
            "memory_total_bytes": 123456,
            "memory_processed_bytes": 12345,
            "memory_remaining_bytes": 120000,
            "disk_total_bytes": 234567,
            "disk_processed_bytes": 23456,
            "disk_remaining_bytes": 230000,
            "updated_at": "2016-01-29T13:42:02.000000"
        }}

        url = self.url('1234', 'migrations', '1')
        self.requests_mock.get(url,
                               json=get_migration,
                               headers=self.json_headers)
        url = self.url('1234', 'migrations', '1')
        self.requests_mock.delete(url,
                                  status_code=202,
                                  headers=self.json_headers)

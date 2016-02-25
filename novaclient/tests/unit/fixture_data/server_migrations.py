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
        self.requests.register_uri('POST', url,
                                   status_code=202,
                                   headers=self.json_headers)

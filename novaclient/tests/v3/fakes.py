# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from novaclient.v3 import client
from novaclient.tests import fakes
from novaclient.tests.v1_1 import fakes as fakes_v1_1


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(fakes_v1_1.FakeHTTPClient):
    #
    # Hosts
    #
    def put_os_hosts_sample_host_1(self, body, **kw):
        return (200, {}, {'host': {'host': 'sample-host_1',
                      'status': 'enabled'}})

    def put_os_hosts_sample_host_2(self, body, **kw):
        return (200, {}, {'host': {'host': 'sample-host_2',
                      'maintenance_mode': 'on_maintenance'}})

    def put_os_hosts_sample_host_3(self, body, **kw):
        return (200, {}, {'host': {'host': 'sample-host_3',
                      'status': 'enabled',
                      'maintenance_mode': 'on_maintenance'}})

    def get_os_hosts_sample_host_reboot(self, **kw):
        return (200, {}, {'host': {'host': 'sample_host',
                          'power_action': 'reboot'}})

    def get_os_hosts_sample_host_startup(self, **kw):
        return (200, {}, {'host': {'host': 'sample_host',
                          'power_action': 'startup'}})

    def get_os_hosts_sample_host_shutdown(self, **kw):
        return (200, {}, {'host': {'host': 'sample_host',
                          'power_action': 'shutdown'}})

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

from novaclient.openstack.common import strutils
from novaclient.tests import fakes
from novaclient.tests.v1_1 import fakes as fakes_v1_1
from novaclient.v3 import client


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

    #
    # Flavors
    #
    post_flavors_1_flavor_extra_specs = (
        fakes_v1_1.FakeHTTPClient.post_flavors_1_os_extra_specs)

    delete_flavors_1_flavor_extra_specs_k1 = (
        fakes_v1_1.FakeHTTPClient.delete_flavors_1_os_extra_specs_k1)

    def get_flavors_detail(self, **kw):
        flavors = {'flavors': [
            {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10,
             'ephemeral': 10,
             'flavor-access:is_public': True,
             'links': {}},
            {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20,
             'ephemeral': 20,
             'flavor-access:is_public': False,
             'links': {}},
            {'id': 'aa1', 'name': '128 MB Server', 'ram': 128, 'disk': 0,
             'ephemeral': 0,
             'flavor-access:is_public': True,
             'links': {}}
        ]}

        if 'is_public' not in kw:
            filter_is_public = True
        else:
            if kw['is_public'].lower() == 'none':
                filter_is_public = None
            else:
                filter_is_public = strutils.bool_from_string(kw['is_public'],
                                                             True)

        if filter_is_public is not None:
            if filter_is_public:
                flavors['flavors'] = [
                        v for v in flavors['flavors']
                            if v['flavor-access:is_public']
                        ]
            else:
                flavors['flavors'] = [
                        v for v in flavors['flavors']
                            if not v['flavor-access:is_public']
                        ]

        return (200, {}, flavors)

    #
    # Flavor access
    #
    get_flavors_2_flavor_access = (
        fakes_v1_1.FakeHTTPClient.get_flavors_2_os_flavor_access)

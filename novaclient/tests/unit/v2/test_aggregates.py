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
from novaclient.tests.unit.fixture_data import aggregates as data
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import aggregates
from novaclient.v2 import images


class AggregatesTest(utils.FixturedTestCase):

    data_fixture_class = data.Fixture

    scenarios = [('original', {'client_fixture_class': client.V1}),
                 ('session', {'client_fixture_class': client.SessionV1})]

    def test_list_aggregates(self):
        result = self.cs.aggregates.list()
        self.assert_request_id(result, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-aggregates')
        for aggregate in result:
            self.assertIsInstance(aggregate, aggregates.Aggregate)

    def test_create_aggregate(self):
        body = {"aggregate": {"name": "test", "availability_zone": "nova1"}}
        aggregate = self.cs.aggregates.create("test", "nova1")
        self.assert_request_id(aggregate, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates', body)
        self.assertIsInstance(aggregate, aggregates.Aggregate)

    def test_get(self):
        aggregate = self.cs.aggregates.get("1")
        self.assert_request_id(aggregate, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-aggregates/1')
        self.assertIsInstance(aggregate, aggregates.Aggregate)

        aggregate2 = self.cs.aggregates.get(aggregate)
        self.assert_request_id(aggregate2, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-aggregates/1')
        self.assertIsInstance(aggregate2, aggregates.Aggregate)

    def test_get_details(self):
        aggregate = self.cs.aggregates.get_details("1")
        self.assert_request_id(aggregate, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-aggregates/1')
        self.assertIsInstance(aggregate, aggregates.Aggregate)

        aggregate2 = self.cs.aggregates.get_details(aggregate)
        self.assert_request_id(aggregate2, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('GET', '/os-aggregates/1')
        self.assertIsInstance(aggregate2, aggregates.Aggregate)

    def test_update(self):
        aggregate = self.cs.aggregates.get("1")
        values = {"name": "foo"}
        body = {"aggregate": values}

        result1 = aggregate.update(values)
        self.assert_request_id(result1, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/os-aggregates/1', body)
        self.assertIsInstance(result1, aggregates.Aggregate)

        result2 = self.cs.aggregates.update(2, values)
        self.assert_request_id(result2, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/os-aggregates/2', body)
        self.assertIsInstance(result2, aggregates.Aggregate)

    def test_update_with_availability_zone(self):
        aggregate = self.cs.aggregates.get("1")
        values = {"name": "foo", "availability_zone": "new_zone"}
        body = {"aggregate": values}

        result3 = self.cs.aggregates.update(aggregate, values)
        self.assert_request_id(result3, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('PUT', '/os-aggregates/1', body)
        self.assertIsInstance(result3, aggregates.Aggregate)

    def test_add_host(self):
        aggregate = self.cs.aggregates.get("1")
        host = "host1"
        body = {"add_host": {"host": "host1"}}

        result1 = aggregate.add_host(host)
        self.assert_request_id(result1, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/1/action', body)
        self.assertIsInstance(result1, aggregates.Aggregate)

        result2 = self.cs.aggregates.add_host("2", host)
        self.assert_request_id(result2, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/2/action', body)
        self.assertIsInstance(result2, aggregates.Aggregate)

        result3 = self.cs.aggregates.add_host(aggregate, host)
        self.assert_request_id(result3, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/1/action', body)
        self.assertIsInstance(result3, aggregates.Aggregate)

    def test_remove_host(self):
        aggregate = self.cs.aggregates.get("1")
        host = "host1"
        body = {"remove_host": {"host": "host1"}}

        result1 = aggregate.remove_host(host)
        self.assert_request_id(result1, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/1/action', body)
        self.assertIsInstance(result1, aggregates.Aggregate)

        result2 = self.cs.aggregates.remove_host("2", host)
        self.assert_request_id(result2, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/2/action', body)
        self.assertIsInstance(result2, aggregates.Aggregate)

        result3 = self.cs.aggregates.remove_host(aggregate, host)
        self.assert_request_id(result3, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/1/action', body)
        self.assertIsInstance(result3, aggregates.Aggregate)

    def test_set_metadata(self):
        aggregate = self.cs.aggregates.get("1")
        metadata = {"foo": "bar"}
        body = {"set_metadata": {"metadata": metadata}}

        result1 = aggregate.set_metadata(metadata)
        self.assert_request_id(result1, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/1/action', body)
        self.assertIsInstance(result1, aggregates.Aggregate)

        result2 = self.cs.aggregates.set_metadata(2, metadata)
        self.assert_request_id(result2, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/2/action', body)
        self.assertIsInstance(result2, aggregates.Aggregate)

        result3 = self.cs.aggregates.set_metadata(aggregate, metadata)
        self.assert_request_id(result3, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('POST', '/os-aggregates/1/action', body)
        self.assertIsInstance(result3, aggregates.Aggregate)

    def test_delete_aggregate(self):
        aggregate = self.cs.aggregates.list()[0]
        result1 = aggregate.delete()
        self.assert_request_id(result1, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/os-aggregates/1')

        result2 = self.cs.aggregates.delete('1')
        self.assert_request_id(result2, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/os-aggregates/1')

        result3 = self.cs.aggregates.delete(aggregate)
        self.assert_request_id(result3, fakes.FAKE_REQUEST_ID_LIST)
        self.assert_called('DELETE', '/os-aggregates/1')


class AggregatesV281Test(utils.FixturedTestCase):
    api_version = "2.81"
    data_fixture_class = data.Fixture

    scenarios = [('original', {'client_fixture_class': client.V1}),
                 ('session', {'client_fixture_class': client.SessionV1})]

    def setUp(self):
        super(AggregatesV281Test, self).setUp()
        self.cs.api_version = api_versions.APIVersion(self.api_version)

    def test_cache_images(self):
        aggregate = self.cs.aggregates.list()[0]
        _images = [images.Image(self.cs.aggregates, {'id': '1'}),
                   images.Image(self.cs.aggregates, {'id': '2'})]
        aggregate.cache_images(_images)
        expected_body = {'cache': [{'id': image.id}
                                   for image in _images]}
        self.assert_called('POST', '/os-aggregates/1/images',
                           expected_body)

    def test_cache_images_just_ids(self):
        aggregate = self.cs.aggregates.list()[0]
        _images = ['1']
        aggregate.cache_images(_images)
        expected_body = {'cache': [{'id': '1'}]}
        self.assert_called('POST', '/os-aggregates/1/images',
                           expected_body)

    def test_cache_images_pre281(self):
        self.cs.api_version = api_versions.APIVersion('2.80')
        aggregate = self.cs.aggregates.list()[0]
        _images = [images.Image(self.cs.aggregates, {'id': '1'})]
        self.assertRaises(exceptions.VersionNotFoundForAPIMethod,
                          aggregate.cache_images, _images)

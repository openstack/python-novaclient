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

import copy

from keystoneauth1 import session
import mock
from oslo_utils import uuidutils

import novaclient.api_versions
import novaclient.client
import novaclient.extension
from novaclient.tests.unit import utils
import novaclient.v2.client


class ClientTest(utils.TestCase):
    def test_get_client_class_v2(self):
        output = novaclient.client.get_client_class('2')
        self.assertEqual(output, novaclient.v2.client.Client)

    def test_get_client_class_v2_int(self):
        output = novaclient.client.get_client_class(2)
        self.assertEqual(output, novaclient.v2.client.Client)

    def test_get_client_class_unknown(self):
        self.assertRaises(novaclient.exceptions.UnsupportedVersion,
                          novaclient.client.get_client_class, '0')

    def test_get_client_class_latest(self):
        self.assertRaises(novaclient.exceptions.UnsupportedVersion,
                          novaclient.client.get_client_class, 'latest')
        self.assertRaises(novaclient.exceptions.UnsupportedVersion,
                          novaclient.client.get_client_class, '2.latest')


class SessionClientTest(utils.TestCase):

    def test_timings(self):
        self.requests_mock.get('http://no.where')

        client = novaclient.client.SessionClient(session=session.Session())
        client.request("http://no.where", 'GET')
        self.assertEqual(0, len(client.times))

        client = novaclient.client.SessionClient(session=session.Session(),
                                                 timings=True)
        client.request("http://no.where", 'GET')
        self.assertEqual(1, len(client.times))
        self.assertEqual('GET http://no.where', client.times[0][0])

    def test_client_get_reset_timings_v2(self):
        cs = novaclient.client.SessionClient(session=session.Session())
        self.assertEqual(0, len(cs.get_timings()))
        cs.times.append("somevalue")
        self.assertEqual(1, len(cs.get_timings()))
        self.assertEqual("somevalue", cs.get_timings()[0])

        cs.reset_timings()
        self.assertEqual(0, len(cs.get_timings()))

    def test_global_id(self):
        global_id = "req-%s" % uuidutils.generate_uuid()
        self.requests_mock.get('http://no.where')

        client = novaclient.client.SessionClient(session=session.Session(),
                                                 global_request_id=global_id)
        client.request("http://no.where", 'GET')
        headers = self.requests_mock.last_request.headers
        self.assertEqual(headers['X-OpenStack-Request-ID'], global_id)


class ClientsUtilsTest(utils.TestCase):

    @mock.patch("novaclient.client._discover_via_entry_points")
    @mock.patch("novaclient.client._discover_via_python_path")
    @mock.patch("novaclient.extension.Extension")
    def test_discover_extensions_all(self, mock_extension,
                                     mock_discover_via_python_path,
                                     mock_discover_via_entry_points):
        def make_gen(start, end):
            def f(*args, **kwargs):
                for i in range(start, end):
                    yield "name-%s" % i, i
            return f

        mock_discover_via_python_path.side_effect = make_gen(0, 3)
        mock_discover_via_entry_points.side_effect = make_gen(3, 4)

        version = novaclient.api_versions.APIVersion("2.0")

        result = novaclient.client.discover_extensions(version)

        self.assertEqual([mock.call("name-%s" % i, i) for i in range(0, 4)],
                         mock_extension.call_args_list)
        mock_discover_via_python_path.assert_called_once_with()
        mock_discover_via_entry_points.assert_called_once_with()
        self.assertEqual([mock_extension()] * 4, result)

    @mock.patch("novaclient.client.warnings")
    def test__check_arguments(self, mock_warnings):
        release = "Coolest"

        # no reference
        novaclient.client._check_arguments({}, release=release,
                                           deprecated_name="foo")
        self.assertFalse(mock_warnings.warn.called)
        novaclient.client._check_arguments({}, release=release,
                                           deprecated_name="foo",
                                           right_name="bar")
        self.assertFalse(mock_warnings.warn.called)

        # with alternative
        original_kwargs = {"foo": "text"}
        actual_kwargs = copy.copy(original_kwargs)
        self.assertEqual(original_kwargs, actual_kwargs)
        novaclient.client._check_arguments(actual_kwargs, release=release,
                                           deprecated_name="foo",
                                           right_name="bar")
        self.assertNotEqual(original_kwargs, actual_kwargs)
        self.assertEqual({"bar": original_kwargs["foo"]}, actual_kwargs)
        self.assertTrue(mock_warnings.warn.called)

        mock_warnings.warn.reset_mock()

        # without alternative
        original_kwargs = {"foo": "text"}
        actual_kwargs = copy.copy(original_kwargs)
        self.assertEqual(original_kwargs, actual_kwargs)
        novaclient.client._check_arguments(actual_kwargs, release=release,
                                           deprecated_name="foo")
        self.assertNotEqual(original_kwargs, actual_kwargs)
        self.assertEqual({}, actual_kwargs)
        self.assertTrue(mock_warnings.warn.called)

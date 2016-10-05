# Copyright 2016 IBM Corp.
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

from novaclient import exceptions
from novaclient.tests.unit import utils as test_utils


class ExceptionsTestCase(test_utils.TestCase):

    def _test_from_response(self, body, expected_message):
        data = {
            'status_code': 404,
            'headers': {
                'content-type': 'application/json',
                'x-openstack-request-id': (
                    'req-d9df03b0-4150-4b53-8157-7560ccf39f75'),
            }
        }
        response = test_utils.TestResponse(data)
        fake_url = 'http://localhost:8774/v2.1/fake/flavors/test'
        error = exceptions.from_response(response, body, fake_url, 'GET')
        self.assertIsInstance(error, exceptions.NotFound)
        self.assertEqual(expected_message, error.message)

    def test_from_response_webob_pre_1_6_0(self):
        # Tests error responses before webob 1.6.0 where the error details
        # are nested in the response body.
        message = "Flavor test could not be found."
        self._test_from_response(
            {"itemNotFound": {"message": message, "code": 404}},
            message)

    def test_from_response_webob_post_1_6_0(self):
        # Tests error responses from webob 1.6.0 where the error details
        # are in the response body.
        message = "Flavor test could not be found."
        self._test_from_response({"message": message, "code": 404}, message)

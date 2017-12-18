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

import time

from oslo_utils import timeutils
from oslo_utils import uuidutils
import six
from tempest.lib import exceptions

from novaclient.tests.functional import base


class TestInstanceActionCLI(base.ClientTestBase):

    COMPUTE_API_VERSION = "2.21"

    def _test_cmd_with_not_existing_instance(self, cmd, args):
        try:
            self.nova("%s %s" % (cmd, args))
        except exceptions.CommandFailed as e:
            self.assertIn("ERROR (NotFound):", six.text_type(e))
        else:
            self.fail("%s is not failed on non existing instance." % cmd)

    def test_show_action_with_not_existing_instance(self):
        name_or_uuid = uuidutils.generate_uuid()
        request_id = uuidutils.generate_uuid()
        self._test_cmd_with_not_existing_instance(
            "instance-action", "%s %s" % (name_or_uuid, request_id))

    def test_list_actions_with_not_existing_instance(self):
        name_or_uuid = uuidutils.generate_uuid()
        self._test_cmd_with_not_existing_instance("instance-action-list",
                                                  name_or_uuid)

    def test_show_and_list_actions_on_deleted_instance(self):
        server = self._create_server(add_cleanup=False)
        server.delete()
        self.wait_for_resource_delete(server, self.client.servers)

        output = self.nova("instance-action-list %s" % server.id)
        # NOTE(andreykurilin): output is not a single row table, so we can
        #   obtain just "create" action. It should be enough for testing
        #   "nova instance-action <server> <request-id>" command
        request_id = self._get_column_value_from_single_row_table(
            output, "Request_ID")

        output = self.nova("instance-action %s %s" % (server.id, request_id))

        # ensure that obtained action is "create".
        self.assertEqual("create",
                         self._get_value_from_the_table(output, "action"))


class TestInstanceActionCLIV258(TestInstanceActionCLI):
    """Instance action functional tests for v2.58 nova-api microversion."""

    COMPUTE_API_VERSION = "2.58"

    def test_list_instance_action_with_marker_and_limit(self):
        server = self._create_server()
        server.stop()
        # The actions are sorted by created_at in descending order,
        # and now we have two actions: create and stop.
        output = self.nova("instance-action-list %s --limit 1" % server.id)
        marker_req = self._get_column_value_from_single_row_table(
            output, "Request_ID")
        action = self._get_list_of_values_from_single_column_table(
            output, "Action")
        # The stop action was most recently created so it's what
        # we get back when limit=1.
        self.assertEqual(action, ['stop'])

        output = self.nova("instance-action-list %s --limit 1 "
                           "--marker %s" % (server.id, marker_req))
        action = self._get_list_of_values_from_single_column_table(
            output, "Action")
        self.assertEqual(action, ['create'])

    def test_list_instance_action_with_changes_since(self):
        # Ignore microseconds to make this a deterministic test.
        before_create = timeutils.utcnow().replace(microsecond=0).isoformat()
        server = self._create_server()
        time.sleep(2)
        before_stop = timeutils.utcnow().replace(microsecond=0).isoformat()
        server.stop()

        create_output = self.nova(
            "instance-action-list %s --changes-since %s" %
            (server.id, before_create))
        action = self._get_list_of_values_from_single_column_table(
            create_output, "Action")
        # The actions are sorted by created_at in descending order.
        self.assertEqual(action, ['create', 'stop'])

        stop_output = self.nova("instance-action-list %s --changes-since %s" %
                                (server.id, before_stop))
        action = self._get_list_of_values_from_single_column_table(
            stop_output, "Action")
        # Provide detailed debug information if this fails.
        self.assertEqual(action, ['stop'],
                         'Expected to find the stop action with '
                         '--changes-since=%s but got: %s\n\n'
                         'First instance-action-list output: %s' %
                         (before_stop, stop_output, create_output))

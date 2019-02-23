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
    # Does this microversion return a hostId field in the event response?
    expect_event_hostId_field = False

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
        if not self.expect_event_hostId_field:
            # Make sure host and hostId are not in the response when
            # microversion is less than 2.62.
            output = self.nova("instance-action %s %s" % (
                server.id, marker_req))
            self.assertNotIn("'host'", output)
            self.assertNotIn("'hostId'", output)

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


class TestInstanceActionCLIV262(TestInstanceActionCLIV258,
                                base.TenantTestBase):
    """Instance action functional tests for v2.62 nova-api microversion."""

    COMPUTE_API_VERSION = "2.62"
    expect_event_hostId_field = True

    def test_show_actions_with_host(self):
        name = self.name_generate()
        # Create server with non-admin user
        server = self.another_nova('boot --flavor %s --image %s --poll %s' %
                                   (self.flavor.name, self.image.name, name))
        server_id = self._get_value_from_the_table(server, 'id')
        output = self.nova("instance-action-list %s" % server_id)
        request_id = self._get_column_value_from_single_row_table(
            output, "Request_ID")

        # Only the 'hostId' are exposed to non-admin
        output = self.another_nova(
            "instance-action %s %s" % (server_id, request_id))
        self.assertNotIn("'host'", output)
        self.assertIn("'hostId'", output)

        # The 'host' and 'hostId' are exposed to admin
        output = self.nova("instance-action %s %s" % (server_id, request_id))
        self.assertIn("'host'", output)
        self.assertIn("'hostId'", output)


class TestInstanceActionCLIV266(TestInstanceActionCLIV258,
                                base.TenantTestBase):
    """Instance action functional tests for v2.66 nova-api microversion."""

    COMPUTE_API_VERSION = "2.66"
    expect_event_hostId_field = True

    def _wait_for_instance_actions(self, server, expected_num_of_actions):
        start_time = time.time()
        # Time out after 60 seconds
        while time.time() - start_time < 60:
            actions = self.client.instance_action.list(server)
            if len(actions) == expected_num_of_actions:
                break
            # Sleep 1 second
            time.sleep(1)
        else:
            self.fail("The number of instance actions for server %s "
                      "was not %d after 60 s" %
                      (server.id, expected_num_of_actions))
        # NOTE(takashin): In some DBMSs (e.g. MySQL 5.7), fractions
        # (millisecond and microsecond) of DateTime column is not stored
        # by default. So sleep an extra second.
        time.sleep(1)
        # Return time
        return timeutils.utcnow().isoformat()

    def test_list_instance_action_with_changes_before(self):
        server = self._create_server()
        end_create = self._wait_for_instance_actions(server, 1)
        # NOTE(takashin): In some DBMSs (e.g. MySQL 5.7), fractions
        # (millisecond and microsecond) of DateTime column is not stored
        # by default. So sleep a second.
        time.sleep(1)
        server.stop()
        end_stop = self._wait_for_instance_actions(server, 2)

        stop_output = self.nova(
            "instance-action-list %s --changes-before %s" %
            (server.id, end_stop))
        action = self._get_list_of_values_from_single_column_table(
            stop_output, "Action")
        # The actions are sorted by created_at in descending order.
        self.assertEqual(['create', 'stop'], action,
                         'Expected to find the create and stop actions with '
                         '--changes-before=%s but got: %s\n\n' %
                         (end_stop, stop_output))

        create_output = self.nova(
            "instance-action-list %s --changes-before %s" %
            (server.id, end_create))
        action = self._get_list_of_values_from_single_column_table(
            create_output, "Action")
        # Provide detailed debug information if this fails.
        self.assertEqual(['create'], action,
                         'Expected to find the create action with '
                         '--changes-before=%s but got: %s\n\n'
                         'First instance-action-list output: %s' %
                         (end_create, create_output, stop_output))

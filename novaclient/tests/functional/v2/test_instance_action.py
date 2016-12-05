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

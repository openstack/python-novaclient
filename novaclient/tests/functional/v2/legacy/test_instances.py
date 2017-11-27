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

from novaclient.tests.functional import base


class TestInstanceCLI(base.ClientTestBase):

    COMPUTE_API_VERSION = "2.1"

    def test_attach_volume(self):
        """Test we can attach a volume via the cli.

        This test was added after bug 1423695. That bug exposed
        inconsistencies in how to talk to API services from the CLI
        vs. API level. The volumes api calls that were designed to
        populate the completion cache were incorrectly routed to the
        Nova endpoint. Novaclient volumes support actually talks to
        Cinder endpoint directly.

        This would case volume-attach to return a bad error code,
        however it does this *after* the attach command is correctly
        dispatched. So the volume-attach still works, but the user is
        presented a 404 error.

        This test ensures we can do a through path test of: boot,
        create volume, attach volume, detach volume, delete volume,
        destroy.

        """
        name = self.name_generate()

        # Boot via the cli, as we're primarily testing the cli in this test
        self.nova('boot',
                  params="--flavor %s --image %s %s --nic net-id=%s --poll" %
                  (self.flavor.name, self.image.name, name, self.network.id))

        # Be nice about cleaning up, however, use the API for this to avoid
        # parsing text.
        servers = self.client.servers.list(search_opts={"name": name})
        # the name is a random uuid, there better only be one
        self.assertEqual(1, len(servers), servers)
        server = servers[0]
        self.addCleanup(server.delete)

        # create a volume for attachment
        volume = self.cinder.volumes.create(1)
        self.addCleanup(volume.delete)

        # allow volume to become available
        self.wait_for_volume_status(volume, 'available')

        # attach the volume
        self.nova('volume-attach', params="%s %s" % (name, volume.id))

        # volume needs to transition to 'in-use' to be attached
        self.wait_for_volume_status(volume, 'in-use')

        # clean up on success
        self.nova('volume-detach', params="%s %s" % (name, volume.id))
        self.wait_for_volume_status(volume, 'available')

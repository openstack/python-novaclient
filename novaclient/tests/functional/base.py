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

import os
import time

from cinderclient.v2 import client as cinderclient
import fixtures
from glanceclient import client as glanceclient
from keystoneauth1.exceptions import discovery as discovery_exc
from keystoneauth1 import identity
from keystoneauth1 import session as ksession
from keystoneclient import client as keystoneclient
from keystoneclient import discover as keystone_discover
from neutronclient.v2_0 import client as neutronclient
import openstack.config
import openstack.config.exceptions
from oslo_utils import uuidutils
import tempest.lib.cli.base
import testtools

import novaclient
import novaclient.api_versions
from novaclient import base
import novaclient.client
from novaclient.v2 import networks
import novaclient.v2.shell

BOOT_IS_COMPLETE = ("login as 'cirros' user. default password: "
                    "'gocubsgo'. use 'sudo' for root.")


def is_keystone_version_available(session, version):
    """Given a (major, minor) pair, check if the API version is enabled."""

    d = keystone_discover.Discover(session)
    try:
        d.create_client(version)
    except (discovery_exc.DiscoveryFailure, discovery_exc.VersionNotAvailable):
        return False
    else:
        return True


# The following are simple filter functions that filter our available
# image / flavor list so that they can be used in standard testing.
def pick_flavor(flavors):
    """Given a flavor list pick a reasonable one."""
    for flavor_priority in ('m1.nano', 'm1.micro', 'm1.tiny', 'm1.small'):
        for flavor in flavors:
            if flavor.name == flavor_priority:
                return flavor
    raise NoFlavorException()


def pick_image(images):
    firstImage = None
    for image in images:
        firstImage = firstImage or image
        if image.name.startswith('cirros') and (
                image.name.endswith('-uec') or
                image.name.endswith('-disk.img')):
            return image

    # We didn't find the specific cirros image we'd like to use, so just use
    # the first available.
    if firstImage:
        return firstImage

    raise NoImageException()


def pick_network(networks):
    network_name = os.environ.get('OS_NOVACLIENT_NETWORK')
    if network_name:
        for network in networks:
            if network.name == network_name:
                return network
        raise NoNetworkException()
    return networks[0]


class NoImageException(Exception):
    """We couldn't find an acceptable image."""
    pass


class NoFlavorException(Exception):
    """We couldn't find an acceptable flavor."""
    pass


class NoNetworkException(Exception):
    """We couldn't find an acceptable network."""
    pass


class NoCloudConfigException(Exception):
    """We couldn't find a cloud configuration."""
    pass


CACHE = {}


class ClientTestBase(testtools.TestCase):
    """Base test class for read only python-novaclient commands.

    This is a first pass at a simple read only python-novaclient test. This
    only exercises client commands that are read only.

    This should test commands:
    * as a regular user
    * as a admin user
    * with and without optional parameters
    * initially just check return codes, and later test command outputs

    """
    COMPUTE_API_VERSION = None

    log_format = ('%(asctime)s %(process)d %(levelname)-8s '
                  '[%(name)s] %(message)s')

    def setUp(self):
        super(ClientTestBase, self).setUp()

        test_timeout = os.environ.get('OS_TEST_TIMEOUT', 0)
        try:
            test_timeout = int(test_timeout)
        except ValueError:
            test_timeout = 0
        if test_timeout > 0:
            self.useFixture(fixtures.Timeout(test_timeout, gentle=True))

        if (os.environ.get('OS_STDOUT_CAPTURE') == 'True' or
                os.environ.get('OS_STDOUT_CAPTURE') == '1'):
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if (os.environ.get('OS_STDERR_CAPTURE') == 'True' or
                os.environ.get('OS_STDERR_CAPTURE') == '1'):
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))

        if (os.environ.get('OS_LOG_CAPTURE') != 'False' and
                os.environ.get('OS_LOG_CAPTURE') != '0'):
            self.useFixture(fixtures.LoggerFixture(nuke_handlers=False,
                                                   format=self.log_format,
                                                   level=None))

        # Collecting of credentials:
        #
        # Grab the cloud config from a user's clouds.yaml file.
        # First look for a functional_admin cloud, as this is a cloud
        # that the user may have defined for functional testing that has
        # admin credentials.
        # If that is not found, get the devstack config and override the
        # username and project_name to be admin so that admin credentials
        # will be used.
        #
        # Finally, fall back to looking for environment variables to support
        # existing users running these the old way. We should deprecate that
        # as tox 2.0 blanks out environment.
        #
        # TODO(sdague): while we collect this information in
        # tempest-lib, we do it in a way that's not available for top
        # level tests. Long term this probably needs to be in the base
        # class.
        openstack_config = openstack.config.OpenStackConfig()
        try:
            cloud_config = openstack_config.get_one_cloud('functional_admin')
        except openstack.config.exceptions.OpenStackConfigException:
            try:
                cloud_config = openstack_config.get_one_cloud(
                    'devstack', auth=dict(
                        username='admin', project_name='admin'))
            except openstack.config.exceptions.OpenStackConfigException:
                try:
                    cloud_config = openstack_config.get_one_cloud('envvars')
                except openstack.config.exceptions.OpenStackConfigException:
                    cloud_config = None

        if cloud_config is None:
            raise NoCloudConfigException(
                "Could not find a cloud named functional_admin or a cloud"
                " named devstack. Please check your clouds.yaml file and"
                " try again.")
        auth_info = cloud_config.config['auth']

        user = auth_info['username']
        passwd = auth_info['password']
        self.project_name = auth_info['project_name']
        auth_url = auth_info['auth_url']
        user_domain_id = auth_info['user_domain_id']
        self.project_domain_id = auth_info['project_domain_id']

        if 'insecure' in cloud_config.config:
            self.insecure = cloud_config.config['insecure']
        else:
            self.insecure = False

        auth = identity.Password(username=user,
                                 password=passwd,
                                 project_name=self.project_name,
                                 auth_url=auth_url,
                                 project_domain_id=self.project_domain_id,
                                 user_domain_id=user_domain_id)
        session = ksession.Session(auth=auth, verify=(not self.insecure))

        self.client = self._get_novaclient(session)

        self.glance = glanceclient.Client('2', session=session)

        # pick some reasonable flavor / image combo
        if "flavor" not in CACHE:
            CACHE["flavor"] = pick_flavor(self.client.flavors.list())
        if "image" not in CACHE:
            CACHE["image"] = pick_image(self.glance.images.list())
        self.flavor = CACHE["flavor"]
        self.image = CACHE["image"]

        if "network" not in CACHE:
            # Get the networks from neutron.
            neutron = neutronclient.Client(session=session)
            neutron_networks = neutron.list_networks()['networks']
            # Convert the neutron dicts to Network objects.
            nets = []
            for network in neutron_networks:
                nets.append(networks.Network(
                    networks.NeutronManager, network))
            # Keep track of whether or not there are multiple networks
            # available to the given tenant because if so, a specific
            # network ID has to be passed in on server create requests
            # otherwise the server POST will fail with a 409.
            CACHE['multiple_networks'] = len(nets) > 1
            CACHE["network"] = pick_network(nets)
        self.network = CACHE["network"]
        self.multiple_networks = CACHE['multiple_networks']

        # create a CLI client in case we'd like to do CLI
        # testing. tempest.lib does this really weird thing where it
        # builds a giant factory of all the CLIs that it knows
        # about. Eventually that should really be unwound into
        # something more sensible.
        cli_dir = os.environ.get(
            'OS_NOVACLIENT_EXEC_DIR',
            os.path.join(os.path.abspath('.'), '.tox/functional/bin'))

        self.cli_clients = tempest.lib.cli.base.CLIClient(
            username=user,
            password=passwd,
            tenant_name=self.project_name,
            uri=auth_url,
            cli_dir=cli_dir,
            insecure=self.insecure)

        self.keystone = keystoneclient.Client(session=session,
                                              username=user,
                                              password=passwd)
        self.cinder = cinderclient.Client(auth=auth, session=session)

    def _get_novaclient(self, session):
        nc = novaclient.client.Client("2", session=session)

        if self.COMPUTE_API_VERSION:
            if "min_api_version" not in CACHE:
                # Obtain supported versions by API side
                v = nc.versions.get_current()
                if not hasattr(v, 'version') or not v.version:
                    # API doesn't support microversions
                    CACHE["min_api_version"] = (
                        novaclient.api_versions.APIVersion("2.0"))
                    CACHE["max_api_version"] = (
                        novaclient.api_versions.APIVersion("2.0"))
                else:
                    CACHE["min_api_version"] = (
                        novaclient.api_versions.APIVersion(v.min_version))
                    CACHE["max_api_version"] = (
                        novaclient.api_versions.APIVersion(v.version))

            if self.COMPUTE_API_VERSION == "2.latest":
                requested_version = min(novaclient.API_MAX_VERSION,
                                        CACHE["max_api_version"])
            else:
                requested_version = novaclient.api_versions.APIVersion(
                    self.COMPUTE_API_VERSION)

            if not requested_version.matches(CACHE["min_api_version"],
                                             CACHE["max_api_version"]):
                msg = ("%s is not supported by Nova-API. Supported version" %
                       self.COMPUTE_API_VERSION)
                if CACHE["min_api_version"] == CACHE["max_api_version"]:
                    msg += ": %s" % CACHE["min_api_version"].get_string()
                else:
                    msg += "s: %s - %s" % (
                        CACHE["min_api_version"].get_string(),
                        CACHE["max_api_version"].get_string())
                self.skipTest(msg)

            nc.api_version = requested_version
        return nc

    def nova(self, action, flags='', params='', fail_ok=False,
             endpoint_type='publicURL', merge_stderr=False):
        if self.COMPUTE_API_VERSION:
            flags += " --os-compute-api-version %s " % self.COMPUTE_API_VERSION
        return self.cli_clients.nova(action, flags, params, fail_ok,
                                     endpoint_type, merge_stderr)

    def wait_for_volume_status(self, volume, status, timeout=60,
                               poll_interval=1):
        """Wait until volume reaches given status.

        :param volume: volume resource
        :param status: expected status of volume
        :param timeout: timeout in seconds
        :param poll_interval: poll interval in seconds
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            volume = self.cinder.volumes.get(volume.id)
            if volume.status == status:
                break
            time.sleep(poll_interval)
        else:
            self.fail("Volume %s did not reach status %s after %d s"
                      % (volume.id, status, timeout))

    def wait_for_server_os_boot(self, server_id, timeout=300,
                                poll_interval=1):
        """Wait until instance's operating system  is completely booted.

        :param server_id: uuid4 id of given instance
        :param timeout: timeout in seconds
        :param poll_interval: poll interval in seconds
        """
        start_time = time.time()
        console = None
        while time.time() - start_time < timeout:
            console = self.nova('console-log %s ' % server_id)
            if BOOT_IS_COMPLETE in console:
                break
            time.sleep(poll_interval)
        else:
            self.fail("Server %s did not boot after %d s.\nConsole:\n%s"
                      % (server_id, timeout, console))

    def wait_for_resource_delete(self, resource, manager,
                                 timeout=60, poll_interval=1):
        """Wait until getting the resource raises NotFound exception.

        :param resource: Resource object.
        :param manager: Manager object with get method.
        :param timeout: timeout in seconds
        :param poll_interval: poll interval in seconds
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                manager.get(resource)
            except Exception as e:
                if getattr(e, "http_status", None) == 404:
                    break
                else:
                    raise
            time.sleep(poll_interval)
        else:
            self.fail("The resource '%s' still exists." % base.getid(resource))

    def name_generate(self):
        """Generate randomized name for some entity."""
        # NOTE(andreykurilin): name_generator method is used for various
        #   resources (servers, flavors, volumes, keystone users, etc).
        #   Since the length of name has limits we cannot use the whole UUID,
        #   so the first 8 chars is taken from it.
        #   Based on the fact that the new name includes class and method
        #   names, 8 chars of uuid should be enough to prevent any conflicts,
        #   even if the single test will be launched in parallel thousand times
        return "%(prefix)s-%(test_cls)s-%(test_name)s" % {
            "prefix": uuidutils.generate_uuid()[:8],
            "test_cls": self.__class__.__name__,
            "test_name": self.id().rsplit(".", 1)[-1]
        }

    def _get_value_from_the_table(self, table, key):
        """Parses table to get desired value.

        EXAMPLE of the table:
        # +-------------+----------------------------------+
        # |   Property  |              Value               |
        # +-------------+----------------------------------+
        # | description |                                  |
        # |   enabled   |               True               |
        # |      id     | 582df899eabc47018c96713c2f7196ba |
        # |     name    |              admin               |
        # +-------------+----------------------------------+
        """
        lines = table.split("\n")
        for line in lines:
            if "|" in line:
                l_property, l_value = line.split("|")[1:3]
                if l_property.strip() == key:
                    return l_value.strip()
        raise ValueError("Property '%s' is missing from the table:\n%s" %
                         (key, table))

    def _get_column_value_from_single_row_table(self, table, column):
        """Get the value for the column in the single-row table

        Example table:

        +----------+-------------+----------+----------+
        | address  | cidr        | hostname | host     |
        +----------+-------------+----------+----------+
        | 10.0.0.3 | 10.0.0.0/24 | test     | myhost   |
        +----------+-------------+----------+----------+

        :param table: newline-separated table with |-separated cells
        :param column: name of the column to look for
        :raises: ValueError if the column value is not found
        """
        lines = table.split("\n")
        # Determine the column header index first.
        column_index = -1
        for line in lines:
            if "|" in line:
                if column_index == -1:
                    headers = line.split("|")[1:-1]
                    for index, header in enumerate(headers):
                        if header.strip() == column:
                            column_index = index
                            break
                else:
                    # We expect a single-row table so we should be able to get
                    # the value now using the column index.
                    return line.split("|")[1:-1][column_index].strip()

        raise ValueError("Unable to find value for column '%s'." % column)

    def _get_list_of_values_from_single_column_table(self, table, column):
        """Get the list of values for the column in the single-column table

        Example table:

        +------+
        | Tags |
        +------+
        | tag1 |
        | tag2 |
        +------+

        :param table: newline-separated table with |-separated cells
        :param column: name of the column to look for
        :raises: ValueError if the single column has some other name
        """
        lines = table.split("\n")
        column_name = None
        values = []
        for line in lines:
            if "|" in line:
                if not column_name:
                    column_name = line.split("|")[1].strip()
                    if column_name != column:
                        raise ValueError(
                            "The table has no column %(expected)s "
                            "but has column %(actual)s." % {
                                'expected': column, 'actual': column_name})
                else:
                    values.append(line.split("|")[1].strip())
        return values

    def _create_server(self, name=None, flavor=None, with_network=True,
                       add_cleanup=True, **kwargs):
        name = name or self.name_generate()
        if with_network:
            nics = [{"net-id": self.network.id}]
        else:
            nics = None
        flavor = flavor or self.flavor
        server = self.client.servers.create(name, self.image, flavor,
                                            nics=nics, **kwargs)
        if add_cleanup:
            self.addCleanup(server.delete)
        novaclient.v2.shell._poll_for_status(
            self.client.servers.get, server.id,
            'building', ['active'])
        return server

    def _wait_for_state_change(self, server_id, status):
        novaclient.v2.shell._poll_for_status(
            self.client.servers.get, server_id, None, [status],
            show_progress=False, poll_period=1, silent=True)

    def _get_project_id(self, name):
        """Obtain project id by project name."""
        if self.keystone.version == "v3":
            project = self.keystone.projects.find(name=name)
        else:
            project = self.keystone.tenants.find(name=name)
        return project.id

    def _cleanup_server(self, server_id):
        """Deletes a server and waits for it to be gone."""
        self.client.servers.delete(server_id)
        self.wait_for_resource_delete(server_id, self.client.servers)

    def _get_absolute_limits(self):
        """Returns the absolute limits (quota usage) including reserved quota
        usage for the given tenant running the test.

        :return: A dict where the key is the limit (or usage) and value.
        """
        # The absolute limits are returned in a generator so convert to a dict.
        return {limit.name: limit.value
                for limit in self.client.limits.get(reserved=True).absolute}


class TenantTestBase(ClientTestBase):
    """Base test class for additional tenant and user creation which
    could be required in various test scenarios
    """

    def setUp(self):
        super(TenantTestBase, self).setUp()
        user_name = uuidutils.generate_uuid()
        project_name = uuidutils.generate_uuid()
        password = 'password'

        if self.keystone.version == "v3":
            project = self.keystone.projects.create(project_name,
                                                    self.project_domain_id)
            self.project_id = project.id
            self.addCleanup(self.keystone.projects.delete, self.project_id)

            self.user_id = self.keystone.users.create(
                name=user_name, password=password,
                default_project=self.project_id).id

            for role in self.keystone.roles.list():
                if "member" in role.name.lower():
                    self.keystone.roles.grant(role.id, user=self.user_id,
                                              project=self.project_id)
                    break
        else:
            project = self.keystone.tenants.create(project_name)
            self.project_id = project.id
            self.addCleanup(self.keystone.tenants.delete, self.project_id)

            self.user_id = self.keystone.users.create(
                user_name, password, tenant_id=self.project_id).id

        self.addCleanup(self.keystone.users.delete, self.user_id)
        self.cli_clients_2 = tempest.lib.cli.base.CLIClient(
            username=user_name,
            password=password,
            tenant_name=project_name,
            uri=self.cli_clients.uri,
            cli_dir=self.cli_clients.cli_dir,
            insecure=self.insecure)

    def another_nova(self, action, flags='', params='', fail_ok=False,
                     endpoint_type='publicURL', merge_stderr=False):
        flags += " --os-compute-api-version %s " % self.COMPUTE_API_VERSION
        return self.cli_clients_2.nova(action, flags, params, fail_ok,
                                       endpoint_type, merge_stderr)

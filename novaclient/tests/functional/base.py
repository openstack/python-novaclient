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
import uuid

import fixtures
import os_client_config
import six
import tempest_lib.cli.base
import testtools

import novaclient.client


# The following are simple filter functions that filter our available
# image / flavor list so that they can be used in standard testing.
def pick_flavor(flavors):
    """Given a flavor list pick a reasonable one."""
    for flavor in flavors:
        if flavor.name == 'm1.tiny':
            return flavor
    for flavor in flavors:
        if flavor.name == 'm1.small':
            return flavor
    raise NoFlavorException()


def pick_image(images):
    for image in images:
        if image.name.startswith('cirros') and image.name.endswith('-uec'):
            return image
    raise NoImageException()


class NoImageException(Exception):
    """We couldn't find an acceptable image."""
    pass


class NoFlavorException(Exception):
    """We couldn't find an acceptable flavor."""
    pass


class NoCloudConfigException(Exception):
    """We couldn't find a cloud configuration."""
    pass


class ClientTestBase(testtools.TestCase):
    """
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
        openstack_config = os_client_config.config.OpenStackConfig()
        try:
            cloud_config = openstack_config.get_one_cloud('functional_admin')
        except os_client_config.exceptions.OpenStackConfigException:
            try:
                cloud_config = openstack_config.get_one_cloud(
                    'devstack', auth=dict(
                        username='admin', project_name='admin'))
            except os_client_config.exceptions.OpenStackConfigException:
                try:
                    cloud_config = openstack_config.get_one_cloud('envvars')
                except os_client_config.exceptions.OpenStackConfigException:
                    cloud_config = None

        if cloud_config is None:
            raise NoCloudConfigException(
                "Cloud not find a cloud named functional_admin or a cloud"
                " named devstack. Please check your clouds.yaml file and"
                " try again.")
        auth_info = cloud_config.config['auth']

        user = auth_info['username']
        passwd = auth_info['password']
        tenant = auth_info['project_name']
        auth_url = auth_info['auth_url']

        # TODO(sdague): we made a lot of fun of the glanceclient team
        # for version as int in first parameter. I guess we know where
        # they copied it from.
        self.client = novaclient.client.Client(
            2, user, passwd, tenant,
            auth_url=auth_url)

        # pick some reasonable flavor / image combo
        self.flavor = pick_flavor(self.client.flavors.list())
        self.image = pick_image(self.client.images.list())

        # create a CLI client in case we'd like to do CLI
        # testing. tempest_lib does this really weird thing where it
        # builds a giant factory of all the CLIs that it knows
        # about. Eventually that should really be unwound into
        # something more sensible.
        cli_dir = os.environ.get(
            'OS_NOVACLIENT_EXEC_DIR',
            os.path.join(os.path.abspath('.'), '.tox/functional/bin'))

        self.cli_clients = tempest_lib.cli.base.CLIClient(
            username=user,
            password=passwd,
            tenant_name=tenant,
            uri=auth_url,
            cli_dir=cli_dir)

    def nova(self, action, flags='', params='', fail_ok=False,
             endpoint_type='publicURL', merge_stderr=False):
        if self.COMPUTE_API_VERSION:
            flags += " --os-compute-api-version %s " % self.COMPUTE_API_VERSION
        return self.cli_clients.nova(action, flags, params, fail_ok,
                                     endpoint_type, merge_stderr)

    def wait_for_volume_status(self, volume, status, timeout=60,
                               poll_interval=1):
        """Wait until volume reaches given status.

        :param volume_id: uuid4 id of given volume
        :param status: expected status of volume
        :param timeout: timeout in seconds
        :param poll_interval: poll interval in seconds
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            volume = self.client.volumes.get(volume.id)
            if volume.status == status:
                break
            time.sleep(poll_interval)
        else:
            self.fail("Volume %s did not reach status %s after %d s"
                      % (volume.id, status, timeout))

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
            self.fail("The resource '%s' still exists." % resource.id)

    def name_generate(self, prefix='Entity'):
        """Generate randomized name for some entity.

        :param prefix: string prefix
        """
        name = "%s-%s" % (prefix, six.text_type(uuid.uuid4()))
        return name

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
        raise ValueError("Property '%s' is missing from the table." % key)

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

        raise ValueError("Unable to find value for column '%s'.")

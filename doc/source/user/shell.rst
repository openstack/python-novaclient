===================================
 The :program:`nova` Shell Utility
===================================

.. program:: nova
.. highlight:: bash

The :program:`nova` shell utility interacts with OpenStack Nova API from the
command line. It supports the entirety of the OpenStack Nova API.

You'll need to provide :program:`nova` with your OpenStack Keystone user
information. You can do this with the `--os-username`, `--os-password`,
`--os-project-name` (`--os-project-id`), `--os-project-domain-name`
(`--os-project-domain-id`) and `--os-user-domain-name` (`--os-user-domain-id`)
options, but it's easier to just set them as environment variables by setting
some environment variables:

.. deprecated:: 17.8.0

    The ``nova`` CLI has been deprecated in favour of the unified
    ``openstack`` CLI. For information on using the ``openstack`` CLI, see
    :python-openstackclient-doc:`OpenStackClient <>`.

.. envvar:: OS_USERNAME

    Your OpenStack Keystone user name.

.. envvar:: OS_PASSWORD

    Your password.

.. envvar:: OS_PROJECT_NAME

    The name of project for work.

.. envvar:: OS_PROJECT_ID

    The ID of project for work.

.. envvar:: OS_PROJECT_DOMAIN_NAME

    The name of domain containing the project.

.. envvar:: OS_PROJECT_DOMAIN_ID

    The ID of domain containing the project.

.. envvar:: OS_USER_DOMAIN_NAME

    The user's domain name.

.. envvar:: OS_USER_DOMAIN_ID

    The user's domain ID.

.. envvar:: OS_AUTH_URL

    The OpenStack Keystone endpoint URL.

.. envvar:: OS_COMPUTE_API_VERSION

    The OpenStack Nova API version (microversion).

.. envvar:: OS_REGION_NAME

    The Keystone region name. Defaults to the first region if multiple regions
    are available.

.. envvar:: OS_TRUSTED_IMAGE_CERTIFICATE_IDS

    A comma-delimited list of trusted image certificate IDs. Only used
    with the ``nova boot`` and ``nova rebuild`` commands starting with the
    2.63 microversion.

    For example::

      export OS_TRUSTED_IMAGE_CERTIFICATE_IDS=trusted-cert-id1,trusted-cert-id2

For example, in Bash you'd use::

    export OS_USERNAME=yourname
    export OS_PASSWORD=yadayadayada
    export OS_PROJECT_NAME=myproject
    export OS_PROJECT_DOMAIN_NAME=default
    export OS_USER_DOMAIN_NAME=default
    export OS_AUTH_URL=http://<url-to-openstack-keystone>/identity
    export OS_COMPUTE_API_VERSION=2.1

From there, all shell commands take the form::

    nova <command> [arguments...]

Run :program:`nova help` to get a full list of all possible commands, and run
:program:`nova help <command>` to get detailed help for that command.

For more information, see :doc:`the command reference </cli/nova>`.

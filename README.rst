Python bindings to the OpenStack Nova API
==================================================

This is a client for the OpenStack Nova API. There's a Python API (the
``novaclient`` module), and a command-line script (``nova``). Each
implements 100% of the OpenStack Nova API.

[PENDING] `Full documentation is available`__.

__ http://packages.python.org/python-novaclient/

You'll also probably want to read `OpenStack Compute Developer Guide API`__ --
the first bit, at least -- to get an idea of the concepts. Rackspace is doing
the cloud hosting thing a bit differently from Amazon, and if you get the
concepts this library should make more sense.

__ http://docs.openstack.org/api/

The project is hosted on `Launchpad`_, where bugs can be filed. The code is
hosted on `Github`_. Patches must be submitted using `Gerrit`_, *not* Github
pull requests.

.. _Github: https://github.com/openstack/python-novaclient
.. _Launchpad: https://launchpad.net/python-novaclient
.. _Gerrit: http://wiki.openstack.org/GerritWorkflow

This code a fork of `Jacobian's python-cloudservers`__ If you need API support
for the Rackspace API solely or the BSD license, you should use that repository.
python-client is licensed under the Apache License like the rest of OpenStack.

__ http://github.com/jacobian/python-cloudservers

.. contents:: Contents:
   :local:

Command-line API
----------------

Installing this package gets you a shell command, ``nova``, that you
can use to interact with any Rackspace compatible API (including OpenStack).

You'll need to provide your OpenStack username and password. You can do this
with the ``--os_username``, ``--os_password`` and  ``--os_tenant_name``
params, but it's easier to just set them as environment variables::

    export OS_USERNAME=openstack
    export OS_PASSWORD=yadayada
    export OS_TENANT_NAME=myproject

You will also need to define the authentication url with ``--os_auth_url``
and the version of the API with ``--version``.  Or set them as an environment
variables as well::

    export OS_AUTH_URL=http://example.com:8774/v1.1/
    export NOVA_VERSION=1.1

If you are using Keystone, you need to set the NOVA_URL to the keystone
endpoint::

    export OS_AUTH_URL=http://example.com:5000/v2.0/

Since Keystone can return multiple regions in the Service Catalog, you
can specify the one you want with ``--os_region_name`` (or
``export OS_REGION_NAME``). It defaults to the first in the list returned.

You'll find complete documentation on the shell by running
``nova help``::

    usage: nova [--debug] [--os_username OS_USERNAME] [--os_password OS_PASSWORD]
                [--os_tenant_name OS_TENANT_NAME] [--os_auth_url OS_AUTH_URL]
                [--os_region_name OS_REGION_NAME] [--service_type SERVICE_TYPE]
                [--service_name SERVICE_NAME] [--endpoint_type ENDPOINT_TYPE]
                [--version VERSION]
                <subcommand> ...

    Command-line interface to the OpenStack Nova API.

    Positional arguments:
      <subcommand>
        add-fixed-ip        Add a new fixed IP address to a servers network.
        add-floating-ip     Add a floating IP address to a server.
        aggregate-add-host  Add the host to the specified aggregate
        aggregate-create    Create a new aggregate with the specified details
        aggregate-delete    Delete the aggregate by its id
        aggregate-details   Show details of the specified aggregate
        aggregate-list      Print a list of all aggregates
        aggregate-remove-host
                            Remove the specified host from the specfied
                            aggregate
        aggregate-set-metadata
                            Update the metadata associated with the aggregate
        aggregate-update    Update the aggregate's name and optionally
                            availability zone
        backup              Backup a server.
        backup-schedule     Show or edit the backup schedule for a server.
        backup-schedule-delete
                            Delete the backup schedule for a server.
        boot                Boot a new server.
        delete              Immediately shut down and delete a server.
        flavor-create       Create a new flavor
        flavor-delete       Delete a specific flavor
        flavor-list         Print a list of available 'flavors' (sizes of
                            servers).
        floating-ip-create  Allocate a floating IP to the current tenant.
        floating-ip-delete  De-allocate a floating IP from the current tenant.
        floating-ip-list    List allocated floating IPs for the current tenant.
        floating-ip-pool-list
                            List all floating ip pools.
        get-vnc-console     Get a vnc console for a server
        help                Display help about this program or one of its
                            subcommands.
        host-update         Update the host status or maintenance mode
        host-action         Perform a power action on the host
        image-create        Create a new image by taking a snapshot of a running
                            server.
        image-delete        Delete an image.
        image-list          Print a list of available images to boot from.
        ip-share            Share an IP address from the given IP group onto a
                            server.
        ip-unshare          Stop sharing an given address with a server.
        ipgroup-create      Create a new IP group.
        ipgroup-delete      Delete an IP group.
        ipgroup-list        Show IP groups.
        ipgroup-show        Show details about a particular IP group.
        keypair-add         Create a new key pair for use with instances
        keypair-delete      Delete keypair by its id
        keypair-list        Show a list of keypairs for a user
        list                List active servers.
        lock                Lock a server
        migrate             Migrate a server to a new host.
        reboot              Reboot a server.
        rebuild             Shutdown, re-image, and re-boot a server.
        remove-fixed-ip     Remove an IP address from a server.
        remove-floating-ip  Remove a floating IP address from a server.
        rename              Rename a server.
        rescue              Rescue a server.
        resize              Resize a server.
        resize-confirm      Confirm a previous resize.
        resize-revert       Revert a previous resize (and return to the previous
                            VM).
        root-password       Change the root password for a server.
        secgroup-add-group-rule
                            Add a source group rule to a security group.
        secgroup-add-rule   Add a rule to a security group.
        secgroup-create     Create a new security group.
        secgroup-delete     Delete a security group.
        secgroup-delete-group-rule
                            Delete a source group rule from a security group.
        secgroup-delete-rule
                            Delete a rule from a security group.
        secgroup-list       List security groups for the curent tenant.
        secgroup-list-rules List rules for a security group.
        show                Show details about the given server.
        suspend             Suspend a server.
        unlock              Unlock a server.
        unpause             Unpause a server.
        unrescue            Unrescue a server.
        usage-list          List usage data for all tenants
        volume-attach       Attach a volume to a server.
        volume-create       Add a new volume.
        volume-delete       Remove a volume.
        volume-detach       Detach a volume from a server.
        volume-list         List all the volumes.
        volume-show         Show details about a volume.
        volume-snapshot-create
                            Add a new snapshot.
        volume-snapshot-delete
                            Remove a snapshot.
        volume-snapshot-list
                            List all the snapshots.
        volume-snapshot-show
                            Show details about a snapshot.
        x509-create-cert    Create x509 cert for a user in tenant
        x509-get-root-cert  Fetches the x509 root cert.

    Optional arguments:
      --debug               Print debugging output
      --os_username OS_USERNAME
                            Defaults to env[OS_USERNAME].
      --os_password OS_PASSWORD
                            Defaults to env[OS_PASSWORD].
      --os_tenant_name OS_TENANT_NAME
                            Defaults to env[OS_TENANT_NAME].
      --os_auth_url OS_AUTH_URL
                            Defaults to env[OS_AUTH_URL].
      --os_region_name OS_REGION_NAME
                            Defaults to env[OS_REGION_NAME].
      --service_type SERVICE_TYPE
                            Defaults to compute for most actions
      --service_name SERVICE_NAME
                            Defaults to env[NOVA_SERVICE_NAME]
      --endpoint_type ENDPOINT_TYPE
                            Defaults to env[NOVA_ENDPOINT_TYPE] or publicURL.
      --version VERSION     Accepts 1.1, defaults to env[NOVA_VERSION].


    See "nova help COMMAND" for help on a specific command.

Python API
----------

[PENDING] There's also a `complete Python API`__.

__ http://packages.python.org/python-novaclient/

By way of a quick-start::

    >>> import novaclient
    >>> nt = novaclient.OpenStack(USERNAME, PASSWORD, PROJECT_ID [, AUTH_URL])
    >>> nt.flavors.list()
    [...]
    >>> nt.servers.list()
    [...]
    >>> s = nt.servers.create(image=2, flavor=1, name='myserver')

    ... time passes ...

    >>> s.reboot()

    ... time passes ...

    >>> s.delete()

Quick-start using keystone::

    # use v2.0 auth with http://example.com:5000/v2.0/")
    >>> from novaclient.v1_1 import client
    >>> nt = client.Client(USER, PASS, TENANT, AUTH_URL)
    >>> nt.flavors.list()
    [...]
    >>> nt.servers.list()
    [...]
    >>> nt.keypairs.list()
    [...]

What's new?
-----------

[PENDING] See `the release notes <http://packages.python.org/python-novaclient/releases.html>`_.

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
    export OS_COMPUTE_API_VERSION=1.1

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
                [--version VERSION] [--username USERNAME]
                [--region_name REGION_NAME] [--apikey APIKEY]
                [--projectid PROJECTID] [--url URL]
                <subcommand> ...

    Command-line interface to the OpenStack Nova API.

    Positional arguments:
      <subcommand>
        absolute-limits     Print a list of absolute limits for a user
        actions             Retrieve server actions.
        add-fixed-ip        Add new IP address to network.
        add-floating-ip     Add a floating IP address to a server.
        aggregate-add-host  Add the host to the specified aggregate.
        aggregate-create    Create a new aggregate with the specified details.
        aggregate-delete    Delete the aggregate by its id.
        aggregate-details   Show details of the specified aggregate.
        aggregate-list      Print a list of all aggregates.
        aggregate-remove-host
                            Remove the specified host from the specified aggregate.
        aggregate-set-metadata
                            Update the metadata associated with the aggregate.
        aggregate-update    Update the aggregate's name and optionally
                            availability zone.
        boot                Boot a new server.
        console-log         Get console log output of a server.
        credentials         Show user credentials returned from auth
        delete              Immediately shut down and delete a server.
        describe-resource   Show details about a resource
        diagnostics         Retrieve server diagnostics.
        dns-create          Create a DNS entry for domain, name and ip.
        dns-create-private-domain
                            Create the specified DNS domain.
        dns-create-public-domain
                            Create the specified DNS domain.
        dns-delete          Delete the specified DNS entry.
        dns-delete-domain   Delete the specified DNS domain.
        dns-domains         Print a list of available dns domains.
        dns-list            List current DNS entries for domain and ip or domain
                            and name.
        endpoints           Discover endpoints that get returned from the
                            authenticate services
        flavor-create       Create a new flavor
        flavor-delete       Delete a specific flavor
        flavor-list         Print a list of available 'flavors' (sizes of
                            servers).
        floating-ip-create  Allocate a floating IP for the current tenant.
        floating-ip-delete  De-allocate a floating IP.
        floating-ip-list    List floating ips for this tenant.
        floating-ip-pool-list
                            List all floating ip pools.
        get-vnc-console     Get a vnc console to a server.
        host-action         Perform a power action on a host.
        host-update         Update host settings.
        image-create        Create a new image by taking a snapshot of a running
                            server.
        image-delete        Delete an image.
        image-list          Print a list of available images to boot from.
        image-meta          Set or Delete metadata on an image.
        image-show          Show details about the given image.
        keypair-add         Create a new key pair for use with instances
        keypair-delete      Delete keypair by its id
        keypair-list        Print a list of keypairs for a user
        list                List active servers.
        live-migration      Migrates a running instance to a new machine.
        lock                Lock a server.
        meta                Set or Delete metadata on a server.
        migrate             Migrate a server.
        pause               Pause a server.
        rate-limits         Print a list of rate limits for a user
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
        resume              Resume a server.
        root-password       Change the root password for a server.
        secgroup-add-group-rule
                            Add a source group rule to a security group.
        secgroup-add-rule   Add a rule to a security group.
        secgroup-create     Create a security group.
        secgroup-delete     Delete a security group.
        secgroup-delete-group-rule
                            Delete a source group rule from a security group.
        secgroup-delete-rule
                            Delete a rule from a security group.
        secgroup-list       List security groups for the curent tenant.
        secgroup-list-rules
                            List rules for a security group.
        show                Show details about the given server.
        ssh                 SSH into a server.
        start               Start a server.
        stop                Stop a server.
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
        volume-type-create  Create a new volume type.
        volume-type-delete  Delete a specific flavor
        volume-type-list    Print a list of available 'volume types'.
        x509-create-cert    Create x509 cert for a user in tenant
        x509-get-root-cert  Fetches the x509 root cert.
        bash-completion     Prints all of the commands and options to stdout so
                            that the
        help                Display help about this program or one of its
                            subcommands.

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
      --os_compute_api_version VERSION
                            Accepts 1.1, defaults to env[OS_COMPUTE_API_VERSION].
      --username USERNAME   Deprecated
      --region_name REGION_NAME
                            Deprecated
      --apikey APIKEY, --password APIKEY
                            Deprecated
      --projectid PROJECTID, --tenant_name PROJECTID
                            Deprecated
      --url URL, --auth_url URL
                            Deprecated

    See "nova help COMMAND" for help on a specific command.

Python API
----------

[PENDING] There's also a `complete Python API`__.

__ http://packages.python.org/python-novaclient/

Quick-start using keystone::

    # use v2.0 auth with http://example.com:5000/v2.0/")
    >>> from novaclient.v1_1 import client
    >>> nt = client.Client(USER, PASS, TENANT, AUTH_URL, service_type="compute")
    >>> nt.flavors.list()
    [...]
    >>> nt.servers.list()
    [...]
    >>> nt.keypairs.list()
    [...]

What's new?
-----------

[PENDING] See `the release notes <http://packages.python.org/python-novaclient/releases.html>`_.

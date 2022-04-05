======
 nova
======

The nova client is the command-line interface (CLI) for
the Compute service (nova) API and its extensions.

For help on a specific :command:`nova` command, enter:

.. code-block:: console

   $ nova help COMMAND

.. deprecated:: 17.8.0

    The ``nova`` CLI has been deprecated in favour of the unified
    ``openstack`` CLI. For information on using the ``openstack`` CLI, see
    :python-openstackclient-doc:`OpenStackClient <>`.

.. _nova_command_usage:

nova usage
~~~~~~~~~~

.. code-block:: console

   usage: nova [--version] [--debug] [--os-cache] [--timings]
               [--os-region-name <region-name>] [--service-type <service-type>]
               [--service-name <service-name>]
               [--os-endpoint-type <endpoint-type>]
               [--os-compute-api-version <compute-api-ver>]
               [--os-endpoint-override <bypass-url>] [--profile HMAC_KEY]
               [--insecure] [--os-cacert <ca-certificate>]
               [--os-cert <certificate>] [--os-key <key>] [--timeout <seconds>]
               [--collect-timing] [--os-auth-type <name>]
               [--os-auth-url OS_AUTH_URL] [--os-system-scope OS_SYSTEM_SCOPE]
               [--os-domain-id OS_DOMAIN_ID] [--os-domain-name OS_DOMAIN_NAME]
               [--os-project-id OS_PROJECT_ID]
               [--os-project-name OS_PROJECT_NAME]
               [--os-project-domain-id OS_PROJECT_DOMAIN_ID]
               [--os-project-domain-name OS_PROJECT_DOMAIN_NAME]
               [--os-trust-id OS_TRUST_ID]
               [--os-default-domain-id OS_DEFAULT_DOMAIN_ID]
               [--os-default-domain-name OS_DEFAULT_DOMAIN_NAME]
               [--os-user-id OS_USER_ID] [--os-username OS_USERNAME]
               [--os-user-domain-id OS_USER_DOMAIN_ID]
               [--os-user-domain-name OS_USER_DOMAIN_NAME]
               [--os-password OS_PASSWORD]
               <subcommand> ...

**Subcommands:**

``add-fixed-ip``
  **DEPRECATED** Add new IP address on a network to
  server.

``add-secgroup``
  Add a Security Group to a server.

``agent-create``
  Create new agent build.

``agent-delete``
  Delete existing agent build.

``agent-list``
  List all builds.

``agent-modify``
  Modify existing agent build.

``aggregate-add-host``
  Add the host to the specified aggregate.

``aggregate-cache-images``
  Request images be pre-cached on hosts within an aggregate.
  (Supported by API versions '2.81' - '2.latest')

``aggregate-create``
  Create a new aggregate with the specified
  details.

``aggregate-delete``
  Delete the aggregate.

``aggregate-list``
  Print a list of all aggregates.

``aggregate-remove-host``
  Remove the specified host from the specified
  aggregate.

``aggregate-set-metadata``
  Update the metadata associated with the
  aggregate.

``aggregate-show``
  Show details of the specified aggregate.

``aggregate-update``
  Update the aggregate's name and optionally
  availability zone.

``availability-zone-list``
  List all the availability zones.

``backup``
  Backup a server by creating a 'backup' type
  snapshot.

``boot``
  Boot a new server.

``clear-password``
  Clear the admin password for a server from the
  metadata server. This action does not actually
  change the instance server password.

``cloudpipe-configure``
  **DEPRECATED** Update the VPN IP/port of a
  cloudpipe instance.

``cloudpipe-create``
  **DEPRECATED** Create a cloudpipe instance for the
  given project.

``cloudpipe-list``
  **DEPRECATED** Print a list of all cloudpipe
  instances.

``console-log``
  Get console log output of a server.

``delete``
  Immediately shut down and delete specified
  server(s).

``diagnostics``
  Retrieve server diagnostics.

``evacuate``
  Evacuate server from failed host.

``flavor-access-add``
  Add flavor access for the given tenant.

``flavor-access-list``
  Print access information about the given
  flavor.

``flavor-access-remove``
  Remove flavor access for the given tenant.

``flavor-create``
  Create a new flavor.

``flavor-delete``
  Delete a specific flavor

``flavor-key``
  Set or unset extra_spec for a flavor.

``flavor-list``
  Print a list of available 'flavors' (sizes of
  servers).

``flavor-show``
  Show details about the given flavor.

``flavor-update``
  Update the description of an existing flavor.
  (Supported by API versions '2.55' - '2.latest')
  [hint: use '--os-compute-api-version' flag to show help message
  for proper version]

``floating-ip-associate``
  **DEPRECATED** Associate a floating IP address to
  a server.

``floating-ip-disassociate``
  **DEPRECATED** Disassociate a floating IP address
  from a server.

``force-delete``
  Force delete a server.

``get-mks-console``
  Get an MKS console to a server. (Supported by
  API versions '2.8' - '2.latest') [hint: use
  '--os-compute-api-version' flag to show help
  message for proper version]

``get-password``
  Get the admin password for a server. This
  operation calls the metadata service to query
  metadata information and does not read
  password information from the server itself.

``get-rdp-console``
  Get a rdp console to a server.

``get-serial-console``
  Get a serial console to a server.

``get-spice-console``
  Get a spice console to a server.

``get-vnc-console``
  Get a vnc console to a server.

``host-action``
  **DEPRECATED** Perform a power action on a host.

``host-describe``
  **DEPRECATED** Describe a specific host.

``host-evacuate``
  Evacuate all instances from failed host.

``host-evacuate-live``
  Live migrate all instances off the specified
  host to other available hosts.

``host-list``
  **DEPRECATED** List all hosts by service.

``host-meta``
  Set or Delete metadata on all instances of a
  host.

``host-servers-migrate``
  Cold migrate all instances off the specified
  host to other available hosts.

``host-update``
  **DEPRECATED** Update host settings.

``hypervisor-list``
  List hypervisors. (Supported by API versions '2.0' - '2.latest')
  [hint: use '--os-compute-api-version' flag to show help message
  for proper version]

``hypervisor-servers``
  List servers belonging to specific
  hypervisors.

``hypervisor-show``
  Display the details of the specified
  hypervisor.

``hypervisor-stats``
  Get hypervisor statistics over all compute
  nodes.

``hypervisor-uptime``
  Display the uptime of the specified
  hypervisor.

``image-create``
  Create a new image by taking a snapshot of a
  running server.

``instance-action``
  Show an action.

``instance-action-list``
  List actions on a server.

``instance-usage-audit-log``
  List/Get server usage audits.

``interface-attach``
  Attach a network interface to a server.

``interface-detach``
  Detach a network interface from a server.

``interface-list``
  List interfaces attached to a server.

``keypair-add``
  Create a new key pair for use with servers.

``keypair-delete``
  Delete keypair given by its name. (Supported
  by API versions '2.0' - '2.latest') [hint: use
  '--os-compute-api-version' flag to show help
  message for proper version]

``keypair-list``
  Print a list of keypairs for a user (Supported
  by API versions '2.0' - '2.latest') [hint: use
  '--os-compute-api-version' flag to show help
  message for proper version]

``keypair-show``
  Show details about the given keypair.
  (Supported by API versions '2.0' - '2.latest')
  [hint: use '--os-compute-api-version' flag to
  show help message for proper version]

``limits``
  Print rate and absolute limits.

``list``
  List servers.

``list-secgroup``
  List Security Group(s) of a server.

``live-migration``
  Migrate running server to a new machine.

``live-migration-abort``
  Abort an on-going live migration. (Supported
  by API versions '2.24' - '2.latest') [hint:
  use '--os-compute-api-version' flag to show
  help message for proper version]

``live-migration-force-complete``
  Force on-going live migration to complete.
  (Supported by API versions '2.22' - '2.latest')
  [hint: use '--os-compute-api-version' flag to show help message
  for proper version]

``lock``
  Lock a server. A normal (non-admin) user will
  not be able to execute actions on a locked
  server.

``meta``
  Set or delete metadata on a server.

``migrate``
  Migrate a server. The new host will be
  selected by the scheduler.

``migration-list``
  Print a list of migrations.

``pause``
  Pause a server.

``quota-class-show``
  List the quotas for a quota class.

``quota-class-update``
  Update the quotas for a quota class.
  (Supported by API versions '2.0' - '2.latest')
  [hint: use '--os-compute-api-version' flag to
  show help message for proper version]

``quota-defaults``
  List the default quotas for a tenant.

``quota-delete``
  Delete quota for a tenant/user so their quota
  will Revert back to default.

``quota-show``
  List the quotas for a tenant/user.

``quota-update``
  Update the quotas for a tenant/user.
  (Supported by API versions '2.0' - '2.latest')
  [hint: use '--os-compute-api-version' flag to
  show help message for proper version]

``reboot``
  Reboot a server.

``rebuild``
  Shutdown, re-image, and re-boot a server.

``refresh-network``
  Refresh server network information.

``remove-fixed-ip``
  **DEPRECATED** Remove an IP address from a server.

``remove-secgroup``
  Remove a Security Group from a server.

``rescue``
  Reboots a server into rescue mode, which
  starts the machine from either the initial
  image or a specified image, attaching the
  current boot disk as secondary.

``reset-network``
  Reset network of a server.

``reset-state``
  Reset the state of a server.

``resize``
  Resize a server.

``resize-confirm``
  Confirm a previous resize.

``resize-revert``
  Revert a previous resize (and return to the
  previous VM).

``restore``
  Restore a soft-deleted server.

``resume``
  Resume a server.

``server-group-create``
  Create a new server group with the specified
  details.

``server-group-delete``
  Delete specific server group(s).

``server-group-get``
  Get a specific server group.

``server-group-list``
  Print a list of all server groups.

``server-migration-list``
  Get the migrations list of specified server.
  (Supported by API versions '2.23' - '2.latest')
  [hint: use '--os-compute-api-version' flag to show help message
  for proper version]

``server-migration-show``
  Get the migration of specified server.
  (Supported by API versions '2.23' - '2.latest')
  [hint: use '--os-compute-api-version' flag to show help message
  for proper version]

``server-tag-add``
  Add one or more tags to a server. (Supported
  by API versions '2.26' - '2.latest') [hint:
  use '--os-compute-api-version' flag to show
  help message for proper version]

``server-tag-delete``
  Delete one or more tags from a server.
  (Supported by API versions '2.26' - '2.latest')
  [hint: use '--os-compute-api-version' flag to show help message
  for proper version]

``server-tag-delete-all``
  Delete all tags from a server. (Supported by
  API versions '2.26' - '2.latest') [hint: use
  '--os-compute-api-version' flag to show help
  message for proper version]

``server-tag-list``
  Get list of tags from a server. (Supported by
  API versions '2.26' - '2.latest') [hint: use
  '--os-compute-api-version' flag to show help
  message for proper version]

``server-tag-set``
  Set list of tags to a server. (Supported by
  API versions '2.26' - '2.latest') [hint: use
  '--os-compute-api-version' flag to show help
  message for proper version]

``server-topology``
  Retrieve NUMA topology of the given server.
  (Supported by API versions '2.78' - '2.latest')

``service-delete``
  Delete the service.

``service-disable``
  Disable the service.

``service-enable``
  Enable the service.

``service-force-down``
  Force service to down. (Supported by API
  versions '2.11' - '2.latest') [hint: use
  '--os-compute-api-version' flag to show help
  message for proper version]

``service-list``
  Show a list of all running services. Filter by
  host & binary.

``set-password``
  Change the admin password for a server.

``shelve``
  Shelve a server.

``shelve-offload``
  Remove a shelved server from the compute node.

``show``
  Show details about the given server.

``ssh``
  SSH into a server.

``start``
  Start the server(s).

``stop``
  Stop the server(s).

``suspend``
  Suspend a server.

``trigger-crash-dump``
  Trigger crash dump in an instance. (Supported
  by API versions '2.17' - '2.latest') [hint:
  use '--os-compute-api-version' flag to show
  help message for proper version]

``unlock``
  Unlock a server.

``unpause``
  Unpause a server.

``unrescue``
  Restart the server from normal boot disk
  again.

``unshelve``
  Unshelve a server.

``update``
  Update the name or the description for a
  server.

``usage``
  Show usage data for a single tenant.

``usage-list``
  List usage data for all tenants.

``version-list``
  List all API versions.

``virtual-interface-list``
  **DEPRECATED** Show virtual interface info about
  the given server.

``volume-attach``
  Attach a volume to a server.

``volume-attachments``
  List all the volumes attached to a server.

``volume-detach``
  Detach a volume from a server.

``volume-update``
  Update the attachment on the server. Migrates the data from an
  attached volume to the specified available volume and swaps out
  the active attachment to the new volume.
  Since microversion 2.85, support for updating the
  ``delete_on_termination`` delete flag, which allows changing the
  behavior of volume deletion on instance deletion.

``x509-create-cert``
  **DEPRECATED** Create x509 cert for a user in
  tenant.

``x509-get-root-cert``
  **DEPRECATED** Fetch the x509 root cert.

``bash-completion``
  Prints all of the commands and options to
  stdout so that the nova.bash_completion script
  doesn't have to hard code them.

``help``
  Display help about this program or one of its
  subcommands.

.. _nova_command_options:

nova optional arguments
~~~~~~~~~~~~~~~~~~~~~~~

``--version``
  show program's version number and exit

``--debug``
  Print debugging output.

``--os-cache``
  Use the auth token cache. Defaults to False if
  ``env[OS_CACHE]`` is not set.

``--timings``
  Print call timing info.

``--os-region-name <region-name>``
  Defaults to ``env[OS_REGION_NAME]``.

``--service-type <service-type>``
  Defaults to compute for most actions.

``--service-name <service-name>``
  Defaults to ``env[NOVA_SERVICE_NAME]``.

``--os-endpoint-type <endpoint-type>``
  Defaults to ``env[NOVA_ENDPOINT_TYPE]``,
  ``env[OS_ENDPOINT_TYPE]`` or publicURL.

``--os-compute-api-version <compute-api-ver>``
  Accepts X, X.Y (where X is major and Y is
  minor part) or "X.latest", defaults to
  ``env[OS_COMPUTE_API_VERSION]``.

``--os-endpoint-override <bypass-url>``
  Use this API endpoint instead of the Service
  Catalog. Defaults to
  ``env[OS_ENDPOINT_OVERRIDE]``.

``--profile HMAC_KEY``
  HMAC key to use for encrypting context data
  for performance profiling of operation. This
  key should be the value of the HMAC key
  configured for the OSprofiler middleware in
  nova; it is specified in the Nova
  configuration file at "/etc/nova/nova.conf".
  Without the key, profiling will not be
  triggered even if OSprofiler is enabled on the
  server side.

``--os-auth-type <name>, --os-auth-plugin <name>``
  Authentication type to use

.. _nova_add-secgroup:

nova add-secgroup
-----------------

.. code-block:: console

   usage: nova add-secgroup <server> <secgroup>

Add a Security Group to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<secgroup>``
  Name or ID of Security Group.

.. _nova_agent-create:

nova agent-create
-----------------

.. code-block:: console

   usage: nova agent-create <os> <architecture> <version> <url> <md5hash>
                            <hypervisor>

Create new agent build.

**Positional arguments:**

``<os>``
  Type of OS.

``<architecture>``
  Type of architecture.

``<version>``
  Version.

``<url>``
  URL.

``<md5hash>``
  MD5 hash.

``<hypervisor>``
  Type of hypervisor.

.. _nova_agent-delete:

nova agent-delete
-----------------

.. code-block:: console

   usage: nova agent-delete <id>

Delete existing agent build.

**Positional arguments:**

``<id>``
  ID of the agent-build.

.. _nova_agent-list:

nova agent-list
---------------

.. code-block:: console

   usage: nova agent-list [--hypervisor <hypervisor>]

List all builds.

**Optional arguments:**

``--hypervisor <hypervisor>``
  Type of hypervisor.

.. _nova_agent-modify:

nova agent-modify
-----------------

.. code-block:: console

   usage: nova agent-modify <id> <version> <url> <md5hash>

Modify existing agent build.

**Positional arguments:**

``<id>``
  ID of the agent-build.

``<version>``
  Version.

``<url>``
  URL

``<md5hash>``
  MD5 hash.

.. _nova_aggregate-add-host:

nova aggregate-add-host
-----------------------

.. code-block:: console

   usage: nova aggregate-add-host <aggregate> <host>

Add the host to the specified aggregate.

**Positional arguments:**

``<aggregate>``
  Name or ID of aggregate.

``<host>``
  The host to add to the aggregate.

.. _nova_aggregate-cache-images:

nova aggregate-cache-images
---------------------------

.. code-block:: console

   usage: nova aggregate-cache-images <aggregate> <image> [<image> ..]

Request image(s) be pre-cached on hosts within the aggregate.
(Supported by API versions '2.81' - '2.latest')

.. versionadded:: 16.0.0

**Positional arguments:**

``<aggregate>``
  Name or ID of aggregate.

``<image>``
  Name or ID of image(s) to cache.

.. _nova_aggregate-create:

nova aggregate-create
---------------------

.. code-block:: console

   usage: nova aggregate-create <name> [<availability-zone>]

Create a new aggregate with the specified details.

**Positional arguments:**

``<name>``
  Name of aggregate.

``<availability-zone>``
  The availability zone of the aggregate (optional).

.. _nova_aggregate-delete:

nova aggregate-delete
---------------------

.. code-block:: console

   usage: nova aggregate-delete <aggregate>

Delete the aggregate.

**Positional arguments:**

``<aggregate>``
  Name or ID of aggregate to delete.

.. _nova_aggregate-list:

nova aggregate-list
-------------------

.. code-block:: console

   usage: nova aggregate-list

Print a list of all aggregates.

.. _nova_aggregate-remove-host:

nova aggregate-remove-host
--------------------------

.. code-block:: console

   usage: nova aggregate-remove-host <aggregate> <host>

Remove the specified host from the specified aggregate.

**Positional arguments:**

``<aggregate>``
  Name or ID of aggregate.

``<host>``
  The host to remove from the aggregate.

.. _nova_aggregate-set-metadata:

nova aggregate-set-metadata
---------------------------

.. code-block:: console

   usage: nova aggregate-set-metadata <aggregate> <key=value> [<key=value> ...]

Update the metadata associated with the aggregate.

**Positional arguments:**

``<aggregate>``
  Name or ID of aggregate to update.

``<key=value>``
  Metadata to add/update to aggregate. Specify only the key to
  delete a metadata item.

.. _nova_aggregate-show:

nova aggregate-show
-------------------

.. code-block:: console

   usage: nova aggregate-show <aggregate>

Show details of the specified aggregate.

**Positional arguments:**

``<aggregate>``
  Name or ID of aggregate.

.. _nova_aggregate-update:

nova aggregate-update
---------------------

.. code-block:: console

   usage: nova aggregate-update [--name NAME]
                                [--availability-zone <availability-zone>]
                                <aggregate>

Update the aggregate's name and optionally availability zone.

**Positional arguments:**

``<aggregate>``
  Name or ID of aggregate to update.

**Optional arguments:**

``--name NAME``
  New name for aggregate.

``--availability-zone <availability-zone>``
  New availability zone for aggregate.

.. _nova_availability-zone-list:

nova availability-zone-list
---------------------------

.. code-block:: console

   usage: nova availability-zone-list

List all the availability zones.

.. _nova_backup:

nova backup
-----------

.. code-block:: console

   usage: nova backup <server> <name> <backup-type> <rotation>

Backup a server by creating a 'backup' type snapshot.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<name>``
  Name of the backup image.

``<backup-type>``
  The backup type, like "daily" or "weekly".

``<rotation>``
  Int parameter representing how many backups to keep around.

.. _nova_boot:

nova boot
---------

.. code-block:: console

   usage: nova boot [--flavor <flavor>] [--image <image>]
                    [--image-with <key=value>] [--boot-volume <volume_id>]
                    [--snapshot <snapshot_id>] [--min-count <number>]
                    [--max-count <number>] [--meta <key=value>]
                    [--key-name <key-name>] [--user-data <user-data>]
                    [--availability-zone <availability-zone>]
                    [--security-groups <security-groups>]
                    [--block-device-mapping <dev-name=mapping>]
                    [--block-device key1=value1[,key2=value2...]]
                    [--swap <swap_size>]
                    [--ephemeral size=<size>[,format=<format>]]
                    [--hint <key=value>]
                    [--nic <auto,none,net-id=net-uuid,net-name=network-name,port-id=port-uuid,v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr,tag=tag>]
                    [--config-drive <value>] [--poll] [--admin-pass <value>]
                    [--access-ip-v4 <value>] [--access-ip-v6 <value>]
                    [--description <description>] [--tags <tags>]
                    [--return-reservation-id]
                    [--trusted-image-certificate-id <trusted-image-certificate-id>]
                    [--host <host>]
                    [--hypervisor-hostname <hypervisor-hostname>]
                    [--hostname <hostname>]
                    <name>

Boot a new server.

In order to create a server with pre-existing ports that contain a
``resource_request`` value, such as for guaranteed minimum bandwidth
quality of service support, microversion ``2.72`` is required.

**Positional arguments:**

``<name>``
  Name for the new server.

**Optional arguments:**

``--flavor <flavor>``
  Name or ID of flavor (see 'nova flavor-list').

``--image <image>``
  Name or ID of image (see 'glance image-list').

``--image-with <key=value>``
  Image metadata property (see 'glance image-show').

``--boot-volume <volume_id>``
  Volume ID to boot from.

``--snapshot <snapshot_id>``
  Snapshot ID to boot from (will create a
  volume).

``--min-count <number>``
  Boot at least <number> servers (limited by
  quota).

``--max-count <number>``
  Boot up to <number> servers (limited by
  quota).

``--meta <key=value>``
  Record arbitrary key/value metadata to
  /meta_data.json on the metadata server. Can be
  specified multiple times.

``--key-name <key-name>``
  Key name of keypair that should be created
  earlier with the command keypair-add.

``--user-data <user-data>``
  user data file to pass to be exposed by the
  metadata server.

``--availability-zone <availability-zone>``
  The availability zone for server placement.

``--security-groups <security-groups>``
  Comma separated list of security group names.

``--block-device-mapping <dev-name=mapping>``
  Block device mapping in the format
  <dev-name>=<id>:<type>:<size(GiB)>:<delete-on-terminate>.

``--block-device``
  key1=value1[,key2=value2...]
  Block device mapping with the keys: id=UUID
  (image_id, snapshot_id or volume_id only if
  using source image, snapshot or volume)
  source=source type (image, snapshot, volume or
  blank), dest=destination type of the block
  device (volume or local), bus=device's bus
  (e.g. uml, lxc, virtio, ...; if omitted,
  hypervisor driver chooses a suitable default,
  honoured only if device type is supplied)
  type=device type (e.g. disk, cdrom, ...;
  defaults to 'disk') device=name of the device
  (e.g. vda, xda, ...; if omitted, hypervisor
  driver chooses suitable device depending on
  selected bus; note the libvirt driver always
  uses default device names), size=size of the
  block device in MiB(for swap) and in GiB(for
  other formats) (if omitted, hypervisor driver
  calculates size), format=device will be
  formatted (e.g. swap, ntfs, ...; optional),
  bootindex=integer used for ordering the boot
  disks (for image backed instances it is equal
  to 0, for others need to be specified),
  shutdown=shutdown behaviour (either preserve
  or remove, for local destination set to
  remove), tag=device metadata tag
  (optional; supported by API versions '2.42'
  - '2.latest'), and volume_type=type of volume
  to create (either ID or name) when source is
  `blank`, `image` or `snapshot` and dest is `volume`
  (optional; supported by API versions '2.67'
  - '2.latest').

``--swap <swap_size>``
  Create and attach a local swap block device of
  <swap_size> MiB.

``--ephemeral``
  size=<size>[,format=<format>]
  Create and attach a local ephemeral block
  device of <size> GiB and format it to <format>.

``--hint <key=value>``
  Send arbitrary key/value pairs to the
  scheduler for custom use.

``--nic <auto,none,net-id=net-uuid,net-name=network-name,port-id=port-uuid,v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr,tag=tag>``
  Create a NIC on the server. Specify option
  multiple times to create multiple nics unless
  using the special 'auto' or 'none' values.
  auto: automatically allocate network resources
  if none are available. This cannot be
  specified with any other nic value and cannot
  be specified multiple times. none: do not
  attach a NIC at all. This cannot be specified
  with any other nic value and cannot be
  specified multiple times. net-id: attach NIC
  to network with a specific UUID. net-name:
  attach NIC to network with this name (either
  port-id or net-id or net-name must be
  provided), v4-fixed-ip: IPv4 fixed address for
  NIC (optional), v6-fixed-ip: IPv6 fixed
  address for NIC (optional), port-id: attach
  NIC to port with this UUID tag: interface
  metadata tag (optional) (either port-id or
  net-id must be provided). (Supported by API
  versions '2.42' - '2.latest')

``--config-drive <value>``
  Enable config drive. The value must be a
  boolean value.

``--poll``
  Report the new server boot progress until it
  completes.

``--admin-pass <value>``
  Admin password for the instance.

``--access-ip-v4 <value>``
  Alternative access IPv4 of the instance.

``--access-ip-v6 <value>``
  Alternative access IPv6 of the instance.

``--description <description>``
  Description for the server. (Supported by API
  versions '2.19' - '2.latest')

``--tags <tags>``
  Tags for the server.Tags must be separated by commas: --tags <tag1,tag2>
  (Supported by API versions '2.52' - '2.latest')

``--return-reservation-id``
  Return a reservation id bound to created servers.

``--trusted-image-certificate-id <trusted-image-certificate-id>``
  Trusted image certificate IDs used to validate certificates
  during the image signature verification process.
  Defaults to env[OS_TRUSTED_IMAGE_CERTIFICATE_IDS].
  May be specified multiple times to pass multiple trusted image
  certificate IDs. (Supported by API versions '2.63' - '2.latest')

``--host <host>``
  Requested host to create servers. Admin only by default.
  (Supported by API versions '2.74' - '2.latest')

``--hypervisor-hostname <hypervisor-hostname>``
  Requested hypervisor hostname to create servers. Admin only by default.
  (Supported by API versions '2.74' - '2.latest')

``--hostname <hostname>``
  Hostname for the instance. This sets the hostname stored in the
  metadata server: a utility such as cloud-init running on the guest
  is required to propagate these changes to the guest.
  (Supported by API versions '2.90' - '2.latest')

.. _nova_clear-password:

nova clear-password
-------------------

.. code-block:: console

   usage: nova clear-password <server>

Clear the admin password for a server from the metadata server. This action
does not actually change the instance server password.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_console-log:

nova console-log
----------------

.. code-block:: console

   usage: nova console-log [--length <length>] <server>

Get console log output of a server.

**Locale encoding issues**

If you encounter an error such as:

.. code-block:: console

  UnicodeEncodeError: 'ascii' codec can't encode characters in position

The solution to these problems is different depending on which locale your
computer is running in.

For instance, if you have a German Linux machine, you can fix the problem by
exporting the locale to de_DE.utf-8:

.. code-block:: console

  export LC_ALL=de_DE.utf-8
  export LANG=de_DE.utf-8

If you are on a US machine, en_US.utf-8 is the encoding of choice. On some
newer Linux systems, you could also try C.UTF-8 as the locale:

.. code-block:: console

  export LC_ALL=C.UTF-8
  export LANG=C.UTF-8

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--length <length>``
  Length in lines to tail.

.. _nova_delete:

nova delete
-----------

.. code-block:: console

   usage: nova delete [--all-tenants] <server> [<server> ...]

Immediately shut down and delete specified server(s).

**Positional arguments:**

``<server>``
  Name or ID of server(s).

**Optional arguments:**

``--all-tenants``
  Delete server(s) in another tenant by name (Admin only).

.. _nova_diagnostics:

nova diagnostics
----------------

.. code-block:: console

   usage: nova diagnostics <server>

Retrieve server diagnostics.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_evacuate:

nova evacuate
-------------

.. code-block:: console

   usage: nova evacuate [--password <password>] [--on-shared-storage] [--force] <server> [<host>]

Evacuate server from failed host.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<host>``
  Name or ID of the target host. If no host is
  specified, the scheduler will choose one.

**Optional arguments:**

``--password <password>``
  Set the provided admin password on the evacuated
  server. Not applicable if the server is on shared
  storage.

``--on-shared-storage``
  Specifies whether server files are located on shared
  storage. (Supported by API versions '2.0' - '2.13')

``--force``
  Force an evacuation by not verifying the provided destination host by the
  scheduler. (Supported by API versions '2.29' - '2.67')

  .. warning:: This could result in failures to actually evacuate the
    server to the specified host. It is recommended to either not specify
    a host so that the scheduler will pick one, or specify a host without
    ``--force``.

.. _nova_flavor-access-add:

nova flavor-access-add
----------------------

.. code-block:: console

   usage: nova flavor-access-add <flavor> <tenant_id>

Add flavor access for the given tenant.

**Positional arguments:**

``<flavor>``
  Flavor name or ID to add access for the given tenant.

``<tenant_id>``
  Tenant ID to add flavor access for.

.. _nova_flavor-access-list:

nova flavor-access-list
-----------------------

.. code-block:: console

   usage: nova flavor-access-list [--flavor <flavor>]

Print access information about the given flavor.

**Optional arguments:**

``--flavor <flavor>``
  Filter results by flavor name or ID.

.. _nova_flavor-access-remove:

nova flavor-access-remove
-------------------------

.. code-block:: console

   usage: nova flavor-access-remove <flavor> <tenant_id>

Remove flavor access for the given tenant.

**Positional arguments:**

``<flavor>``
  Flavor name or ID to remove access for the given tenant.

``<tenant_id>``
  Tenant ID to remove flavor access for.

.. _nova_flavor-create:

nova flavor-create
------------------

.. code-block:: console

   usage: nova flavor-create [--ephemeral <ephemeral>] [--swap <swap>]
                             [--rxtx-factor <factor>] [--is-public <is-public>]
                             [--description <description>]
                             <name> <id> <ram> <disk> <vcpus>

Create a new flavor.

**Positional arguments:**

``<name>``
  Unique name of the new flavor.

``<id>``
  Unique ID of the new flavor. Specifying 'auto' will
  generated a UUID for the ID.

``<ram>``
  Memory size in MiB.

``<disk>``
  Disk size in GiB.

``<vcpus>``
  Number of vcpus

**Optional arguments:**

``--ephemeral <ephemeral>``
  Ephemeral space size in GiB (default 0).

``--swap <swap>``
  Swap space size in MiB (default 0).

``--rxtx-factor <factor>``
  RX/TX factor (default 1).

``--is-public <is-public>``
  Make flavor accessible to the public (default
  true).

``--description <description>``
  A free form description of the flavor. Limited to 65535 characters
  in length. Only printable characters are allowed.
  (Supported by API versions '2.55' - '2.latest')

.. _nova_flavor-delete:

nova flavor-delete
------------------

.. code-block:: console

   usage: nova flavor-delete <flavor>

Delete a specific flavor

**Positional arguments:**

``<flavor>``
  Name or ID of the flavor to delete.

.. _nova_flavor-key:

nova flavor-key
---------------

.. code-block:: console

   usage: nova flavor-key <flavor> <action> <key=value> [<key=value> ...]

Set or unset extra_spec for a flavor.

**Positional arguments:**

``<flavor>``
  Name or ID of flavor.

``<action>``
  Actions: 'set' or 'unset'.

``<key=value>``
  Extra_specs to set/unset (only key is necessary on unset).

.. _nova_flavor-list:

nova flavor-list
----------------

.. code-block:: console

   usage: nova flavor-list [--extra-specs] [--all] [--marker <marker>]
                           [--min-disk <min-disk>] [--min-ram <min-ram>]
                           [--limit <limit>] [--sort-key <sort-key>]
                           [--sort-dir <sort-dir>]

Print a list of available 'flavors' (sizes of servers).

**Optional arguments:**

``--extra-specs``
  Get extra-specs of each flavor.

``--all``
  Display all flavors (Admin only).

``--marker <marker>``
  The last flavor ID of the previous page; displays
  list of flavors after "marker".

``--min-disk <min-disk>``
  Filters the flavors by a minimum disk space, in GiB.

``--min-ram <min-ram>``
  Filters the flavors by a minimum RAM, in MiB.

``--limit <limit>``
  Maximum number of flavors to display. If limit is
  bigger than 'CONF.api.max_limit' option of Nova API,
  limit 'CONF.api.max_limit' will be used instead.

``--sort-key <sort-key>``
  Flavors list sort key.

``--sort-dir <sort-dir>``
  Flavors list sort direction.

.. _nova_flavor-show:

nova flavor-show
----------------

.. code-block:: console

   usage: nova flavor-show <flavor>

Show details about the given flavor.

**Positional arguments:**

``<flavor>``
  Name or ID of flavor.

nova flavor-update
------------------

.. code-block:: console

   usage: nova flavor-update <flavor> <description>

Update the description of an existing flavor.
(Supported by API versions '2.55' - '2.latest')
[hint: use '--os-compute-api-version' flag to show help message for proper
version]

.. versionadded:: 10.0.0

**Positional arguments**

``<flavor>``
  Name or ID of the flavor to update.

``<description>``
  A free form description of the flavor. Limited to 65535
  characters in length. Only printable characters are allowed.

.. _nova_force-delete:

nova force-delete
-----------------

.. code-block:: console

   usage: nova force-delete <server>

Force delete a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_get-mks-console:

nova get-mks-console
--------------------

.. code-block:: console

   usage: nova get-mks-console <server>

Get an MKS console to a server. (Supported by API versions '2.8' - '2.latest')
[hint: use '--os-compute-api-version' flag to show help message for proper
version]

.. versionadded:: 3.0.0

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_get-password:

nova get-password
-----------------

.. code-block:: console

   usage: nova get-password <server> [<private-key>]

Get the admin password for a server. This operation calls the metadata service
to query metadata information and does not read password information from the
server itself.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<private-key>``
  Private key (used locally to decrypt password) (Optional).
  When specified, the command displays the clear (decrypted) VM
  password. When not specified, the ciphered VM password is
  displayed.

.. _nova_get-rdp-console:

nova get-rdp-console
--------------------

.. code-block:: console

   usage: nova get-rdp-console <server> <console-type>

Get a rdp console to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<console-type>``
  Type of rdp console ("rdp-html5").

.. _nova_get-serial-console:

nova get-serial-console
-----------------------

.. code-block:: console

   usage: nova get-serial-console [--console-type CONSOLE_TYPE] <server>

Get a serial console to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--console-type CONSOLE_TYPE``
  Type of serial console, default="serial".

.. _nova_get-spice-console:

nova get-spice-console
----------------------

.. code-block:: console

   usage: nova get-spice-console <server> <console-type>

Get a spice console to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<console-type>``
  Type of spice console ("spice-html5").

.. _nova_get-vnc-console:

nova get-vnc-console
--------------------

.. code-block:: console

   usage: nova get-vnc-console <server> <console-type>

Get a vnc console to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<console-type>``
  Type of vnc console ("novnc" or "xvpvnc").

.. _nova_host-evacuate:

nova host-evacuate
------------------

.. code-block:: console

   usage: nova host-evacuate [--target_host <target_host>] [--force] [--strict]
                             <host>

Evacuate all instances from failed host.

**Positional arguments:**

``<host>``
  The hypervisor hostname (or pattern) to search for.

  .. warning::

    Use a fully qualified domain name if you only want to evacuate from
    a specific host.

**Optional arguments:**

``--target_host <target_host>``
  Name of target host. If no host is specified
  the scheduler will select a target.

``--force``
  Force an evacuation by not verifying the provided destination host by the
  scheduler. (Supported by API versions '2.29' - '2.67')

  .. warning:: This could result in failures to actually evacuate the
    server to the specified host. It is recommended to either not specify
    a host so that the scheduler will pick one, or specify a host without
    ``--force``.

``--strict``
  Evacuate host with exact hypervisor hostname match

.. _nova_host-evacuate-live:

nova host-evacuate-live
-----------------------

.. code-block:: console

   usage: nova host-evacuate-live [--target-host <target_host>] [--block-migrate]
                                  [--max-servers <max_servers>] [--force]
                                  [--strict]
                                  <host>

Live migrate all instances off the specified host to other available hosts.

**Positional arguments:**

``<host>``
  Name of host.
  The hypervisor hostname (or pattern) to search for.

  .. warning::

    Use a fully qualified domain name if you only want to live migrate
    from a specific host.

**Optional arguments:**

``--target-host <target_host>``
  Name of target host. If no host is specified, the scheduler will choose
  one.

``--block-migrate``
  Enable block migration. (Default=auto)
  (Supported by API versions '2.25' - '2.latest')

``--max-servers <max_servers>``
  Maximum number of servers to live migrate
  simultaneously

``--force``
  Force a live-migration by not verifying the provided destination host by
  the scheduler. (Supported by API versions '2.30' - '2.67')

  .. warning:: This could result in failures to actually live migrate the
    servers to the specified host. It is recommended to either not specify
    a host so that the scheduler will pick one, or specify a host without
    ``--force``.

``--strict``
  live Evacuate host with exact hypervisor hostname match

.. _nova_host-meta:

nova host-meta
--------------

.. code-block:: console

   usage: nova host-meta [--strict] <host> <action> <key=value> [<key=value> ...]

Set or Delete metadata on all instances of a host.

**Positional arguments:**

``<host>``
  The hypervisor hostname (or pattern) to search for.

  .. warning::

    Use a fully qualified domain name if you only want to update
    metadata for servers on a specific host.

``<action>``
  Actions: 'set' or 'delete'

``<key=value>``
  Metadata to set or delete (only key is necessary on delete)

**Optional arguments:**

``--strict``
  Set host-meta to the hypervisor with exact hostname match

.. _nova_host-servers-migrate:

nova host-servers-migrate
-------------------------

.. code-block:: console

   usage: nova host-servers-migrate [--strict] <host>

Cold migrate all instances off the specified host to other available hosts.

**Positional arguments:**

``<host>``
  Name of host.
  The hypervisor hostname (or pattern) to search for.

  .. warning::

    Use a fully qualified domain name if you only want to cold migrate
    from a specific host.

**Optional arguments:**

``--strict``
  Migrate host with exact hypervisor hostname match

.. _nova_hypervisor-list:

nova hypervisor-list
--------------------

.. code-block:: console

   usage: nova hypervisor-list [--matching <hostname>] [--marker <marker>]
                               [--limit <limit>]

List hypervisors. (Supported by API versions '2.0' - '2.latest') [hint: use
'--os-compute-api-version' flag to show help message for proper version]

**Optional arguments:**

``--matching <hostname>``
  List hypervisors matching the given <hostname>. If
  matching is used limit and marker options will be
  ignored.

``--marker <marker>``
  The last hypervisor of the previous page; displays
  list of hypervisors after "marker".
  (Supported by API versions '2.33' - '2.latest')

``--limit <limit>``
  Maximum number of hypervisors to display. If limit is
  bigger than 'CONF.api.max_limit' option of Nova API,
  limit 'CONF.api.max_limit' will be used instead.
  (Supported by API versions '2.33' - '2.latest')

.. _nova_hypervisor-servers:

nova hypervisor-servers
-----------------------

.. code-block:: console

   usage: nova hypervisor-servers <hostname>

List servers belonging to specific hypervisors.

**Positional arguments:**

``<hostname>``
  The hypervisor hostname (or pattern) to search for.

.. _nova_hypervisor-show:

nova hypervisor-show
--------------------

.. code-block:: console

   usage: nova hypervisor-show [--wrap <integer>] <hypervisor>

Display the details of the specified hypervisor.

**Positional arguments:**

``<hypervisor>``
  Name or ID of the hypervisor.
  Starting with microversion 2.53 the ID must be a UUID.

**Optional arguments:**

``--wrap <integer>``
  Wrap the output to a specified length. Default is 40 or 0
  to disable

.. _nova_hypervisor-stats:

nova hypervisor-stats
---------------------

.. code-block:: console

   usage: nova hypervisor-stats

Get hypervisor statistics over all compute nodes.

.. _nova_hypervisor-uptime:

nova hypervisor-uptime
----------------------

.. code-block:: console

   usage: nova hypervisor-uptime <hypervisor>

Display the uptime of the specified hypervisor.

**Positional arguments:**

``<hypervisor>``
  Name or ID of the hypervisor.
  Starting with microversion 2.53 the ID must be a UUID.

.. _nova_image-create:

nova image-create
-----------------

.. code-block:: console

   usage: nova image-create [--metadata <key=value>] [--show] [--poll]
                            <server> <name>

Create a new image by taking a snapshot of a running server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<name>``
  Name of snapshot.

**Optional arguments:**

``--metadata <key=value>``
  Record arbitrary key/value metadata to
  /meta_data.json on the metadata server. Can be
  specified multiple times.

``--show``
  Print image info.

``--poll``
  Report the snapshot progress and poll until image
  creation is complete.

.. _nova_instance-action:

nova instance-action
--------------------

.. code-block:: console

   usage: nova instance-action <server> <request_id>

Show an action.

**Positional arguments:**

``<server>``
  Name or UUID of the server to show actions for. Only UUID can
  be used to show actions for a deleted server. (Supported by
  API versions '2.21' - '2.latest')

``<request_id>``
  Request ID of the action to get.

.. _nova_instance-action-list:

nova instance-action-list
-------------------------

.. code-block:: console

   usage: nova instance-action-list [--marker <marker>] [--limit <limit>]
                                    [--changes-since <changes_since>]
                                    [--changes-before <changes_before>]
                                    <server>

List actions on a server.

**Positional arguments:**

``<server>``
  Name or UUID of the server to list actions for. Only UUID can be
  used to list actions on a deleted server. (Supported by API
  versions '2.21' - '2.latest')

**Optional arguments:**

``--marker <marker>``
  The last instance action of the previous page; displays list of actions
  after "marker". (Supported by API versions '2.58' - '2.latest')

``--limit <limit>``
  Maximum number of instance actions to display. Note that there is
  a configurable max limit on the server, and the limit that is used will be
  the minimum of what is requested here and what is configured
  in the server. (Supported by API versions '2.58' - '2.latest')

``--changes-since <changes_since>``
  List only instance actions changed later or equal to a certain
  point of time. The provided time should be an ISO 8061 formatted time.
  e.g. 2016-03-04T06:27:59Z. (Supported by API versions '2.58' - '2.latest')

``--changes-before <changes_before>``
  List only instance actions changed earlier or equal to a certain
  point of time. The provided time should be an ISO 8061 formatted time.
  e.g. 2016-03-04T06:27:59Z. (Supported by API versions '2.66' - '2.latest')

.. _nova_instance-usage-audit-log:

nova instance-usage-audit-log
-----------------------------

.. code-block:: console

   usage: nova instance-usage-audit-log [--before <before>]

List/Get server usage audits.

**Optional arguments:**

``--before <before>``
  Filters the response by the date and time before which to list usage audits.
  The date and time stamp format is as follows: CCYY-MM-DD hh:mm:ss.NNNNNN
  ex 2015-08-27 09:49:58 or 2015-08-27 09:49:58.123456.

.. _nova_interface-attach:

nova interface-attach
---------------------

.. code-block:: console

   usage: nova interface-attach [--port-id <port_id>] [--net-id <net_id>]
                                [--fixed-ip <fixed_ip>] [--tag <tag>]
                                <server>

Attach a network interface to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--port-id <port_id>``
  Port ID.

``--net-id <net_id>``
  Network ID

``--fixed-ip <fixed_ip>``
  Requested fixed IP.

``--tag <tag>``
  Tag for the attached interface.
  (Supported by API versions '2.49' - '2.latest')

.. _nova_interface-detach:

nova interface-detach
---------------------

.. code-block:: console

   usage: nova interface-detach <server> <port_id>

Detach a network interface from a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<port_id>``
  Port ID.

.. _nova_interface-list:

nova interface-list
-------------------

.. code-block:: console

   usage: nova interface-list <server>

List interfaces attached to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_keypair-add:

nova keypair-add
----------------

.. code-block:: console

   usage: nova keypair-add [--pub-key <pub-key>] [--key-type <key-type>]
                           [--user <user-id>]
                           <name>

Create a new key pair for use with servers.

**Positional arguments:**

``<name>``
  Name of key.

**Optional arguments:**

``--pub-key <pub-key>``
  Path to a public ssh key.

``--key-type <key-type>``
  Keypair type. Can be ssh or x509. (Supported by API
  versions '2.2' - '2.latest')

``--user <user-id>``
  ID of user to whom to add key-pair (Admin only).
  (Supported by API versions '2.10' - '2.latest')

.. _nova_keypair-delete:

nova keypair-delete
-------------------

.. code-block:: console

   usage: nova keypair-delete [--user <user-id>] <name>

Delete keypair given by its name. (Supported by API versions '2.0' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

**Positional arguments:**

``<name>``
  Keypair name to delete.

**Optional arguments:**

``--user <user-id>``
  ID of key-pair owner (Admin only).

.. _nova_keypair-list:

nova keypair-list
-----------------

.. code-block:: console

   usage: nova keypair-list [--user <user-id>] [--marker <marker>]
                            [--limit <limit>]

Print a list of keypairs for a user (Supported by API versions '2.0' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

**Optional arguments:**

``--user <user-id>``
  List key-pairs of specified user ID (Admin only).

``--marker <marker>``
  The last keypair of the previous page; displays list of
  keypairs after "marker".

``--limit <limit>``
  Maximum number of keypairs to display. If limit is bigger
  than 'CONF.api.max_limit' option of Nova API, limit
  'CONF.api.max_limit' will be used instead.

.. _nova_keypair-show:

nova keypair-show
-----------------

.. code-block:: console

   usage: nova keypair-show [--user <user-id>] <keypair>

Show details about the given keypair. (Supported by API versions '2.0' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

**Positional arguments:**

``<keypair>``
  Name of keypair.

**Optional arguments:**

``--user <user-id>``
  ID of key-pair owner (Admin only).

.. _nova_limits:

nova limits
-----------

.. code-block:: console

   usage: nova limits [--tenant [<tenant>]] [--reserved]

Print rate and absolute limits.

**Optional arguments:**

``--tenant [<tenant>]``
  Display information from single tenant (Admin only).

``--reserved``
  Include reservations count.

.. _nova_list:

nova list
---------

.. code-block:: console

   usage: nova list [--reservation-id <reservation-id>] [--ip <ip-regexp>]
                    [--ip6 <ip6-regexp>] [--name <name-regexp>]
                    [--status <status>] [--flavor <flavor>] [--image <image>]
                    [--host <hostname>] [--all-tenants [<0|1>]]
                    [--tenant [<tenant>]] [--user [<user>]] [--deleted]
                    [--fields <fields>] [--minimal]
                    [--sort <key>[:<direction>]] [--marker <marker>]
                    [--limit <limit>] [--availability-zone <availability_zone>]
                    [--key-name <key_name>] [--[no-]config-drive]
                    [--progress <progress>] [--vm-state <vm_state>]
                    [--task-state <task_state>] [--power-state <power_state>]
                    [--changes-since <changes_since>]
                    [--changes-before <changes_before>]
                    [--tags <tags>] [--tags-any <tags-any>]
                    [--not-tags <not-tags>] [--not-tags-any <not-tags-any>]
                    [--locked]

List servers.

Note that from microversion 2.69, during partial infrastructure failures in the
deployment, the output of this command may return partial results for the servers
present in the failure domain.

**Optional arguments:**

``--reservation-id <reservation-id>``
  Only return servers that match reservation-id.

``--ip <ip-regexp>``
  Search with regular expression match by IP
  address.

``--ip6 <ip6-regexp>``
  Search with regular expression match by IPv6
  address.

``--name <name-regexp>``
  Search with regular expression match by name.

``--status <status>``
  Search by server status.

``--flavor <flavor>``
  Search by flavor name or ID.

``--image <image>``
  Search by image name or ID.

``--host <hostname>``
  Search servers by hostname to which they are
  assigned (Admin only).

``--all-tenants [<0|1>]``
  Display information from all tenants (Admin
  only).

``--tenant [<tenant>]``
  Display information from single tenant (Admin
  only).

``--user [<user>]``
  Display information from single user (Admin
  only until microversion 2.82).

``--deleted``
  Only display deleted servers (Admin only).

``--fields <fields>``
  Comma-separated list of fields to display. Use
  the show command to see which fields are
  available.

``--minimal``
  Get only UUID and name.

``--sort <key>[:<direction>]``
  Comma-separated list of sort keys and
  directions in the form of <key>[:<asc|desc>].
  The direction defaults to descending if not
  specified.

``--marker <marker>``
  The last server UUID of the previous page;
  displays list of servers after "marker".

``--limit <limit>``
  Maximum number of servers to display. If limit
  == -1, all servers will be displayed. If limit
  is bigger than 'CONF.api.max_limit' option of
  Nova API, limit 'CONF.api.max_limit' will be
  used instead.

``--availability-zone <availability_zone>``
  Display servers based on their availability zone
  (Admin only until microversion 2.82).

``--key-name <key_name>``
  Display servers based on their keypair name
  (Admin only until microversion 2.82).

``--config-drive``
  Display servers that have a config drive attached.
  It is mutually exclusive with '--no-config-drive'.
  (Admin only until microversion 2.82).

``--no-config-drive``
  Display servers that do not have a config drive attached.
  It is mutually exclusive with '--config-drive'.
  (Admin only until microversion 2.82).

``--progress <progress>``
  Display servers based on their progress value
  (Admin only until microversion 2.82).

``--vm-state <vm_state>``
  Display servers based on their vm_state value
  (Admin only until microversion 2.82).

``--task-state <task_state>``
  Display servers based on their task_state value
  (Admin only until microversion 2.82).

``--power-state <power_state>``
  Display servers based on their power_state value
  (Admin only until microversion 2.82).

``--changes-since <changes_since>``
  List only servers changed later or equal to a
  certain point of time. The provided time should
  be an ISO 8061 formatted time. e.g.
  2016-03-04T06:27:59Z .

``--changes-before <changes_before>``
  List only servers changed earlier or equal to a
  certain point of time. The provided time should
  be an ISO 8061 formatted time. e.g.
  2016-03-05T06:27:59Z . (Supported by API versions
  '2.66' - '2.latest')

``--tags <tags>``
  The given tags must all be present for a
  server to be included in the list result.
  Boolean expression in this case is 't1 AND
  t2'. Tags must be separated by commas: --tags
  <tag1,tag2> (Supported by API versions '2.26'
  - '2.latest')

``--tags-any <tags-any>``
  If one of the given tags is present the server
  will be included in the list result. Boolean
  expression in this case is 't1 OR t2'. Tags
  must be separated by commas: --tags-any
  <tag1,tag2> (Supported by API versions '2.26'
  - '2.latest')

``--not-tags <not-tags>``
  Only the servers that do not have any of the
  given tags will be included in the list
  results. Boolean expression in this case is
  'NOT(t1 AND t2)'. Tags must be separated by
  commas: --not-tags <tag1,tag2> (Supported by
  API versions '2.26' - '2.latest')

``--not-tags-any <not-tags-any>``
  Only the servers that do not have at least one
  of the given tags will be included in the list
  result. Boolean expression in this case is
  'NOT(t1 OR t2)'. Tags must be separated by
  commas: --not-tags-any <tag1,tag2> (Supported
  by API versions '2.26' - '2.latest')

``--locked <locked>``
  Display servers based on their locked value. A
  value must be specified; eg. 'true' will list
  only locked servers and 'false' will list only
  unlocked servers. (Supported by API versions
  '2.73' - '2.latest')

.. _nova_list-secgroup:

nova list-secgroup
------------------

.. code-block:: console

   usage: nova list-secgroup <server>

List Security Group(s) of a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_live-migration:

nova live-migration
-------------------

.. code-block:: console

   usage: nova live-migration [--block-migrate] [--force] <server> [<host>]

Migrate running server to a new machine.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<host>``
  Destination host name. If no host is specified, the scheduler will choose
  one.

**Optional arguments:**

``--block-migrate``
  True in case of block_migration.
  (Default=auto:live_migration) (Supported by API versions
  '2.25' - '2.latest')

``--force``
  Force a live-migration by not verifying the provided destination host by
  the scheduler. (Supported by API versions '2.30' - '2.67')

  .. warning:: This could result in failures to actually live migrate the
    server to the specified host. It is recommended to either not specify
    a host so that the scheduler will pick one, or specify a host without
    ``--force``.

.. _nova_live-migration-abort:

nova live-migration-abort
-------------------------

.. code-block:: console

   usage: nova live-migration-abort <server> <migration>

Abort an on-going live migration. (Supported by API versions '2.24' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

For microversions from 2.24 to 2.64 the migration status must be ``running``;
for microversion 2.65 and greater, the migration status can also be ``queued``
and ``preparing``.

.. versionadded:: 3.3.0

**Positional arguments:**

``<server>``
  Name or ID of server.

``<migration>``
  ID of migration.

.. _nova_live-migration-force-complete:

nova live-migration-force-complete
----------------------------------

.. code-block:: console

   usage: nova live-migration-force-complete <server> <migration>

Force on-going live migration to complete. (Supported by API versions '2.22' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

.. versionadded:: 3.3.0

**Positional arguments:**

``<server>``
  Name or ID of server.

``<migration>``
  ID of migration.

.. _nova_lock:

nova lock
---------

.. code-block:: console

   usage: nova lock [--reason <reason>] <server>

Lock a server. A normal (non-admin) user will not be able to execute actions
on a locked server.

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--reason <reason>``
  Reason for locking the server. (Supported by API versions
  '2.73' - '2.latest')

.. _nova_meta:

nova meta
---------

.. code-block:: console

   usage: nova meta <server> <action> <key=value> [<key=value> ...]

Set or delete metadata on a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<action>``
  Actions: 'set' or 'delete'.

``<key=value>``
  Metadata to set or delete (only key is necessary on delete).

.. _nova_migrate:

nova migrate
------------

.. code-block:: console

   usage: nova migrate [--host <host>] [--poll] <server>

Migrate a server. The new host will be selected by the scheduler.

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--host <host>``
  Destination host name. (Supported by API versions '2.56' - '2.latest')

``--poll``
  Report the server migration progress until it completes.

.. _nova_migration-list:

nova migration-list
-------------------

.. code-block:: console

   usage: nova migration-list [--instance-uuid <instance_uuid>]
                              [--host <host>]
                              [--status <status>]
                              [--migration-type <migration_type>]
                              [--source-compute <source_compute>]
                              [--marker <marker>]
                              [--limit <limit>]
                              [--changes-since <changes_since>]
                              [--changes-before <changes_before>]
                              [--project-id <project_id>]
                              [--user-id <user_id>]

Print a list of migrations.

**Examples**

To see the list of evacuation operations *from* a compute service host:

.. code-block:: console

  nova migration-list --migration-type evacuation --source-compute host.foo.bar

**Optional arguments:**

``--instance-uuid <instance_uuid>``
  Fetch migrations for the given instance.

``--host <host>``
  Fetch migrations for the given source or destination host.

``--status <status>``
  Fetch migrations for the given status.

``--migration-type <migration_type>``
  Filter migrations by type. Valid values are:

  * evacuation
  * live-migration
  * migration

    .. note:: This is a cold migration.

  * resize

``--source-compute <source_compute>``
  Filter migrations by source compute host name.

``--marker <marker>``
  The last migration of the previous page; displays list of migrations after
  "marker". Note that the marker is the migration UUID.
  (Supported by API versions '2.59' - '2.latest')

``--limit <limit>``
  Maximum number of migrations to display. Note that there is a configurable
  max limit on the server, and the limit that is used will be the minimum of
  what is requested here and what is configured in the server.
  (Supported by API versions '2.59' - '2.latest')

``--changes-since <changes_since>``
  List only migrations changed later or equal to a certain
  point of time. The provided time should be an ISO 8061 formatted time.
  e.g. 2016-03-04T06:27:59Z . (Supported by API versions '2.59' - '2.latest')

``--changes-before <changes_before>``
  List only migrations changed earlier or equal to a certain
  point of time. The provided time should be an ISO 8061 formatted time.
  e.g. 2016-03-04T06:27:59Z . (Supported by API versions '2.66' - '2.latest')

``--project-id <project_id>``
  Filter the migrations by the given project ID.
  (Supported by API versions '2.80' - '2.latest')

``--user-id <user_id>``
  Filter the migrations by the given user ID.
  (Supported by API versions '2.80' - '2.latest')

.. _nova_pause:

nova pause
----------

.. code-block:: console

   usage: nova pause <server>

Pause a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_quota-class-show:

nova quota-class-show
---------------------

.. code-block:: console

   usage: nova quota-class-show <class>

List the quotas for a quota class.

**Positional arguments:**

``<class>``
  Name of quota class to list the quotas for.

.. _nova_quota-class-update:

nova quota-class-update
-----------------------

.. code-block:: console

   usage: nova quota-class-update [--instances <instances>] [--cores <cores>]
                                  [--ram <ram>]
                                  [--metadata-items <metadata-items>]
                                  [--key-pairs <key-pairs>]
                                  [--server-groups <server-groups>]
                                  [--server-group-members <server-group-members>]
                                  <class>

Update the quotas for a quota class. (Supported by API versions '2.0' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

**Positional arguments:**

``<class>``
  Name of quota class to set the quotas for.

**Optional arguments:**

``--instances <instances>``
  New value for the "instances" quota.

``--cores <cores>``
  New value for the "cores" quota.

``--ram <ram>``
  New value for the "ram" quota.

``--metadata-items <metadata-items>``
  New value for the "metadata-items" quota.

``--key-pairs <key-pairs>``
  New value for the "key-pairs" quota.

``--server-groups <server-groups>``
  New value for the "server-groups" quota.

``--server-group-members <server-group-members>``
  New value for the "server-group-members"
  quota.

.. _nova_quota-defaults:

nova quota-defaults
-------------------

.. code-block:: console

   usage: nova quota-defaults [--tenant <tenant-id>]

List the default quotas for a tenant.

**Optional arguments:**

``--tenant <tenant-id>``
  ID of tenant to list the default quotas for.

.. _nova_quota-delete:

nova quota-delete
-----------------

.. code-block:: console

   usage: nova quota-delete --tenant <tenant-id> [--user <user-id>]

Delete quota for a tenant/user so their quota will Revert back to default.

**Optional arguments:**

``--tenant <tenant-id>``
  ID of tenant to delete quota for.

``--user <user-id>``
  ID of user to delete quota for.

.. _nova_quota-show:

nova quota-show
---------------

.. code-block:: console

   usage: nova quota-show [--tenant <tenant-id>] [--user <user-id>] [--detail]

List the quotas for a tenant/user.

**Optional arguments:**

``--tenant <tenant-id>``
  ID of tenant to list the quotas for.

``--user <user-id>``
  ID of user to list the quotas for.

``--detail``
  Show detailed info (limit, reserved, in-use).

.. _nova_quota-update:

nova quota-update
-----------------

.. code-block:: console

   usage: nova quota-update [--user <user-id>] [--instances <instances>]
                            [--cores <cores>] [--ram <ram>]
                            [--metadata-items <metadata-items>]
                            [--key-pairs <key-pairs>]
                            [--server-groups <server-groups>]
                            [--server-group-members <server-group-members>]
                            [--force]
                            <tenant-id>

Update the quotas for a tenant/user. (Supported by API versions '2.0' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

**Positional arguments:**

``<tenant-id>``
  ID of tenant to set the quotas for.

**Optional arguments:**

``--user <user-id>``
  ID of user to set the quotas for.

``--instances <instances>``
  New value for the "instances" quota.

``--cores <cores>``
  New value for the "cores" quota.

``--ram <ram>``
  New value for the "ram" quota.

``--metadata-items <metadata-items>``
  New value for the "metadata-items" quota.

``--key-pairs <key-pairs>``
  New value for the "key-pairs" quota.

``--server-groups <server-groups>``
  New value for the "server-groups" quota.

``--server-group-members <server-group-members>``
  New value for the "server-group-members"
  quota.

``--force``
  Whether force update the quota even if the
  already used and reserved exceeds the new
  quota.

.. _nova_reboot:

nova reboot
-----------

.. code-block:: console

   usage: nova reboot [--hard] [--poll] <server> [<server> ...]

Reboot a server.

**Positional arguments:**

``<server>``
  Name or ID of server(s).

**Optional arguments:**

``--hard``
  Perform a hard reboot (instead of a soft one). Note: Ironic does
  not currently support soft reboot; consequently, bare metal nodes
  will always do a hard reboot, regardless of the use of this
  option.

``--poll``
  Poll until reboot is complete.

.. _nova_rebuild:

nova rebuild
------------

.. code-block:: console

   usage: nova rebuild [--rebuild-password <rebuild-password>] [--poll]
                       [--minimal] [--preserve-ephemeral] [--name <name>]
                       [--description <description>] [--meta <key=value>]
                       [--key-name <key-name>] [--key-unset]
                       [--user-data <user-data>] [--user-data-unset]
                       [--trusted-image-certificate-id <trusted-image-certificate-id>]
                       [--trusted-image-certificates-unset]
                       [--hostname <hostname>]
                       <server> <image>

Shutdown, re-image, and re-boot a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<image>``
  Name or ID of new image.

**Optional arguments:**

``--rebuild-password <rebuild-password>``
  Set the provided admin password on the rebuilt
  server.

``--poll``
  Report the server rebuild progress until it
  completes.

``--minimal``
  Skips flavor/image lookups when showing
  servers.

``--preserve-ephemeral``
  Preserve the default ephemeral storage
  partition on rebuild.

``--name <name>``
  Name for the new server.

``--description <description>``
  New description for the server. (Supported by
  API versions '2.19' - '2.latest')

``--meta <key=value>``
  Record arbitrary key/value metadata to
  /meta_data.json on the metadata server. Can be
  specified multiple times.

``--key-name <key-name>``
  Keypair name to set in the server. Cannot be specified with
  the '--key-unset' option.
  (Supported by API versions '2.54' - '2.latest')

``--key-unset``
  Unset keypair in the server. Cannot be specified with
  the '--key-name' option.
  (Supported by API versions '2.54' - '2.latest')

``--user-data <user-data>``
  User data file to pass to be exposed by the metadata server.
  (Supported by API versions '2.57' - '2.latest')

``--user-data-unset``
  Unset user_data in the server. Cannot be specified with
  the '--user-data' option.
  (Supported by API versions '2.57' - '2.latest')

``--trusted-image-certificate-id <trusted-image-certificate-id>``
  Trusted image certificate IDs used to validate certificates
  during the image signature verification process.
  Defaults to env[OS_TRUSTED_IMAGE_CERTIFICATE_IDS].
  May be specified multiple times to pass multiple trusted image
  certificate IDs. (Supported by API versions '2.63' - '2.latest')

``--trusted-image-certificates-unset``
  Unset trusted_image_certificates in the server. Cannot be
  specified with the ``--trusted-image-certificate-id`` option.
  (Supported by API versions '2.63' - '2.latest')

``--hostname <hostname>``
  New hostname for the instance. This only updates the hostname
  stored in the metadata server: a utility running on the guest
  is required to propagate these changes to the guest.
  (Supported by API versions '2.90' - '2.latest')

.. _nova_refresh-network:

nova refresh-network
--------------------

.. code-block:: console

   usage: nova refresh-network <server>

Refresh server network information.

**Positional arguments:**

``<server>``
  Name or ID of a server for which the network cache should be
  refreshed from neutron (Admin only).

.. _nova_remove-secgroup:

nova remove-secgroup
--------------------

.. code-block:: console

   usage: nova remove-secgroup <server> <secgroup>

Remove a Security Group from a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<secgroup>``
  Name of Security Group.

.. _nova_rescue:

nova rescue
-----------

.. code-block:: console

   usage: nova rescue [--password <password>] [--image <image>] <server>

Reboots a server into rescue mode, which starts the machine from either the
initial image or a specified image, attaching the current boot disk as
secondary.

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--password <password>``
  The admin password to be set in the rescue
  environment.

``--image <image>``
  The image to rescue with.

.. _nova_reset-network:

nova reset-network
------------------

.. code-block:: console

   usage: nova reset-network <server>

Reset network of a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_reset-state:

nova reset-state
----------------

.. code-block:: console

   usage: nova reset-state [--all-tenants] [--active] <server> [<server> ...]

Reset the state of a server.

**Positional arguments:**

``<server>``
  Name or ID of server(s).

**Optional arguments:**

``--all-tenants``
  Reset state server(s) in another tenant by name (Admin only).

``--active``
  Request the server be reset to "active" state instead of
  "error" state (the default).

.. _nova_resize:

nova resize
-----------

.. code-block:: console

   usage: nova resize [--poll] <server> <flavor>

Resize a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<flavor>``
  Name or ID of new flavor.

**Optional arguments:**

``--poll``
  Report the server resize progress until it completes.

.. _nova_resize-confirm:

nova resize-confirm
-------------------

.. code-block:: console

   usage: nova resize-confirm <server>

Confirm a previous resize.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_resize-revert:

nova resize-revert
------------------

.. code-block:: console

   usage: nova resize-revert <server>

Revert a previous resize (and return to the previous VM).

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_restore:

nova restore
------------

.. code-block:: console

   usage: nova restore <server>

Restore a soft-deleted server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_resume:

nova resume
-----------

.. code-block:: console

   usage: nova resume <server>

Resume a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_server-group-create:

nova server-group-create
------------------------

.. code-block:: console

   usage: nova server-group-create [--rules <key=value>] <name> <policy>

Create a new server group with the specified details.

**Positional arguments:**

``<name>``
  Server group name.

``<policy>``
  Policy for the server groups.

**Optional arguments:**

``--rule``
  Policy rules for the server groups. (Supported by API versions
  '2.64' - '2.latest'）. Currently, only the ``max_server_per_host`` rule
  is supported for the ``anti-affinity`` policy. The ``max_server_per_host``
  rule allows specifying how many members of the anti-affinity group can
  reside on the same compute host. If not specified, only one member from
  the same anti-affinity group can reside on a given host.

.. _nova_server-group-delete:

nova server-group-delete
------------------------

.. code-block:: console

   usage: nova server-group-delete <id> [<id> ...]

Delete specific server group(s).

**Positional arguments:**

``<id>``
  Unique ID(s) of the server group to delete.

.. _nova_server-group-get:

nova server-group-get
---------------------

.. code-block:: console

   usage: nova server-group-get <id>

Get a specific server group.

**Positional arguments:**

``<id>``
  Unique ID of the server group to get.

.. _nova_server-group-list:

nova server-group-list
----------------------

.. code-block:: console

   usage: nova server-group-list [--limit <limit>] [--offset <offset>]
                                 [--all-projects]

Print a list of all server groups.

**Optional arguments:**

``--limit <limit>``
  Maximum number of server groups to display. If limit is
  bigger than 'CONF.api.max_limit' option of Nova API,
  limit 'CONF.api.max_limit' will be used instead.

``--offset <offset>``
  The offset of groups list to display; use with limit to
  return a slice of server groups.

``--all-projects``
  Display server groups from all projects (Admin only).

.. _nova_server-migration-list:

nova server-migration-list
--------------------------

.. code-block:: console

   usage: nova server-migration-list <server>

Get the migrations list of specified server. (Supported by API versions '2.23'
- '2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

.. versionadded:: 3.3.0

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_server-migration-show:

nova server-migration-show
--------------------------

.. code-block:: console

   usage: nova server-migration-show <server> <migration>

Get the migration of specified server. (Supported by API versions '2.23' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

.. versionadded:: 3.3.0

**Positional arguments:**

``<server>``
  Name or ID of server.

``<migration>``
  ID of migration.

.. _nova_server-tag-add:

nova server-tag-add
-------------------

.. code-block:: console

   usage: nova server-tag-add <server> <tag> [<tag> ...]

Add one or more tags to a server. (Supported by API versions '2.26' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

.. versionadded:: 4.1.0

**Positional arguments:**

``<server>``
  Name or ID of server.

``<tag>``
  Tag(s) to add.

.. _nova_server-tag-delete:

nova server-tag-delete
----------------------

.. code-block:: console

   usage: nova server-tag-delete <server> <tag> [<tag> ...]

Delete one or more tags from a server. (Supported by API versions '2.26' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

.. versionadded:: 4.1.0

**Positional arguments:**

``<server>``
  Name or ID of server.

``<tag>``
  Tag(s) to delete.

.. _nova_server-tag-delete-all:

nova server-tag-delete-all
--------------------------

.. code-block:: console

   usage: nova server-tag-delete-all <server>

Delete all tags from a server. (Supported by API versions '2.26' - '2.latest')
[hint: use '--os-compute-api-version' flag to show help message for proper
version]

.. versionadded:: 4.1.0

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_server-tag-list:

nova server-tag-list
--------------------

.. code-block:: console

   usage: nova server-tag-list <server>

Get list of tags from a server. (Supported by API versions '2.26' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

.. versionadded:: 4.1.0

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_server-tag-set:

nova server-tag-set
-------------------

.. code-block:: console

   usage: nova server-tag-set <server> <tags> [<tags> ...]

Set list of tags to a server. (Supported by API versions '2.26' - '2.latest')
[hint: use '--os-compute-api-version' flag to show help message for proper
version]

.. versionadded:: 4.1.0

**Positional arguments:**

``<server>``
  Name or ID of server.

``<tags>``
  Tag(s) to set.

.. _nova_server_topology:

nova server-topology
--------------------

.. code-block:: console

   usage: nova server-topology <server>

Retrieve server NUMA topology information. Host specific fields are only
visible to users with the administrative role.
(Supported by API versions '2.78' - '2.latest')

.. versionadded:: 15.1.0

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_service-delete:

nova service-delete
-------------------

.. code-block:: console

   usage: nova service-delete <id>

Delete the service.

.. important:: If deleting a nova-compute service, be sure to stop the actual
    ``nova-compute`` process on the physical host *before* deleting the
    service with this command. Failing to do so can lead to the running
    service re-creating orphaned **compute_nodes** table records in the
    database.

**Positional arguments:**

``<id>``
  ID of service as a UUID. (Supported by API versions '2.53' - '2.latest')

.. _nova_service-disable:

nova service-disable
--------------------

.. code-block:: console

   usage: nova service-disable [--reason <reason>] <id>

Disable the service.

**Positional arguments:**

``<id>``
  ID of the service as a UUID. (Supported by API versions '2.53' - '2.latest')

**Optional arguments:**

``--reason <reason>``
  Reason for disabling the service.

.. _nova_service-enable:

nova service-enable
-------------------

.. code-block:: console

   usage: nova service-enable <id>

Enable the service.

**Positional arguments:**

``<id>``
  ID of the service as a UUID. (Supported by API versions '2.53' - '2.latest')

.. _nova_service-force-down:

nova service-force-down
-----------------------

.. code-block:: console

   usage: nova service-force-down [--unset] <id>

Force service to down. (Supported by API versions '2.11' - '2.latest') [hint:
use '--os-compute-api-version' flag to show help message for proper version]

.. versionadded:: 2.27.0

**Positional arguments:**

``<id>``
  ID of the service as a UUID. (Supported by API versions '2.53' - '2.latest')


**Optional arguments:**

``--unset``
  Unset the forced_down state of the service.

.. _nova_service-list:

nova service-list
-----------------

.. code-block:: console

   usage: nova service-list [--host <hostname>] [--binary <binary>]

Show a list of all running services. Filter by host & binary.

Note that from microversion 2.69, during partial infrastructure failures in the
deployment, the output of this command may return partial results for the
services present in the failure domain.

**Optional arguments:**

``--host <hostname>``
  Name of host.

``--binary <binary>``
  Service binary.

.. _nova_set-password:

nova set-password
-----------------

.. code-block:: console

   usage: nova set-password <server>

Change the admin password for a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_shelve:

nova shelve
-----------

.. code-block:: console

   usage: nova shelve <server>

Shelve a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_shelve-offload:

nova shelve-offload
-------------------

.. code-block:: console

   usage: nova shelve-offload <server>

Remove a shelved server from the compute node.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_show:

nova show
---------

.. code-block:: console

   usage: nova show [--minimal] [--wrap <integer>] <server>

Show details about the given server.

Note that from microversion 2.69, during partial infrastructure failures in the
deployment, the output of this command may return partial results for the server
if it exists in the failure domain.

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--minimal``
  Skips flavor/image lookups when showing servers.

``--wrap <integer>``
  Wrap the output to a specified length, or 0 to disable.

.. _nova_ssh:

nova ssh
--------

.. code-block:: console

   usage: nova ssh [--port PORT] [--address-type ADDRESS_TYPE]
                   [--network <network>] [--ipv6] [--login <login>] [-i IDENTITY]
                   [--extra-opts EXTRA]
                   <server>

SSH into a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--port PORT``
  Optional flag to indicate which port to use
  for ssh. (Default=22)

``--address-type ADDRESS_TYPE``
  Optional flag to indicate which IP type to
  use. Possible values includes fixed and
  floating (the Default).

``--network <network>``
  Network to use for the ssh.

``--ipv6``
  Optional flag to indicate whether to use an
  IPv6 address attached to a server. (Defaults
  to IPv4 address)

``--login <login>``
  Login to use.

``-i IDENTITY, --identity IDENTITY``
  Private key file, same as the -i option to the
  ssh command.

``--extra-opts EXTRA``
  Extra options to pass to ssh. see: man ssh.

.. _nova_start:

nova start
----------

.. code-block:: console

   usage: nova start [--all-tenants] <server> [<server> ...]

Start the server(s).

**Positional arguments:**

``<server>``
  Name or ID of server(s).

**Optional arguments:**

``--all-tenants``
  Start server(s) in another tenant by name (Admin only).

.. _nova_stop:

nova stop
---------

.. code-block:: console

   usage: nova stop [--all-tenants] <server> [<server> ...]

Stop the server(s).

**Positional arguments:**

``<server>``
  Name or ID of server(s).

**Optional arguments:**

``--all-tenants``
  Stop server(s) in another tenant by name (Admin only).

.. _nova_suspend:

nova suspend
------------

.. code-block:: console

   usage: nova suspend <server>

Suspend a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_trigger-crash-dump:

nova trigger-crash-dump
-----------------------

.. code-block:: console

   usage: nova trigger-crash-dump <server>

Trigger crash dump in an instance. (Supported by API versions '2.17' -
'2.latest') [hint: use '--os-compute-api-version' flag to show help message
for proper version]

.. versionadded:: 3.3.0

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_unlock:

nova unlock
-----------

.. code-block:: console

   usage: nova unlock <server>

Unlock a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_unpause:

nova unpause
------------

.. code-block:: console

   usage: nova unpause <server>

Unpause a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_unrescue:

nova unrescue
-------------

.. code-block:: console

   usage: nova unrescue <server>

Restart the server from normal boot disk again.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_unshelve:

nova unshelve
-------------

.. code-block:: console

   usage: nova unshelve [--availability-zone <availability_zone>] <server>

Unshelve a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

**Optional arguments:**

``--availability-zone <availability_zone>``
  Name of the availability zone in which to unshelve a ``SHELVED_OFFLOADED``
  server. (Supported by API versions '2.77' - '2.latest')

.. _nova_update:

nova update
-----------

.. code-block:: console

   usage: nova update [--name <name>] [--description <description>]
                      [--hostname <hostname>]
                      <server>

Update attributes of a server.

**Positional arguments:**

``<server>``
  Name (old name) or ID of server.

**Optional arguments:**

``--name <name>``
  New name for the server.

``--description <description>``
  New description for the server. If it equals to
  empty string (i.g. ""), the server description
  will be removed. (Supported by API versions
  '2.19' - '2.latest')

``--hostname <hostname>``
  New hostname for the instance. This only updates the hostname
  stored in the metadata server: a utility running on the guest
  is required to propagate these changes to the guest.
  (Supported by API versions '2.90' - '2.latest')

.. _nova_usage:

nova usage
----------

.. code-block:: console

   usage: nova usage [--start <start>] [--end <end>] [--tenant <tenant-id>]

Show usage data for a single tenant.

**Optional arguments:**

``--start <start>``
  Usage range start date ex 2012-01-20. (default: 4
  weeks ago)

``--end <end>``
  Usage range end date, ex 2012-01-20. (default:
  tomorrow)

``--tenant <tenant-id>``
  UUID of tenant to get usage for.

.. _nova_usage-list:

nova usage-list
---------------

.. code-block:: console

   usage: nova usage-list [--start <start>] [--end <end>]

List usage data for all tenants.

**Optional arguments:**

``--start <start>``
  Usage range start date ex 2012-01-20. (default: 4 weeks
  ago)

``--end <end>``
  Usage range end date, ex 2012-01-20. (default: tomorrow)

.. _nova_version-list:

nova version-list
-----------------

.. code-block:: console

   usage: nova version-list

List all API versions.

.. _nova_volume-attach:

nova volume-attach
------------------

.. code-block:: console

   usage: nova volume-attach [--delete-on-termination] [--tag <tag>]
                             <server> <volume> [<device>]

Attach a volume to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<volume>``
  ID of the volume to attach.

``<device>``
  Name of the device e.g. /dev/vdb. Use "auto" for autoassign (if
  supported). Libvirt driver will use default device name.

**Optional arguments:**

``--tag <tag>``
  Tag for the attached volume. (Supported by API versions '2.49' - '2.latest')

``--delete-on-termination``
  Specify if the attached volume should be deleted when the server is
  destroyed. By default the attached volume is not deleted when the server is
  destroyed. (Supported by API versions '2.79' - '2.latest')

.. _nova_volume-attachments:

nova volume-attachments
-----------------------

.. code-block:: console

   usage: nova volume-attachments <server>

List all the volumes attached to a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

.. _nova_volume-detach:

nova volume-detach
------------------

.. code-block:: console

   usage: nova volume-detach <server> <volume>

Detach a volume from a server.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<volume>``
  ID of the volume to detach.

.. _nova_volume-update:

nova volume-update
------------------

.. code-block:: console

   usage: nova volume-update [--[no-]delete-on-termination]
                             <server> <src_volume> <dest_volume>

Update the attachment on the server. Migrates the data from an attached volume
to the specified available volume and swaps out the active attachment to the
new volume.

**Positional arguments:**

``<server>``
  Name or ID of server.

``<src_volume>``
  ID of the source (original) volume.

``<dest_volume>``
  ID of the destination volume.

**Optional arguments:**

``--delete-on-termination``
  Specify that the volume should be deleted when the server is destroyed.
  It is mutually exclusive with '--no-delete-on-termination'.
  (Supported by API versions '2.85' - '2.latest')

``--no-delete-on-termination``
  Specify that the attached volume should not be deleted when
  the server is destroyed. It is mutually exclusive with '--delete-on-termination'.
  (Supported by API versions '2.85' - '2.latest')

.. _nova_bash-completion:

nova bash-completion
--------------------

.. code-block:: console

   usage: nova bash-completion

Prints all of the commands and options to stdout so that the
nova.bash_completion script doesn't have to hard code them.

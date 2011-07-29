Python bindings to the OpenStack Nova API
==================================================

This is a client for the OpenStack Nova API. There's a Python API (the
``novaclient`` module), and a command-line script (``nova``). Each
implements 100% of the OpenStack Nova API.

[PENDING] `Full documentation is available`__.

__ http://packages.python.org/python-novaclient/

You'll also probably want to read `Rackspace's API guide`__ (PDF) -- the first
bit, at least -- to get an idea of the concepts. Rackspace is doing the cloud
hosting thing a bit differently from Amazon, and if you get the concepts this
library should make more sense.

__ http://docs.rackspacecloud.com/servers/api/cs-devguide-latest.pdf

Development takes place on GitHub__. Bug reports and patches may be filed there.

__ https://github.com/rackspace/python-client

This code a fork of `Jacobian's python-cloudservers`__ If you need API support
for the Rackspace API soley or the BSD license, you should use that repository. 
python-client is licensed under the Apache License like the rest of OpenStack.

__ http://github.com/jacobian/python-cloudservers

.. contents:: Contents:
   :local:

Command-line API
----------------

Installing this package gets you a shell command, ``nova``, that you
can use to interact with any Rackspace compatible API (including OpenStack).

You'll need to provide your OpenStack username and API key. You can do this
with the ``--username``, ``--apikey`` and  ``--projectid`` params, but it's easier to just 
set them as environment variables::

    export NOVA_USERNAME=openstack
    export NOVA_API_KEY=yadayada
    export NOVA_PROJECT_ID=myproject

You will also need to define the authentication url with ``--url``. Or set it as
an environment variable as well::

    export NOVA_URL=http://myserver:port/v1.0/
    
You'll find complete documentation on the shell by running 
``nova help``::
    
    usage: nova [--username USERNAME] [--apikey APIKEY] 
                        [--projectid PROJECTID] [--url AUTH_URL] <subcommand> ...

    Command-line interface to the OpenStack Nova API.

    Positional arguments:
      <subcommand>
        add-fixed-ip        Add a new fixed IP address to a servers network.
        backup              Resize a server.
        backup-schedule     Show or edit the backup schedule for a server.
        backup-schedule-delete
                            Delete the backup schedule for a server.
        boot                Boot a new server.
        delete              Immediately shut down and delete a server.
        flavor-list         Print a list of available 'flavors' (sizes of
                            servers).
        help                Display help about this program or one of its
                            subcommands.
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
        list                List active servers.
        migrate             Migrate a server to a new host in the same zone.
        reboot              Reboot a server.
        rebuild             Shutdown, re-image, and re-boot a server.
        remove-fixed-ip     Remove an IP address from a server.
        rename              Rename a server.
        rescue              Rescue a server.
        resize              Resize a server.
        resize-confirm      Confirm a previous resize.
        resize-revert       Revert a previous resize (and return to the previous
                            VM).
        root-password       Change the root password for a server.
        show                Show details about the given server.
        unrescue            Unrescue a server.
        zone                Show or edit a Child Zone
        zone-add            Add a Child Zone.
        zone-boot           Boot a server, considering Zones.
        zone-delete         Remove a Child Zone.
        zone-info           Show the capabilities for this Zone.
        zone-list           List all the immediate Child Zones.

    Optional arguments:
      --username USERNAME   Defaults to env[NOVA_USERNAME].
      --apikey APIKEY       Defaults to env[NOVA_API_KEY].
      --apikey PROJECTID    Defaults to env[NOVA_PROJECT_ID].
      --url AUTH_URL        Defaults to env[NOVA_URL] or
                            https://auth.api.rackspacecloud.com/v1.0
                            if undefined. 

    See "nova help COMMAND" for help on a specific command.
    
Python API
----------

[PENDING] There's also a `complete Python API`__.

__ http://packages.python.org/python-novaclient/

By way of a quick-start::

    >>> import novaclient
    >>> nt = novaclient.OpenStack(USERNAME, API_KEY,PROJECT_ID [, AUTH_URL])
    >>> nt.flavors.list()
    [...]
    >>> nt.servers.list()
    [...]
    >>> s = nt.servers.create(image=2, flavor=1, name='myserver')
    
    ... time passes ...
    
    >>> s.reboot()
    
    ... time passes ...
    
    >>> s.delete()

What's new?
-----------

[PENDING] See `the release notes <http://packages.python.org/python-novaclient/releases.html>`_.

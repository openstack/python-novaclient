Python bindings to the Rackspace Cloud Servers API
==================================================

This is a client for Rackspace's Cloud Servers API. There's a Python API (the
``cloudservers`` module), and a command-line script (``cloudservers``). Each
implements 100% of the Rackspace API.

`Full documentation is available`__.

__ http://packages.python.org/python-cloudservers/

You'll also probably want to read `Rackspace's API guide`__ (PDF) -- the first
bit, at least -- to get an idea of the concepts. Rackspace is doing the cloud
hosting thing a bit differently from Amazon, and if you get the concepts this
library should make more sense.

__ http://docs.rackspacecloud.com/servers/api/cs-devguide-latest.pdf

Development takes place on GitHub__. Bug reports and patches may be filed there.

__ http://github.com/jacobian/python-cloudservers

.. contents:: Contents:
   :local:

Command-line API
----------------

Installing this package gets you a shell command, ``cloudservers``, that you
can use to interact with any Rackspace compatible API (including OpenStack).

You'll need to provide your Rackspace username and API key. You can do this
with the ``--username`` and ``--apikey`` params, but it's easier to just 
set them as environment variables::

    export CLOUD_SERVERS_USERNAME=jacobian
    export CLOUD_SERVERS_API_KEY=yadayada

If you are using OpenStack or another Rackspace compatible API, you can 
optionally define its authentication url with ``--url``. Or set it as
an environment variable as well::

    export CLOUD_SERVERS_URL=http://myserver:port/v1.0/
    
You'll find complete documentation on the shell by running 
``cloudservers help``::
    
    usage: cloudservers [--username USERNAME] [--apikey APIKEY] 
                        [--url AUTH_URL] <subcommand> ...

    Command-line interface to the Cloud Servers API.

    Positional arguments:
      <subcommand>
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
        reboot              Reboot a server.
        rebuild             Shutdown, re-image, and re-boot a server.
        rename              Rename a server.
        rescue              Rescue a server.
        resize              Resize a server.
        resize-confirm      Confirm a previous resize.
        resize-revert       Revert a previous resize (and return to the previous
                            VM).
        root-password       Change the root password for a server.
        show                Show details about the given server.
        unrescue            Unrescue a server.

    Optional arguments:
      --username USERNAME   Defaults to env[CLOUD_SERVERS_USERNAME].
      --apikey APIKEY       Defaults to env[CLOUD_SERVERS_API_KEY].
      --url AUTH_URL        Defaults to env[CLOUD_SERVERS_URL] or
                            https://auth.api.rackspacecloud.com/v1.0
                            if undefined. 

    See "cloudservers help COMMAND" for help on a specific command.
    
Python API
----------

There's also a `complete Python API`__.

__ http://packages.python.org/python-cloudservers/

By way of a quick-start::

    >>> import cloudservers
    >>> cs = cloudservers.CloudServers(USERNAME, API_KEY [, AUTH_URL])
    >>> cs.flavors.list()
    [...]
    >>> cs.servers.list()
    [...]
    >>> s = cs.servers.create(image=2, flavor=1, name='myserver')
    
    ... time passes ...
    
    >>> s.reboot()
    
    ... time passes ...
    
    >>> s.delete()

FAQ
---

What's wrong with libcloud?

    Nothing! However, as a cross-service binding it's by definition lowest
    common denominator; I needed access to the Rackspace-specific APIs (shared
    IP groups, image snapshots, resizing, etc.). I also wanted a command-line
    utility.
    
What's new?
-----------

See `the release notes <http://packages.python.org/python-cloudservers/releases.html>`_.

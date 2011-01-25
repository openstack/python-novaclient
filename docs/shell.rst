The :program:`cloudservers` shell utility
=========================================

.. program:: cloudservers
.. highlight:: bash

The :program:`cloudservers` shell utility interacts with Rackspace Cloud servers
from the command line. It supports the entirety of the Cloud Servers API,
including some commands not available from the Rackspace web console.

First, you'll need a Rackspace Cloud Servers account and an API key. At the time
of this writing getting an API key is non-obvious: you need to sign up for
*both* Cloud Servers *and* Cloud Files; only then can you grab an API key from
the Rackspace web console.

You'll need to provide :program:`cloudservers` with your Rackspace username and
API key. You can do this with the :option:`--username` and :option:`--apikey`
options, but it's easier to just set them as environment variables by setting
two environment variables:

.. envvar:: CLOUD_SERVERS_USERNAME

    Your Rackspace Cloud username.

.. envvar:: CLOUD_SERVERS_API_KEY

    Your API key.

For example, in Bash you'd use::

    export CLOUD_SERVERS_USERNAME=yourname
    export CLOUD_SERVERS_API_KEY=yadayadayada
    
From there, all shell commands take the form::
    
    cloudservers <command> [arguments...]

Run :program:`cloudservers help` to get a full list of all possible commands,
and run :program:`cloudservers help <command>` to get detailed help for that
command.
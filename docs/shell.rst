The :program:`nova` shell utility
=========================================

.. program:: nova
.. highlight:: bash

The :program:`nova` shell utility interacts with OpenStack Nova API
from the command line. It supports the entirety of the OpenStack Nova API.

First, you'll need an OpenStack Nova account and an API key. You get this
by using the `nova-manage` command in OpenStack Nova.

You'll need to provide :program:`nova` with your OpenStack username and
API key. You can do this with the :option:`--username` and :option:`--apikey`
options, but it's easier to just set them as environment variables by setting
two environment variables:

.. envvar:: NOVA_USERNAME

    Your OpenStack Nova username.

.. envvar:: NOVA_API_KEY

    Your API key.

For example, in Bash you'd use::

    export NOVA_USERNAME=yourname
    export NOVA_API_KEY=yadayadayada
    
From there, all shell commands take the form::
    
    nova <command> [arguments...]

Run :program:`nova help` to get a full list of all possible commands,
and run :program:`nova help <command>` to get detailed help for that
command.

The :mod:`novaclient` Python API
================================

.. module:: novaclient
   :synopsis: A client for the OpenStack Nova API.

.. currentmodule:: novaclient

Usage
-----

First create a client instance with your credentials::

    >>> from novaclient import client
    >>> nova = client.Client(VERSION, USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

Here ``VERSION`` can be a string or ``novaclient.api_versions.APIVersion`` obj.
If you prefer string value, you can use ``1.1`` (deprecated now), ``2`` or
``2.X`` (where X is a microversion).


Alternatively, you can create a client instance using the keystoneclient
session API::

    >>> from keystoneclient.auth.identity import v2
    >>> from keystoneclient import session
    >>> from novaclient import client
    >>> auth = v2.Password(auth_url=AUTH_URL,
    ...                    username=USERNAME,
    ...                    password=PASSWORD,
    ...                    tenant_name=PROJECT_ID)
    >>> sess = session.Session(auth=auth)
    >>> nova = client.Client(VERSION, session=sess)

For more information on this keystoneclient API, see `Using Sessions`_.

.. _Using Sessions: http://docs.openstack.org/developer/python-keystoneclient/using-sessions.html

It is also possible to use an instance as a context manager in which case
there will be a session kept alive for the duration of the with statement::

    >>> from novaclient import client
    >>> with client.Client(VERSION, USERNAME, PASSWORD,
    ...                    PROJECT_ID, AUTH_URL) as nova:
    ...     nova.servers.list()
    ...     nova.flavors.list()
    ...

It is also possible to have a permanent (process-long) connection pool,
by passing a connection_pool=True::

    >>> from novaclient import client
    >>> nova = client.Client(VERSION, USERNAME, PASSWORD, PROJECT_ID,
    ...                      AUTH_URL, connection_pool=True)

Then call methods on its managers::

    >>> nova.servers.list()
    [<Server: buildslave-ubuntu-9.10>]

    >>> nova.flavors.list()
    [<Flavor: 256 server>,
     <Flavor: 512 server>,
     <Flavor: 1GB server>,
     <Flavor: 2GB server>,
     <Flavor: 4GB server>,
     <Flavor: 8GB server>,
     <Flavor: 15.5GB server>]

    >>> fl = nova.flavors.find(ram=512)
    >>> nova.servers.create("my-server", flavor=fl)
    <Server: my-server>

.. warning:: Direct initialization of ``novaclient.v2.client.Client`` object
  can cause you to "shoot yourself in the foot". See launchpad bug-report
  `1493576`_ for more details.

.. _1493576: https://launchpad.net/bugs/1493576


Reference
---------

For more information, see the reference:

.. toctree::
   :maxdepth: 2

   ref/index
   ref/v2/index

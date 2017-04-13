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


Alternatively, you can create a client instance using the keystoneauth
session API::

    >>> from keystoneauth1 import loading
    >>> from keystoneauth1 import session
    >>> from novaclient import client
    >>> loader = loading.get_plugin_loader('password')
    >>> auth = loader.load_from_options(auth_url=AUTH_URL,
    ...                                 username=USERNAME,
    ...                                 password=PASSWORD,
    ...                                 project_id=PROJECT_ID)
    >>> sess = session.Session(auth=auth)
    >>> nova = client.Client(VERSION, session=sess)

If you have PROJECT_NAME instead of a PROJECT_ID, use the project_name
parameter. Similarly, if your cloud uses keystone v3 and you have a DOMAIN_NAME
or DOMAIN_ID, provide it as `user_domain_(name|id)` and if you are using a
PROJECT_NAME also provide the domain information as `project_domain_(name|id)`.

novaclient adds 'python-novaclient' and its version to the user-agent string
that keystoneauth produces. If you are creating an application using novaclient
and want to register a name and version in the user-agent string, pass those
to the Session::

    >>> sess = session.Session(
    ...     auth=auth, app_name'nodepool', app_version'1.2.3')

If you are making a library that consumes novaclient but is not an end-user
application, you can append a (name, version) tuple to the session's
`additional_user_agent` property::

    >>> sess = session.Session(auth=auth)
    >>> sess.additional_user_agent.append(('shade', '1.2.3'))

For more information on this keystoneauth API, see `Using Sessions`_.

.. _Using Sessions: http://docs.openstack.org/developer/keystoneauth/using-sessions.html

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

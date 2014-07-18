The :mod:`novaclient` Python API
==================================

.. module:: novaclient
   :synopsis: A client for the OpenStack Nova API.

.. currentmodule:: novaclient

Usage
-----

First create a client instance with your credentials::

    >>> from novaclient.client import Client
    >>> nova = Client(VERSION, USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

Here ``VERSION`` can be: ``1.1``, ``2`` and ``3``.

Alternatively, you can create a client instance using the keystoneclient
session API::

    >>> from keystoneclient.auth.identity import v2
    >>> from keystoneclient import session
    >>> from novaclient.client import Client
    >>> auth = v2.Password(auth_url=AUTH_URL,
                           username=USERNAME,
                           password=PASSWORD,
                           tenant_name=PROJECT_ID)
    >>> sess = session.Session(auth=auth)
    >>> nova = client.Client(VERSION, session=sess)

For more information on this keystoneclient API, see `Using Sessions`_.

.. _Using Sessions: http://docs.openstack.org/developer/python-keystoneclient/using-sessions.html

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

Reference
---------

For more information, see the reference:

.. toctree::
   :maxdepth: 2

   ref/index
   ref/v1_1/index
   ref/v3/index

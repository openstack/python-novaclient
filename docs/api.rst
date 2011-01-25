The :mod:`cloudservers` Python API
==================================

.. module:: cloudservers
   :synopsis: A client for the Rackspace Cloud Servers API.
   
.. currentmodule:: cloudservers

Usage
-----

First create an instance of :class:`CloudServers` with your credentials::

    >>> from cloudservers import CloudServers
    >>> cloudservers = CloudServers(USERNAME, API_KEY)

Then call methods on the :class:`CloudServers` object:

.. class:: CloudServers
    
    .. attribute:: backup_schedules
    
        A :class:`BackupScheduleManager` -- manage automatic backup images.
    
    .. attribute:: flavors
    
        A :class:`FlavorManager` -- query available "flavors" (hardware
        configurations).
        
    .. attribute:: images
    
        An :class:`ImageManager` -- query and create server disk images.
    
    .. attribute:: ipgroups
    
        A :class:`IPGroupManager` -- manage shared public IP addresses.
    
    .. attribute:: servers
    
        A :class:`ServerManager` -- start, stop, and manage virtual machines.
    
    .. automethod:: authenticate

For example::

    >>> cloudservers.servers.list()
    [<Server: buildslave-ubuntu-9.10>]

    >>> cloudservers.flavors.list()
    [<Flavor: 256 server>,
     <Flavor: 512 server>,
     <Flavor: 1GB server>,
     <Flavor: 2GB server>,
     <Flavor: 4GB server>,
     <Flavor: 8GB server>,
     <Flavor: 15.5GB server>]

    >>> fl = cloudservers.flavors.find(ram=512)
    >>> cloudservers.servers.create("my-server", flavor=fl)
    <Server: my-server>

For more information, see the reference:

.. toctree::
   :maxdepth: 2
   
   ref/index
The :mod:`novaclient` Python API
==================================

.. module:: novaclient
   :synopsis: A client for the OpenStack Nova API.
   
.. currentmodule:: novaclient

Usage
-----

First create an instance of :class:`OpenStack` with your credentials::

    >>> from novaclient import OpenStack
    >>> nova = OpenStack(USERNAME, API_KEY, AUTH_URL)

Then call methods on the :class:`OpenStack` object:

.. class:: OpenStack
    
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

For more information, see the reference:

.. toctree::
   :maxdepth: 2
   
   ref/index

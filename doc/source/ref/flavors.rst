Flavors
=======

From Rackspace's API documentation:

    A flavor is an available hardware configuration for a server. Each flavor
    has a unique combination of disk space, memory capacity and priority for
    CPU time.
    
Classes
-------

.. currentmodule:: novaclient

.. autoclass:: FlavorManager
   :members: get, list, find, findall

.. autoclass:: Flavor
   :members:
   
   .. attribute:: id
   
       This flavor's ID.
       
   .. attribute:: name
   
       A human-readable name for this flavor.
   
   .. attribute:: ram
   
       The amount of RAM this flavor has, in MB.
       
   .. attribute:: disk
   
       The amount of disk space this flavor has, in MB

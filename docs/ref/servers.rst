Servers
=======

A virtual machine instance.

Classes
-------

.. currentmodule:: novaclient

.. autoclass:: ServerManager
   :members: get, list, find, findall, create, update, delete, share_ip,
             unshare_ip, reboot, rebuild, resize, confirm_resize,
             revert_resize
             
.. autoclass:: Server
   :members: update, delete, share_ip, unshare_ip, reboot, rebuild, resize,
             confirm_resize, revert_resize
             
   .. attribute:: id
   
        This server's ID.
   
   .. attribute:: name
   
        The name you gave the server when you booted it.

   .. attribute:: imageId
   
        The :class:`Image` this server was booted with.
   
   .. attribute:: flavorId
   
        This server's current :class:`Flavor`.
   
   .. attribute:: hostId
   
        Rackspace doesn't document this value. It appears to be SHA1 hash.
   
   .. attribute:: status
   
        The server's status (``BOOTING``, ``ACTIVE``, etc).
   
   .. attribute:: progress
   
        When booting, resizing, updating, etc., this will be set to a
        value between 0 and 100 giving a rough estimate of the progress
        of the current operation.
   
   .. attribute:: addresses
   
        The public and private IP addresses of this server. This'll be a dict
        of the form::
        
            {
              "public" : ["67.23.10.138"],
              "private" : ["10.176.42.19"]
            }
            
        You *can* get more than one public/private IP provisioned, but not
        directly from the API; you'll need to open a support ticket.
   
   .. attribute:: metadata
   
        The metadata dict you gave when creating the server.
        
Constants
---------

Reboot types:

.. data:: REBOOT_SOFT
.. data:: REBOOT_HARD

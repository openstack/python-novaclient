Images
======

.. currentmodule:: novaclient

An "image" is a snapshot from which you can create new server instances.

From Rackspace's own API documentation:

    An image is a collection of files used to create or rebuild a server.
    Rackspace provides a number of pre-built OS images by default. You may
    also create custom images from cloud servers you have launched. These
    custom images are useful for backup purposes or for producing "gold"
    server images if you plan to deploy a particular server configuration
    frequently.

Classes
-------

.. autoclass:: ImageManager
   :members: get, list, find, findall, create, delete

.. autoclass:: Image
   :members: delete
      
   .. attribute:: id
   
       This image's ID.
       
   .. attribute:: name
   
       This image's name.
       
   .. attribute:: created
   
       The date/time this image was created.
       
   .. attribute:: updated
   
       The date/time this instance was updated.
       
   .. attribute:: status
   
       The status of this image (usually ``"SAVING"`` or ``ACTIVE``).
       
   .. attribute:: progress
   
       During saving of an image this'll be set to something between
       0 and 100, representing a rough percentage done.
       
   .. attribute:: serverId
   
       If this image was created from a :class:`Server` then this attribute
       will be set to the ID of the server whence this image came.

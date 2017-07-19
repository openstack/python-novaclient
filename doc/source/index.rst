===========================================
 Python bindings to the OpenStack Nova API
===========================================

This is a client for OpenStack Nova API. There's :doc:`a Python API
<reference/api/index>` (the :mod:`novaclient` module), and a :doc:`command-line
script </user/shell>` (installed as :program:`nova`). Each implements the
entire OpenStack Nova API.

You'll need credentials for an OpenStack cloud that implements the Compute API,
such as TryStack, HP, or Rackspace, in order to use the nova client.

.. seealso::

    You may want to read the `OpenStack Compute API Guide`__
    to get an idea of the concepts. By understanding the concepts
    this library should make more sense.

    __ https://developer.openstack.org/api-guide/compute/index.html

.. toctree::
   :maxdepth: 2

   user/index
   reference/index
   cli/index
   contributor/index

===========================================
 Python bindings to the OpenStack Nova API
===========================================

This is a client for OpenStack Nova API. There's a :doc:`Python API
<reference/index>` (the :mod:`novaclient` module), and a deprecated
:doc:`command-line script </user/shell>` (installed as :program:`nova`).
Each implements the entire OpenStack Nova API.

You'll need credentials for an OpenStack cloud that implements the Compute API
in order to use the nova client.

.. seealso::

    You may want to read the `OpenStack Compute API Guide`__
    to get an idea of the concepts. By understanding the concepts
    this library should make more sense.

    __ https://docs.openstack.org/api-guide/compute/index.html

.. toctree::
   :maxdepth: 2

   user/index
   cli/index
   reference/index
   contributor/index

Python bindings to the OpenStack Nova API
==================================================

This is a client for OpenStack Nova API. There's :doc:`a Python API
<api>` (the :mod:`novaclient` module), and a :doc:`command-line script
<shell>` (installed as :program:`nova`). Each implements the entire
OpenStack Nova API.

You'll need credentials for an OpenStack cloud that implements the
Compute API, such as TryStack, HP, or Rackspace, in order to use the nova client.

.. seealso::

    You may want to read the `OpenStack Compute Developer Guide`__  -- the overview, at
    least -- to get an idea of the concepts. By understanding the concepts
    this library should make more sense.

    __ http://docs.openstack.org/api/openstack-compute/2/content/

Contents:

.. toctree::
   :maxdepth: 2

   shell
   api
   ref/index
   ref/v1_1/index
   ref/v3/index
   releases

Contributing
============

Code is hosted at `git.openstack.org`_. Submit bugs to the Nova project on
`Launchpad`_. Submit code to the openstack/python-novaclient project using
`Gerrit`_.

.. _git.openstack.org: https://git.openstack.org/cgit/openstack/python-novaclient
.. _Launchpad: https://launchpad.net/nova
.. _Gerrit: http://wiki.openstack.org/GerritWorkflow

Run tests with ``python setup.py test``.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

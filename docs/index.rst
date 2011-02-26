Python bindings to the OpenStack Nova API
==================================================

This is a client for OpenStack Nova API. There's :doc:`a Python API
<api>` (the :mod:`novaclient` module), and a :doc:`command-line script
<shell>` (installed as :program:`nova`). Each implements the entire
OpenStack Nova API.

You'll need an `OpenStack Nova` account, which you can get by using `nova-manage`.

.. seealso::

    You may want to read `Rackspace's API guide`__ (PDF) -- the first bit, at
    least -- to get an idea of the concepts. Rackspace is doing the cloud
    hosting thing a bit differently from Amazon, and if you get the concepts
    this library should make more sense.

    __ http://docs.rackspacecloud.com/servers/api/cs-devguide-latest.pdf

Contents:

.. toctree::
   :maxdepth: 2
   
   shell
   api
   ref/index
   releases

Contributing
============

Development takes place `on GitHub`__; please file bugs/pull requests there.

__ https://github.com/rackspace/python-novaclient

Run tests with ``python setup.py test``.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


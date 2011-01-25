Python bindings to the Rackspace Cloud Servers API
==================================================

This is a client for Rackspace's Cloud Servers API. There's :doc:`a Python API
<api>` (the :mod:`cloudservers` module), and a :doc:`command-line script
<shell>` (installed as :program:`cloudservers`). Each implements the entire
Rackspace Cloud Servers API.

You'll need a `Rackspace Cloud`__ account, and you'll need to make sure to sign
up for both Cloud Servers *and* Cloud Files -- Rackspace won't let you get an
API key unless you've got a Cloud Files account, too. Once you've got an
account, you'll find your API key in the management console under "Your
Account".

__ http://rackspacecloud.com/

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

__ http://github.com/jacobian/python-cloudservers

Run tests with ``python setup.py test``.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


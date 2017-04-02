Python bindings to the OpenStack Nova API
=========================================

This is a client for OpenStack Nova API. There's :doc:`a Python API
<api>` (the :mod:`novaclient` module), and a :doc:`command-line script
<shell>` (installed as :program:`nova`). Each implements the entire
OpenStack Nova API.

You'll need credentials for an OpenStack cloud that implements the
Compute API, such as TryStack, HP, or Rackspace, in order to use the nova client.

.. seealso::

    You may want to read the `OpenStack Compute API Guide`__
    to get an idea of the concepts. By understanding the concepts
    this library should make more sense.

    __ https://developer.openstack.org/api-guide/compute/index.html

Contents:

.. toctree::
   :maxdepth: 2

   shell
   api
   ref/index
   ref/v2/index

Contributing
============

Code is hosted at `git.openstack.org`_. Submit bugs to the Nova project on
`Launchpad`_. Submit code to the openstack/python-novaclient project using
`Gerrit`_.

.. _git.openstack.org: https://git.openstack.org/cgit/openstack/python-novaclient
.. _Launchpad: https://launchpad.net/nova
.. _Gerrit: http://docs.openstack.org/infra/manual/developers.html#development-workflow

Testing
-------

The preferred way to run the unit tests is using ``tox``.

See `Consistent Testing Interface`_ for more details.

.. _Consistent Testing Interface: http://git.openstack.org/cgit/openstack/governance/tree/reference/project-testing-interface.rst

Deprecating commands
====================

There are times when commands need to be deprecated due to rename or removal.
The process for command deprecation is:

  1. Push up a change for review which deprecates the command(s).

   - The change should print a deprecation warning to stderr each time a
     deprecated command is used.
   - That warning message should include a rough timeline for when the command
     will be removed and what should be used instead, if anything.
   - The description in the help text for the deprecated command should mark
     that it is deprecated.
   - The change should include a release note with the ``deprecations`` section
     filled out.
   - The deprecation cycle is typically the first client release *after* the
     next *full* Nova server release so that there is at least six months of
     deprecation.

  2. Once the change is approved, have a member of the `nova-release`_ team
     release a new version of python-novaclient.

     .. _nova-release: https://review.openstack.org/#/admin/groups/147,members

  3. Example: `<https://review.openstack.org/#/c/185141/>`_

     This change was made while the Nova 12.0.0 Liberty release was in
     development. The current version of python-novaclient at the time was
     2.25.0. Once the change was merged, python-novaclient 2.26.0 was released.
     Since there was less than six months before 12.0.0 would be released, the
     deprecation cycle ran through the 13.0.0 Nova server release.


Man Page
========

.. toctree::
   :maxdepth: 1

   man/nova



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

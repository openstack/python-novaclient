============================
So You Want to Contribute...
============================

For general information on contributing to OpenStack, please check out the
`contributor guide <https://docs.openstack.org/contributors/>`_ to get started.
It covers all the basics that are common to all OpenStack projects: the accounts
you need, the basics of interacting with our Gerrit review system, how we
communicate as a community, etc.

Below will cover the more project specific information you need to get started
with python-novaclient.

.. important::

    The ``nova`` CLI has been deprecated in favour of the unified ``openstack``
    CLI. Changes to the Python bindings are still welcome, however, no further
    changes should be made to the shell.

Communication
~~~~~~~~~~~~~

Please refer `how-to-get-involved <https://docs.openstack.org/nova/latest/contributor/how-to-get-involved.html>`_.

Contacting the Core Team
~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to reach the core team is via IRC, using the ``openstack-nova``
OFTC IRC channel.

New Feature Planning
~~~~~~~~~~~~~~~~~~~~

If you want to propose a new feature please read the
`blueprints <https://docs.openstack.org/nova/latest/contributor/blueprints.html>`_ page.

Task Tracking
~~~~~~~~~~~~~

We track our tasks in `Launchpad <https://bugs.launchpad.net/python-novaclient>`__.

If you're looking for some smaller, easier work item to pick up and get started
on, search for the 'low-hanging-fruit' tag.

Reporting a Bug
~~~~~~~~~~~~~~~

You found an issue and want to make sure we are aware of it? You can do so on
`Launchpad <https://bugs.launchpad.net/python-novaclient/+filebug>`__.
More info about Launchpad usage can be found on `OpenStack docs page
<https://docs.openstack.org/contributors/common/task-tracking.html#launchpad>`_.

Getting Your Patch Merged
~~~~~~~~~~~~~~~~~~~~~~~~~

All changes proposed to the python-novaclient requires two ``Code-Review +2``
votes from ``python-novaclient`` core reviewers before one of the core reviewers
can approve patch by giving ``Workflow +1`` vote..

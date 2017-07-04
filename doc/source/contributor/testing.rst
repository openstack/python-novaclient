=========
 Testing
=========

The preferred way to run the unit tests is using ``tox``. There are multiple
test targets that can be run to validate the code.

``tox -e pep8``

  Style guidelines enforcement.

``tox -e py27``

  Traditional unit testing.

``tox -e functional``

  Live functional testing against an existing OpenStack instance.

Functional testing assumes the existence of a `clouds.yaml` file as supported
by `os-client-config <http://docs.openstack.org/developer/os-client-config>`__
It assumes the existence of a cloud named `devstack` that behaves like a normal
DevStack installation with a demo and an admin user/tenant - or clouds named
`functional_admin` and `functional_nonadmin`.

Refer to  `Consistent Testing Interface`__ for more details.

__ http://git.openstack.org/cgit/openstack/governance/tree/reference/project-testing-interface.rst

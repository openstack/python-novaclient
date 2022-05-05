=========
 Testing
=========

The preferred way to run the unit tests is using ``tox``. There are multiple
test targets that can be run to validate the code.

``tox -e pep8``
  Style guidelines enforcement.

``tox -e py38``
  Traditional unit testing (Python 3.8).

``tox -e functional``
  Live functional testing against an existing OpenStack instance. (Python 3.8)

``tox -e cover``
  Generate a coverage report on unit testing.

Functional testing assumes the existence of a `clouds.yaml` file as supported
by :os-client-config-doc:`os-client-config <>`.
It assumes the existence of a cloud named `devstack` that behaves like a normal
DevStack installation with a demo and an admin user/tenant - or clouds named
`functional_admin` and `functional_nonadmin`.

Refer to  `Consistent Testing Interface`__ for more details.

__ https://governance.openstack.org/tc/reference/project-testing-interface.html

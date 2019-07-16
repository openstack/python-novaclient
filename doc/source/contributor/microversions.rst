=====================================
Adding support for a new microversion
=====================================

If a new microversion is added on the nova side,
then support must be added on the *python-novaclient* side also.
The following procedure describes how to add support for a new microversion
in *python-novaclient*.

#. Update ``API_MAX_VERSION``

   Set ``API_MAX_VERSION`` in ``novaclient/__init__.py`` to the version
   you are going to support.

   .. note::

     Microversion support should be added one by one in order.
     For example, microversion 2.74 should be added right after
     microversion 2.73. Microversion 2.74 should not be added right
     after microversion 2.72 or earlier.

#. Update CLI and Python API

   Update CLI (``novaclient/v2/shell.py``) and/or Python API
   (``novaclient/v2/*.py``) to support the microversion.

#. Add tests

   Add unit tests for the change. Add unit tests for the previous microversion
   to check raising an error or an exception when new arguments or parameters
   are specified. Add functional tests if necessary.

   Add the microversion in the ``exclusions`` in the ``test_versions``
   method of the ``novaclient.tests.unit.v2.test_shell.ShellTest`` class
   if there are no versioned wrapped method changes for the microversion.
   The versioned wrapped methods have ``@api_versions.wraps`` decorators.

   For example (microversion 2.72 example)::

     exclusions = set([
         (snipped...)
         72,  # There are no version-wrapped shell method changes for this.
     ])

#. Update the CLI reference

   Update the CLI reference (``doc/source/cli/nova.rst``)
   if the CLI commands and/or arguments are modified.

#. Add a release note

   Add a release note for the change. The release note should include a link
   to the description for the microversion in the
   :nova-doc:`Compute API Microversion History
   <reference/api-microversion-history>`.

#. Commit message

   The description of the blueprint and dependency on the patch in nova side
   should be added in the commit message. For example::

     Implements: blueprint remove-force-flag-from-live-migrate-and-evacuate
     Depends-On: https://review.opendev.org/#/c/634600/

See the following examples:

- `Microversion 2.71 - show server group <https://review.opendev.org/#/c/640657/>`_
- `API microversion 2.69: Handles Down Cells <https://review.opendev.org/#/c/579563/>`_
- `Microversion 2.68: Remove 'forced' live migrations, evacuations <https://review.opendev.org/#/c/635131/>`_
- `Add support changes-before for microversion 2.66 <https://review.opendev.org/#/c/603549/>`_
- `Microversion 2.64 - Use new format policy in server group <https://review.opendev.org/#/c/578261/>`_

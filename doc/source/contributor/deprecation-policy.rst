Deprecating commands
====================

There are times when commands need to be deprecated due to rename or removal.
The process for command deprecation is:

1. Push up a change for review which deprecates the command(s).

   - The change should print a deprecation warning to ``stderr`` each time a
     deprecated command is used.
   - That warning message should include a rough timeline for when the command
     will be removed and what should be used instead, if anything.
   - The description in the help text for the deprecated command should mark
     that it is deprecated.
   - The change should include a release note with the ``deprecations`` section
     filled out.
   - The deprecation cycle is typically the first client release *after* the
     next *full* nova server release so that there is at least six months of
     deprecation.

2. Once the change is approved, have a member of the `nova-release`_ team
   release a new version of `python-novaclient`.

   .. _nova-release: https://review.opendev.org/#/admin/groups/147,members

3. Example: `<https://review.opendev.org/#/c/185141/>`_

   This change was made while the nova 12.0.0 Liberty release was in
   development. The current version of `python-novaclient` at the time was
   2.25.0. Once the change was merged, `python-novaclient` 2.26.0 was released.
   Since there was less than six months before 12.0.0 would be released, the
   deprecation cycle ran through the 13.0.0 nova server release.

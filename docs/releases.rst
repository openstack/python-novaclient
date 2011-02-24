=============
Release notes
=============

2.1 (Feb 28, 2011)
=================

* shell renamed to nova from novatools

* license changed from BSD to Apache

2.0 (Feb 7, 2011)
=================

* Forked from https://github.com/jacobian/python-cloudservers

* Rebranded to python-novatools

* Auth URL support

* New OpenStack specific commands added (pause, suspend, etc)

1.2 (August 15, 2010)
=====================

* Support for Python 2.4 - 2.7.

* Improved output of :program:`cloudservers ipgroup-list`.

* Made ``cloudservers boot --ipgroup <name>`` work (as well as ``--ipgroup
  <id>``).

1.1 (May 6, 2010)
=================

* Added a ``--files`` option to :program:`cloudservers boot` supporting
  the upload of (up to five) files at boot time.
  
* Added a ``--key`` option to :program:`cloudservers boot` to key the server
  with an SSH public key at boot time. This is just a shortcut for ``--files``,
  but it's a useful shortcut.
  
* Changed the default server image to Ubuntu 10.04 LTS.

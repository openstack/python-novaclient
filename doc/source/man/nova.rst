====
nova
====


SYNOPSIS
========

  `nova` [options] <command> [command-options]

  `nova help`

  `nova help` <command>


DESCRIPTION
===========

`nova` is a command line client for controlling OpenStack Nova, the cloud
computing fabric controller. It implements 100% of the Nova API, allowing
management of instances, images, quotas and much more.

Before you can issue commands with `nova`, you must ensure that your
environment contains the necessary variables so that you can prove to the CLI
who you are and what credentials you have to issue the commands. See
`Getting Credentials for a CLI` section of `OpenStack CLI Guide` for more
info.

See `OpenStack Nova CLI Guide` for a full-fledged guide.


OPTIONS
=======

To get a list of available commands and options run::

    nova help

To get usage and options of a command run::

    nova help <command>


EXAMPLES
========

Get information about boot command::

    nova help boot

List available images::

    nova image-list

List available flavors::

    nova flavor-list

Launch an instance::

    nova boot myserver --image some-image --flavor 2

View instance information::

    nova show myserver

List instances::

    nova list

Terminate an instance::

    nova delete myserver


SEE ALSO
========

OpenStack Nova CLI Guide: http://docs.openstack.org/cli-reference/content/novaclient_commands.html


BUGS
====

Nova client is hosted in Launchpad so you can view current bugs at https://bugs.launchpad.net/python-novaclient/.

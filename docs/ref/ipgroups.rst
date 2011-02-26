Shared IP addresses
===================

From the Rackspace API guide:

    Public IP addresses can be shared across multiple servers for use in
    various high availability scenarios. When an IP address is shared to
    another server, the cloud network restrictions are modified to allow each
    server to listen to and respond on that IP address (you may optionally
    specify that the target server network configuration be modified). Shared
    IP addresses can be used with many standard heartbeat facilities (e.g.
    ``keepalived``) that monitor for failure and manage IP failover.

    A shared IP group is a collection of servers that can share IPs with other
    members of the group. Any server in a group can share one or more public
    IPs with any other server in the group. With the exception of the first
    server in a shared IP group, servers must be launched into shared IP
    groups. A server may only be a member of one shared IP group.

.. seealso::

    Use :meth:`Server.share_ip` and `Server.unshare_ip` to share and unshare
    IPs in a group.

Classes
-------

.. currentmodule:: novaclient

.. autoclass:: IPGroupManager
   :members: get, list, find, findall, create, delete
   
.. autoclass:: IPGroup
   :members: delete
   
   .. attribute:: id
   
        Shared group ID.
   
   .. attribute:: name
   
        Name of the group.
   
   .. attribute:: servers
   
        A list of server IDs in this group.

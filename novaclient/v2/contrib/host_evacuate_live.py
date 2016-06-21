# Copyright 2014 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from novaclient.i18n import _
from novaclient import utils


def _server_live_migrate(cs, server, args):
    class HostEvacuateLiveResponse(object):
        def __init__(self, server_uuid, live_migration_accepted,
                     error_message):
            self.server_uuid = server_uuid
            self.live_migration_accepted = live_migration_accepted
            self.error_message = error_message
    success = True
    error_message = ""
    update_kwargs = {}
    try:
        # API >= 2.30
        if 'force' in args and args.force:
            update_kwargs['force'] = args.force
        # API 2.0->2.24
        if 'disk_over_commit' in args:
            update_kwargs['disk_over_commit'] = args.disk_over_commit
        cs.servers.live_migrate(server['uuid'], args.target_host,
                                args.block_migrate, **update_kwargs)
    except Exception as e:
        success = False
        error_message = _("Error while live migrating instance: %s") % e
    return HostEvacuateLiveResponse(server['uuid'],
                                    success,
                                    error_message)


@utils.arg('host', metavar='<host>', help='Name of host.')
@utils.arg(
    '--target-host',
    metavar='<target_host>',
    default=None,
    help=_('Name of target host.'))
@utils.arg(
    '--block-migrate',
    action='store_true',
    default=False,
    help=_('Enable block migration. (Default=False)'),
    start_version="2.0", end_version="2.24")
@utils.arg(
    '--block-migrate',
    action='store_true',
    default="auto",
    help=_('Enable block migration. (Default=auto)'),
    start_version="2.25")
@utils.arg(
    '--disk-over-commit',
    action='store_true',
    default=False,
    help=_('Enable disk overcommit.'),
    start_version="2.0", end_version="2.24")
@utils.arg(
    '--max-servers',
    type=int,
    dest='max_servers',
    metavar='<max_servers>',
    help='Maximum number of servers to live migrate simultaneously')
@utils.arg(
    '--force',
    dest='force',
    action='store_true',
    default=False,
    help=_('Force to not verify the scheduler if a host is provided.'),
    start_version='2.30')
def do_host_evacuate_live(cs, args):
    """Live migrate all instances of the specified host
    to other available hosts.
    """
    hypervisors = cs.hypervisors.search(args.host, servers=True)
    response = []
    migrating = 0
    for hyper in hypervisors:
        for server in getattr(hyper, 'servers', []):
            response.append(_server_live_migrate(cs, server, args))
            migrating = migrating + 1
            if args.max_servers is not None and migrating >= args.max_servers:
                break

    utils.print_list(response, ["Server UUID", "Live Migration Accepted",
                                "Error Message"])

# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

import logging

from novaclient import client
from novaclient import exceptions
from novaclient.i18n import _
from novaclient.v2 import agents
from novaclient.v2 import aggregates
from novaclient.v2 import assisted_volume_snapshots
from novaclient.v2 import availability_zones
from novaclient.v2 import flavor_access
from novaclient.v2 import flavors
from novaclient.v2 import hypervisors
from novaclient.v2 import images
from novaclient.v2 import instance_action
from novaclient.v2 import instance_usage_audit_log
from novaclient.v2 import keypairs
from novaclient.v2 import limits
from novaclient.v2 import migrations
from novaclient.v2 import networks
from novaclient.v2 import quota_classes
from novaclient.v2 import quotas
from novaclient.v2 import server_external_events
from novaclient.v2 import server_groups
from novaclient.v2 import server_migrations
from novaclient.v2 import servers
from novaclient.v2 import services
from novaclient.v2 import usage
from novaclient.v2 import versions
from novaclient.v2 import volumes


class Client(object):
    """Top-level object to access the OpenStack Compute API.

    .. warning:: All scripts and projects should not initialize this class
      directly. It should be done via `novaclient.client.Client` interface.
    """

    def __init__(self,
                 api_version=None,
                 auth=None,
                 auth_token=None,
                 auth_url=None,
                 cacert=None,
                 cert=None,
                 direct_use=True,
                 endpoint_override=None,
                 endpoint_type='publicURL',
                 extensions=None,
                 http_log_debug=False,
                 insecure=False,
                 logger=None,
                 os_cache=False,
                 password=None,
                 project_domain_id=None,
                 project_domain_name=None,
                 project_id=None,
                 project_name=None,
                 region_name=None,
                 service_name=None,
                 service_type='compute',
                 session=None,
                 timeout=None,
                 timings=False,
                 user_domain_id=None,
                 user_domain_name=None,
                 user_id=None,
                 username=None,
                 **kwargs):
        """Initialization of Client object.

        :param api_version: Compute API version
        :type api_version: novaclient.api_versions.APIVersion
        :param str auth: Auth
        :param str auth_token: Auth token
        :param str auth_url: Auth URL
        :param str cacert: ca-certificate
        :param str cert: certificate
        :param bool direct_use: Inner variable of novaclient. Do not use it
            outside novaclient. It's restricted.
        :param str endpoint_override: Bypass URL
        :param str endpoint_type: Endpoint Type
        :param str extensions: Extensions
        :param bool http_log_debug: Enable debugging for HTTP connections
        :param bool insecure: Allow insecure
        :param logging.Logger logger: Logger instance to be used for all
            logging stuff
        :param str password: User password
        :param bool os_cache: OS cache
        :param str project_domain_id: ID of project domain
        :param str project_domain_name: Name of project domain
        :param str project_id: Project/Tenant ID
        :param str project_name: Project/Tenant name
        :param str region_name: Region Name
        :param str service_name: Service Name
        :param str service_type: Service Type
        :param str session: Session
        :param float timeout: API timeout, None or 0 disables
        :param bool timings: Timings
        :param str user_domain_id: ID of user domain
        :param str user_domain_name: Name of user domain
        :param str user_id: User ID
        :param str username: Username
        """
        if direct_use:
            raise exceptions.Forbidden(
                403, _("'novaclient.v2.client.Client' is not designed to be "
                       "initialized directly. It is inner class of "
                       "novaclient. You should use "
                       "'novaclient.client.Client' instead. Related lp "
                       "bug-report: 1493576"))

        # NOTE(cyeoh): In the novaclient context (unlike Nova) the
        # project_id is not the same as the tenant_id. Here project_id
        # is a name (what the Nova API often refers to as a project or
        # tenant name) and tenant_id is a UUID (what the Nova API
        # often refers to as a project_id or tenant_id).

        self.project_id = project_id
        self.project_name = project_name
        self.user_id = user_id
        self.flavors = flavors.FlavorManager(self)
        self.flavor_access = flavor_access.FlavorAccessManager(self)
        self.glance = images.GlanceManager(self)
        self.limits = limits.LimitsManager(self)
        self.servers = servers.ServerManager(self)
        self.versions = versions.VersionManager(self)

        # extensions
        self.agents = agents.AgentsManager(self)
        self.volumes = volumes.VolumeManager(self)
        self.keypairs = keypairs.KeypairManager(self)
        self.neutron = networks.NeutronManager(self)
        self.quota_classes = quota_classes.QuotaClassSetManager(self)
        self.quotas = quotas.QuotaSetManager(self)
        self.usage = usage.UsageManager(self)
        self.aggregates = aggregates.AggregateManager(self)
        self.hypervisors = hypervisors.HypervisorManager(self)
        self.hypervisor_stats = hypervisors.HypervisorStatsManager(self)
        self.services = services.ServiceManager(self)
        self.os_cache = os_cache
        self.availability_zones = \
            availability_zones.AvailabilityZoneManager(self)
        self.server_groups = server_groups.ServerGroupsManager(self)
        self.server_migrations = \
            server_migrations.ServerMigrationsManager(self)

        # V2.0 extensions:
        # NOTE(andreykurilin): tenant_networks extension is
        #   deprecated now, which is why it is not initialized by default.
        self.assisted_volume_snapshots = \
            assisted_volume_snapshots.AssistedSnapshotManager(self)
        self.instance_action = instance_action.InstanceActionManager(self)
        self.instance_usage_audit_log = \
            instance_usage_audit_log.InstanceUsageAuditLogManager(self)
        self.migrations = migrations.MigrationManager(self)
        self.server_external_events = \
            server_external_events.ServerExternalEventManager(self)

        self.logger = logger or logging.getLogger(__name__)

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

        self.client = client._construct_http_client(
            api_version=api_version,
            auth=auth,
            auth_token=auth_token,
            auth_url=auth_url,
            cacert=cacert,
            cert=cert,
            endpoint_override=endpoint_override,
            endpoint_type=endpoint_type,
            http_log_debug=http_log_debug,
            insecure=insecure,
            logger=self.logger,
            os_cache=self.os_cache,
            password=password,
            project_domain_id=project_domain_id,
            project_domain_name=project_domain_name,
            project_id=project_id,
            project_name=project_name,
            region_name=region_name,
            service_name=service_name,
            service_type=service_type,
            session=session,
            timeout=timeout,
            timings=timings,
            user_domain_id=user_domain_id,
            user_domain_name=user_domain_name,
            user_id=user_id,
            username=username,
            **kwargs)

    @property
    def api_version(self):
        return self.client.api_version

    @api_version.setter
    def api_version(self, value):
        self.client.api_version = value

    def __enter__(self):
        raise exceptions.InvalidUsage(_(
            "NovaClient instance can't be used as a context manager "
            "since it is redundant in case of SessionClient."))

    def __exit__(self, t, v, tb):
        # do not do anything
        pass

    def get_timings(self):
        return self.client.get_timings()

    def reset_timings(self):
        self.client.reset_timings()

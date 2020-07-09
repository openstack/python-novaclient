# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack Foundation
# Copyright 2011 Piston Cloud Computing, Inc.

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

"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import itertools
import pkgutil
import warnings

from keystoneauth1 import adapter
from keystoneauth1 import identity
from keystoneauth1 import session as ksession
from oslo_utils import importutils
import stevedore

import novaclient
from novaclient import api_versions
from novaclient import exceptions
from novaclient import extension as ext
from novaclient.i18n import _
from novaclient import utils

osprofiler_profiler = importutils.try_import("osprofiler.profiler")
osprofiler_web = importutils.try_import("osprofiler.web")


class SessionClient(adapter.LegacyJsonAdapter):

    client_name = 'python-novaclient'
    client_version = novaclient.__version__

    def __init__(self, *args, **kwargs):
        self.times = []
        self.timings = kwargs.pop('timings', False)
        self.api_version = kwargs.pop('api_version', None)
        self.api_version = self.api_version or api_versions.APIVersion()
        super(SessionClient, self).__init__(*args, **kwargs)

    def request(self, url, method, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        api_versions.update_headers(kwargs["headers"], self.api_version)

        # NOTE(dbelova): osprofiler_web.get_trace_id_headers does not add any
        # headers in case if osprofiler is not initialized.
        if osprofiler_web:
            kwargs['headers'].update(osprofiler_web.get_trace_id_headers())

        # NOTE(jamielennox): The standard call raises errors from
        # keystoneauth1, where we need to raise the novaclient errors.
        raise_exc = kwargs.pop('raise_exc', True)
        with utils.record_time(self.times, self.timings, method, url):
            resp, body = super(SessionClient, self).request(url,
                                                            method,
                                                            raise_exc=False,
                                                            **kwargs)

        # TODO(andreykurilin): uncomment this line, when we will be able to
        #   check only nova-related calls
        # api_versions.check_headers(resp, self.api_version)
        if raise_exc and resp.status_code >= 400:
            raise exceptions.from_response(resp, body, url, method)

        return resp, body

    def get_timings(self):
        return self.times

    def reset_timings(self):
        self.times = []


def _construct_http_client(api_version=None,
                           auth=None,
                           auth_token=None,
                           auth_url=None,
                           cacert=None,
                           cert=None,
                           endpoint_override=None,
                           endpoint_type='publicURL',
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
                           user_agent='python-novaclient',
                           user_domain_id=None,
                           user_domain_name=None,
                           user_id=None,
                           username=None,
                           **kwargs):
    if not session:
        if not auth and auth_token:
            auth = identity.Token(auth_url=auth_url,
                                  token=auth_token,
                                  project_id=project_id,
                                  project_name=project_name,
                                  project_domain_id=project_domain_id,
                                  project_domain_name=project_domain_name)
        elif not auth:
            auth = identity.Password(username=username,
                                     user_id=user_id,
                                     password=password,
                                     project_id=project_id,
                                     project_name=project_name,
                                     auth_url=auth_url,
                                     project_domain_id=project_domain_id,
                                     project_domain_name=project_domain_name,
                                     user_domain_id=user_domain_id,
                                     user_domain_name=user_domain_name)
        session = ksession.Session(auth=auth,
                                   verify=(cacert or not insecure),
                                   timeout=timeout,
                                   cert=cert,
                                   user_agent=user_agent)

    return SessionClient(api_version=api_version,
                         auth=auth,
                         endpoint_override=endpoint_override,
                         interface=endpoint_type,
                         logger=logger,
                         region_name=region_name,
                         service_name=service_name,
                         service_type=service_type,
                         session=session,
                         timings=timings,
                         user_agent=user_agent,
                         **kwargs)


def discover_extensions(*args, **kwargs):
    """Returns the list of extensions, which can be discovered by python path
    and by entry-point 'novaclient.extension'.
    """
    chain = itertools.chain(_discover_via_python_path(),
                            _discover_via_entry_points())
    return [ext.Extension(name, module) for name, module in chain]


def _discover_via_python_path():
    for (module_loader, name, _ispkg) in pkgutil.iter_modules():
        if name.endswith('_python_novaclient_ext'):
            # NOTE(sdague): needed for python 2.x compatibility.
            if not hasattr(module_loader, 'load_module'):
                module_loader = module_loader.find_module(name)
            module = module_loader.load_module(name)
            if hasattr(module, 'extension_name'):
                name = module.extension_name

            yield name, module


def _make_discovery_manager():
    # This function provides a place to mock out the entry point scan
    return stevedore.ExtensionManager('novaclient.extension')


def _discover_via_entry_points():
    mgr = _make_discovery_manager()
    for extension in mgr:
        yield extension.name, extension.plugin


def _get_client_class_and_version(version):
    if not isinstance(version, api_versions.APIVersion):
        version = api_versions.get_api_version(version)
    else:
        api_versions.check_major_version(version)
    if version.is_latest():
        raise exceptions.UnsupportedVersion(
            _("The version should be explicit, not latest."))
    return version, importutils.import_class(
        "novaclient.v%s.client.Client" % version.ver_major)


def _check_arguments(kwargs, release, deprecated_name, right_name=None):
    """Process deprecation of arguments.

    Checks presence of deprecated argument in kwargs, prints proper warning
    message, renames key to right one it needed.
    """
    if deprecated_name in kwargs:
        if right_name:
            if right_name in kwargs:
                msg = _("The '%(old)s' argument is deprecated in "
                        "%(release)s and its use may result in errors "
                        "in future releases. As '%(new)s' is provided, "
                        "the '%(old)s' argument will be ignored.") % {
                    "old": deprecated_name, "release": release,
                    "new": right_name}
                kwargs.pop(deprecated_name)
            else:
                msg = _("The '%(old)s' argument is deprecated in "
                        "%(release)s and its use may result in errors in "
                        "future releases. Use '%(right)s' instead.") % {
                    "old": deprecated_name, "release": release,
                    "right": right_name}
                kwargs[right_name] = kwargs.pop(deprecated_name)

        else:
            msg = _("The '%(old)s' argument is deprecated in %(release)s "
                    "and its use may result in errors in future "
                    "releases.") % {
                "old": deprecated_name, "release": release}
            # just ignore it
            kwargs.pop(deprecated_name)

        warnings.warn(msg)


def Client(version, username=None, password=None, project_id=None,
           auth_url=None, **kwargs):
    """Initialize client object based on given version.

    HOW-TO:
    The simplest way to create a client instance is initialization with your
    credentials::

        >>> from novaclient import client
        >>> nova = client.Client(VERSION, USERNAME, PASSWORD,
        ...                      PROJECT_ID, AUTH_URL)

    Here ``VERSION`` can be a string or
    ``novaclient.api_versions.APIVersion`` obj. If you prefer string value,
    you can use ``1.1`` (deprecated now), ``2`` or ``2.X``
    (where X is a microversion).


    Alternatively, you can create a client instance using the keystoneauth
    session API. See "The novaclient Python API" page at
    python-novaclient's doc.
    """
    if password:
        kwargs["password"] = password
    if project_id:
        kwargs["project_id"] = project_id

    _check_arguments(kwargs, "Ocata", "auth_plugin")
    _check_arguments(kwargs, "Ocata", "auth_system")
    if "no_cache" in kwargs:
        _check_arguments(kwargs, "Ocata", "no_cache", right_name="os_cache")
        # os_cache is not a fully compatible with no_cache, so we need to
        # apply this custom processing
        kwargs["os_cache"] = not kwargs["os_cache"]
    _check_arguments(kwargs, "Ocata", "bypass_url",
                     right_name="endpoint_override")
    _check_arguments(kwargs, "Ocata", "api_key", right_name="password")
    # NOTE(andreykurilin): OpenStack projects use two variables with one
    #   meaning: 'endpoint_type' and 'interface'. 'endpoint_type' is an old
    #   name which was used by most OpenStack clients. Later it was replaced by
    #  'interface' in keystone and later some other clients switched to new
    #   variable name too. In case of novaclient, there is no need to switch to
    #  'interface' variable name due too several reasons:
    #     - novaclient uses 'endpoint_type' variable name long time ago and
    #       there is no real reasons to switch to new name;
    #     - 'interface' argument is used in several shell subcommands
    #       (for example in `nova floating-ip-bulk-create`), so we will need to
    #       modify these subcommands to not conflict with global flag
    #       'interface'
    #   Actually, novaclient did not accept 'interface' before, but since we
    #   allow additional arguments(kwargs), someone can use this variable name
    #   and face issue about unexpected behavior.
    _check_arguments(kwargs, "Ocata", "interface", right_name="endpoint_type")
    _check_arguments(kwargs, "Ocata", "tenant_name", right_name="project_name")
    _check_arguments(kwargs, "Ocata", "tenant_id", right_name="project_id")
    _check_arguments(kwargs, "Ocata", "proxy_tenant_id")
    _check_arguments(kwargs, "Ocata", "proxy_token")
    _check_arguments(kwargs, "Ocata", "connection_pool")
    _check_arguments(kwargs, "Ocata", "volume_service_name")

    api_version, client_class = _get_client_class_and_version(version)
    kwargs.pop("direct_use", None)

    profile = kwargs.pop("profile", None)
    if osprofiler_profiler and profile:
        # Initialize the root of the future trace: the created trace ID will
        # be used as the very first parent to which all related traces will be
        # bound to. The given HMAC key must correspond to the one set in
        # nova-api nova.conf, otherwise the latter will fail to check the
        # request signature and will skip initialization of osprofiler on
        # the server side.
        osprofiler_profiler.init(profile)

    return client_class(api_version=api_version,
                        auth_url=auth_url,
                        direct_use=False,
                        username=username,
                        **kwargs)

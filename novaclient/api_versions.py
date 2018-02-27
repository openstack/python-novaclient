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

import functools
import logging
import os
import pkgutil
import re
import traceback
import warnings

from oslo_utils import strutils

import novaclient
from novaclient import exceptions
from novaclient.i18n import _

LOG = logging.getLogger(__name__)
if not LOG.handlers:
    LOG.addHandler(logging.StreamHandler())


LEGACY_HEADER_NAME = "X-OpenStack-Nova-API-Version"
HEADER_NAME = "OpenStack-API-Version"
SERVICE_TYPE = "compute"

_SUBSTITUTIONS = {}

_type_error_msg = _("'%(other)s' should be an instance of '%(cls)s'")


class APIVersion(object):
    """This class represents an API Version Request.

    This class provides convenience methods for manipulation
    and comparison of version numbers that we need to do to
    implement microversions.
    """

    def __init__(self, version_str=None):
        """Create an API version object.

        :param version_str: String representation of APIVersionRequest.
                            Correct format is 'X.Y', where 'X' and 'Y'
                            are int values. None value should be used
                            to create Null APIVersionRequest, which is
                            equal to 0.0
        """
        self.ver_major = 0
        self.ver_minor = 0

        if version_str is not None:
            match = re.match(r"^([1-9]\d*)\.([1-9]\d*|0|latest)$", version_str)
            if match:
                self.ver_major = int(match.group(1))
                if match.group(2) == "latest":
                    # NOTE(andreykurilin): Infinity allows to easily determine
                    # latest version and doesn't require any additional checks
                    # in comparison methods.
                    self.ver_minor = float("inf")
                else:
                    self.ver_minor = int(match.group(2))
            else:
                msg = _("Invalid format of client version '%s'. "
                        "Expected format 'X.Y', where X is a major part and Y "
                        "is a minor part of version.") % version_str
                raise exceptions.UnsupportedVersion(msg)

    def __str__(self):
        """Debug/Logging representation of object."""
        if self.is_latest():
            return "Latest API Version Major: %s" % self.ver_major
        return ("API Version Major: %s, Minor: %s"
                % (self.ver_major, self.ver_minor))

    def __repr__(self):
        if self.is_null():
            return "<APIVersion: null>"
        else:
            return "<APIVersion: %s>" % self.get_string()

    def is_null(self):
        return self.ver_major == 0 and self.ver_minor == 0

    def is_latest(self):
        return self.ver_minor == float("inf")

    def __lt__(self, other):
        if not isinstance(other, APIVersion):
            raise TypeError(_type_error_msg % {"other": other,
                                               "cls": self.__class__})

        return ((self.ver_major, self.ver_minor) <
                (other.ver_major, other.ver_minor))

    def __eq__(self, other):
        if not isinstance(other, APIVersion):
            raise TypeError(_type_error_msg % {"other": other,
                                               "cls": self.__class__})

        return ((self.ver_major, self.ver_minor) ==
                (other.ver_major, other.ver_minor))

    def __gt__(self, other):
        if not isinstance(other, APIVersion):
            raise TypeError(_type_error_msg % {"other": other,
                                               "cls": self.__class__})

        return ((self.ver_major, self.ver_minor) >
                (other.ver_major, other.ver_minor))

    def __le__(self, other):
        return self < other or self == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        return self > other or self == other

    def matches(self, min_version, max_version):
        """Matches the version object.

        Returns whether the version object represents a version
        greater than or equal to the minimum version and less than
        or equal to the maximum version.

        :param min_version: Minimum acceptable version.
        :param max_version: Maximum acceptable version.
        :returns: boolean

        If min_version is null then there is no minimum limit.
        If max_version is null then there is no maximum limit.
        If self is null then raise ValueError
        """

        if self.is_null():
            raise ValueError(_("Null APIVersion doesn't support 'matches'."))
        if max_version.is_null() and min_version.is_null():
            return True
        elif max_version.is_null():
            return min_version <= self
        elif min_version.is_null():
            return self <= max_version
        else:
            return min_version <= self <= max_version

    def get_string(self):
        """Version string representation.

        Converts object to string representation which if used to create
        an APIVersion object results in the same version.
        """
        if self.is_null():
            raise ValueError(
                _("Null APIVersion cannot be converted to string."))
        elif self.is_latest():
            return "%s.%s" % (self.ver_major, "latest")
        return "%s.%s" % (self.ver_major, self.ver_minor)


class VersionedMethod(object):

    def __init__(self, name, start_version, end_version, func):
        """Versioning information for a single method

        :param name: Name of the method
        :param start_version: Minimum acceptable version
        :param end_version: Maximum acceptable_version
        :param func: Method to call

        Minimum and maximums are inclusive
        """
        self.name = name
        self.start_version = start_version
        self.end_version = end_version
        self.func = func

    def __str__(self):
        return ("Version Method %s: min: %s, max: %s"
                % (self.name, self.start_version, self.end_version))

    def __repr__(self):
        return "<VersionedMethod %s>" % self.name


def get_available_major_versions():
    # NOTE(andreykurilin): available clients version should not be
    # hardcoded, so let's discover them.
    matcher = re.compile(r"v[0-9]*$")
    submodules = pkgutil.iter_modules([os.path.dirname(__file__)])
    available_versions = [name[1:] for loader, name, ispkg in submodules
                          if matcher.search(name)]

    return available_versions


def check_major_version(api_version):
    """Checks major part of ``APIVersion`` obj is supported.

    :raises novaclient.exceptions.UnsupportedVersion: if major part is not
                                                      supported
    """
    available_versions = get_available_major_versions()
    if (not api_version.is_null() and
            str(api_version.ver_major) not in available_versions):
        if len(available_versions) == 1:
            msg = _("Invalid client version '%(version)s'. "
                    "Major part should be '%(major)s'") % {
                "version": api_version.get_string(),
                "major": available_versions[0]}
        else:
            msg = _("Invalid client version '%(version)s'. "
                    "Major part must be one of: '%(major)s'") % {
                "version": api_version.get_string(),
                "major": ", ".join(available_versions)}
        raise exceptions.UnsupportedVersion(msg)


def get_api_version(version_string):
    """Returns checked APIVersion object"""
    version_string = str(version_string)
    if strutils.is_int_like(version_string):
        version_string = "%s.0" % version_string

    api_version = APIVersion(version_string)
    check_major_version(api_version)
    return api_version


def _get_server_version_range(client):
    version = client.versions.get_current()

    if not hasattr(version, 'version') or not version.version:
        return APIVersion(), APIVersion()

    return APIVersion(version.min_version), APIVersion(version.version)


def discover_version(client, requested_version):
    """Discover most recent version supported by API and client.

    Checks ``requested_version`` and returns the most recent version
    supported by both the API and the client.

    :param client: client object
    :param requested_version: requested version represented by APIVersion obj
    :returns: APIVersion
    """
    server_start_version, server_end_version = _get_server_version_range(
        client)

    if (not requested_version.is_latest() and
            requested_version != APIVersion('2.0')):
        if server_start_version.is_null() and server_end_version.is_null():
            raise exceptions.UnsupportedVersion(
                _("Server doesn't support microversions"))
        if not requested_version.matches(server_start_version,
                                         server_end_version):
            raise exceptions.UnsupportedVersion(
                _("The specified version isn't supported by server. The valid "
                  "version range is '%(min)s' to '%(max)s'") % {
                    "min": server_start_version.get_string(),
                    "max": server_end_version.get_string()})
        return requested_version

    if requested_version == APIVersion('2.0'):
        if (server_start_version == APIVersion('2.1') or
                (server_start_version.is_null() and
                 server_end_version.is_null())):
            return APIVersion('2.0')
        else:
            raise exceptions.UnsupportedVersion(
                _("The server isn't backward compatible with Nova V2 REST "
                  "API"))

    if server_start_version.is_null() and server_end_version.is_null():
        return APIVersion('2.0')
    elif novaclient.API_MIN_VERSION > server_end_version:
        raise exceptions.UnsupportedVersion(
            _("Server version is too old. The client valid version range is "
              "'%(client_min)s' to '%(client_max)s'. The server valid version "
              "range is '%(server_min)s' to '%(server_max)s'.") % {
                  'client_min': novaclient.API_MIN_VERSION.get_string(),
                  'client_max': novaclient.API_MAX_VERSION.get_string(),
                  'server_min': server_start_version.get_string(),
                  'server_max': server_end_version.get_string()})
    elif novaclient.API_MAX_VERSION < server_start_version:
        raise exceptions.UnsupportedVersion(
            _("Server version is too new. The client valid version range is "
              "'%(client_min)s' to '%(client_max)s'. The server valid version "
              "range is '%(server_min)s' to '%(server_max)s'.") % {
                  'client_min': novaclient.API_MIN_VERSION.get_string(),
                  'client_max': novaclient.API_MAX_VERSION.get_string(),
                  'server_min': server_start_version.get_string(),
                  'server_max': server_end_version.get_string()})
    elif novaclient.API_MAX_VERSION <= server_end_version:
        return novaclient.API_MAX_VERSION
    elif server_end_version < novaclient.API_MAX_VERSION:
        return server_end_version


def update_headers(headers, api_version):
    """Set microversion headers if api_version is not null"""

    if not api_version.is_null():
        version_string = api_version.get_string()
        if api_version.ver_minor != 0:
            headers[LEGACY_HEADER_NAME] = version_string
        if api_version.ver_minor >= 27:
            headers[HEADER_NAME] = '%s %s' % (SERVICE_TYPE, version_string)


def check_headers(response, api_version):
    """Checks that microversion header is in response."""
    if api_version.ver_minor > 0:
        if (api_version.ver_minor < 27
                and LEGACY_HEADER_NAME not in response.headers):
            _warn_missing_microversion_header(LEGACY_HEADER_NAME)
        elif (api_version.ver_minor >= 27
                and HEADER_NAME not in response.headers):
            _warn_missing_microversion_header(HEADER_NAME)


def _add_substitution(versioned_method):
    _SUBSTITUTIONS.setdefault(versioned_method.name, [])
    _SUBSTITUTIONS[versioned_method.name].append(versioned_method)


def _get_function_name(func):
    # NOTE(andreykurilin): Based on the facts:
    #  - Python 2 does not have __qualname__ property as Python 3 has;
    #  - we cannot use im_class here, since we need to obtain name of
    #    function in `wraps` decorator during class initialization
    #    ("im_class" property does not exist at that moment)
    #  we need to write own logic to obtain the full function name which
    #  include module name, owner name(optional) and just function name.
    filename, _lineno, _name, line = traceback.extract_stack()[-4]
    module, _file_extension = os.path.splitext(filename)
    module = module.replace("/", ".")
    if module.endswith(func.__module__):
        return "%s.[%s].%s" % (func.__module__, line, func.__name__)
    else:
        return "%s.%s" % (func.__module__, func.__name__)


def get_substitutions(func_name, api_version=None):
    if hasattr(func_name, "__id__"):
        func_name = func_name.__id__

    substitutions = _SUBSTITUTIONS.get(func_name, [])
    if api_version and not api_version.is_null():
        return [m for m in substitutions
                if api_version.matches(m.start_version, m.end_version)]
    return sorted(substitutions, key=lambda m: m.start_version)


# FIXME(mriedem): This breaks any ManagerWithFind.list method that has a
# 'detailed' kwarg since the ManagerWithFind.findall won't find the correct
# argspec from the wrapped list method.
def wraps(start_version, end_version=None):
    start_version = APIVersion(start_version)
    if end_version:
        end_version = APIVersion(end_version)
    else:
        end_version = APIVersion("%s.latest" % start_version.ver_major)

    def decor(func):
        func.versioned = True
        name = _get_function_name(func)

        versioned_method = VersionedMethod(name, start_version,
                                           end_version, func)
        _add_substitution(versioned_method)

        @functools.wraps(func)
        def substitution(obj, *args, **kwargs):
            methods = get_substitutions(name, obj.api_version)

            if not methods:
                raise exceptions.VersionNotFoundForAPIMethod(
                    obj.api_version.get_string(), name)
            return methods[-1].func(obj, *args, **kwargs)

        # Let's share "arguments" with original method and substitution to
        # allow put utils.arg and wraps decorators in any order
        if not hasattr(func, 'arguments'):
            func.arguments = []
        substitution.arguments = func.arguments

        # NOTE(andreykurilin): The way to obtain function's name in Python 2
        #   bases on traceback(see _get_function_name for details). Since the
        #   right versioned method is used in several places, one object
        #   can have different names. Let's generate name of function one time
        #   and use __id__ property in all other places.
        substitution.__id__ = name

        return substitution

    return decor


def _warn_missing_microversion_header(header_name):
    """Log a warning about missing microversion response header."""
    LOG.warning(_(
        "Your request was processed by a Nova API which does not support "
        "microversions (%s header is missing from response). "
        "Warning: Response may be incorrect."), header_name)


def deprecated_after(version):
    decorator = wraps('2.0', version)

    def wrapper(fn):
        @functools.wraps(fn)
        def wrapped(*a, **k):
            decorated = decorator(fn)
            if hasattr(fn, '__module__'):
                mod = fn.__module__
            else:
                mod = a[0].__module__
            warnings.warn('The %s module is deprecated '
                          'and will be removed.' % mod, DeprecationWarning)
            return decorated(*a, **k)
        return wrapped
    return wrapper

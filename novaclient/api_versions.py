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
import os
import pkgutil
import re

from oslo_utils import strutils

from novaclient import exceptions
from novaclient.i18n import _, _LW

LOG = logging.getLogger(__name__)
if not LOG.handlers:
    LOG.addHandler(logging.StreamHandler())


# key is a deprecated version and value is an alternative version.
DEPRECATED_VERSIONS = {"1.1": "2"}


_type_error_msg = _("'%(other)s' should be an instance of '%(cls)s'")


class APIVersion(object):
    """This class represents an API Version with convenience
    methods for manipulation and comparison of version
    numbers that we need to do to implement microversions.
    """

    def __init__(self, version_str=None):
        """Create an API version object."""
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
        """Returns whether the version object represents a version
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
        """Converts object to string representation which if used to create
        an APIVersion object results in the same version.
        """
        if self.is_null():
            raise ValueError(
                _("Null APIVersion cannot be converted to string."))
        elif self.is_latest():
            return "%s.%s" % (self.ver_major, "latest")
        return "%s.%s" % (self.ver_major, self.ver_minor)


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
    if version_string in DEPRECATED_VERSIONS:
        LOG.warning(
            _LW("Version %(deprecated_version)s is deprecated, using "
                "alternative version %(alternative)s instead.") %
            {"deprecated_version": version_string,
             "alternative": DEPRECATED_VERSIONS[version_string]})
        version_string = DEPRECATED_VERSIONS[version_string]
    if strutils.is_int_like(version_string):
        version_string = "%s.0" % version_string

    api_version = APIVersion(version_string)
    check_major_version(api_version)
    return api_version


def update_headers(headers, api_version):
    """Set 'X-OpenStack-Nova-API-Version' header if api_version is not null"""

    if not api_version.is_null() and api_version.ver_minor != 0:
        headers["X-OpenStack-Nova-API-Version"] = api_version.get_string()

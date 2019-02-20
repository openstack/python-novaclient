#   Copyright 2012 OpenStack Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import pbr.version

from novaclient import api_versions


__version__ = pbr.version.VersionInfo('python-novaclient').version_string()

API_MIN_VERSION = api_versions.APIVersion("2.1")
# The max version should be the latest version that is supported in the client,
# not necessarily the latest that the server can provide. This is only bumped
# when client supported the max version, and bumped sequentially, otherwise
# the client may break due to server side new version may include some
# backward incompatible change.
API_MAX_VERSION = api_versions.APIVersion("2.72")

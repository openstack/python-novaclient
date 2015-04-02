# Copyright 2011 OpenStack Foundation
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

from novaclient import api_versions
from novaclient.openstack.common import cliutils


@api_versions.wraps("2.10", "2.20")
def do_fake_action():
    return 1


@api_versions.wraps("2.21", "2.30")
def do_fake_action():
    return 2


@cliutils.arg(
    '--foo',
    start_version='2.1',
    end_version='2.2')
@cliutils.arg(
    '--bar',
    start_version='2.3',
    end_version='2.4')
def do_fake_action2():
    return 3

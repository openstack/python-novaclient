# Copyright (C) 2013, Red Hat, Inc.
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
Assisted volume snapshots - to be used by Cinder and not end users.
"""

from novaclient.v2 import assisted_volume_snapshots
from novaclient.v2 import contrib


AssistedSnapshotManager = assisted_volume_snapshots.AssistedSnapshotManager
Snapshot = assisted_volume_snapshots.Snapshot

manager_class = AssistedSnapshotManager
name = 'assisted_volume_snapshots'

contrib.warn()

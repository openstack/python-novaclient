# Copyright 2016 Mirantis, Inc.
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

from novaclient.tests.functional import base


class TestImageMetaV239(base.ClientTestBase):
    """Functional tests for image-meta proxy API."""

    # 'image-metadata' proxy API was deprecated in 2.39 but the CLI should
    # fallback to 2.35 and emit a warning.
    COMPUTE_API_VERSION = "2.39"

    def test_limits(self):
        """Tests that 2.39 won't return 'maxImageMeta' resource limit and
        the CLI output won't show it.
        """
        output = self.nova('limits')
        # assert that MaxImageMeta isn't in the table output
        self.assertRaises(ValueError, self._get_value_from_the_table,
                          output, 'maxImageMeta')

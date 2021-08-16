# Copyright 2012 OpenStack Foundation
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

import importlib
import inspect
from unittest import mock

import stevedore
from stevedore import extension

from novaclient import client
from novaclient.tests.unit import utils


class DiscoverTest(utils.TestCase):

    def test_discover_via_entry_points(self):

        def mock_mgr():
            fake_ep = mock.Mock()
            fake_ep.name = 'foo'
            module_spec = importlib.machinery.ModuleSpec('foo', None)
            fake_ep.module = importlib.util.module_from_spec(module_spec)
            fake_ep.load.return_value = fake_ep.module
            fake_ext = extension.Extension(
                name='foo',
                entry_point=fake_ep,
                plugin=fake_ep.module,
                obj=None,
            )
            return stevedore.ExtensionManager.make_test_instance([fake_ext])

        @mock.patch.object(client, '_make_discovery_manager', mock_mgr)
        def test():
            for name, module in client._discover_via_entry_points():
                self.assertEqual('foo', name)
                self.assertTrue(inspect.ismodule(module))

        test()

    def test_discover_extensions(self):

        def mock_discover_via_python_path():
            module_spec = importlib.machinery.ModuleSpec('foo', None)
            module = importlib.util.module_from_spec(module_spec)
            yield 'foo', module

        def mock_discover_via_entry_points():
            module_spec = importlib.machinery.ModuleSpec('baz', None)
            module = importlib.util.module_from_spec(module_spec)
            yield 'baz', module

        @mock.patch.object(client,
                           '_discover_via_python_path',
                           mock_discover_via_python_path)
        @mock.patch.object(client,
                           '_discover_via_entry_points',
                           mock_discover_via_entry_points)
        def test():
            extensions = client.discover_extensions('1.1')
            self.assertEqual(2, len(extensions))
            names = sorted(['foo', 'baz'])
            sorted_extensions = sorted(extensions, key=lambda ext: ext.name)
            for i in range(len(names)):
                ext = sorted_extensions[i]
                name = names[i]
                self.assertEqual(ext.name, name)
                self.assertTrue(inspect.ismodule(ext.module))

        test()

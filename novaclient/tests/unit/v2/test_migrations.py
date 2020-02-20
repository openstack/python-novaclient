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
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import migrations


class MigrationsTest(utils.TestCase):
    def setUp(self):
        super(MigrationsTest, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.1"))

    def test_list_migrations(self):
        ml = self.cs.migrations.list()
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-migrations')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
            self.assertRaises(AttributeError, getattr, m, "migration_type")
            self.assertRaises(AttributeError, getattr, m, "uuid")

    def test_list_migrations_with_filters(self):
        ml = self.cs.migrations.list('host1', 'finished')
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)

        self.cs.assert_called(
            'GET',
            '/os-migrations?host=host1&status=finished')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)

    def test_list_migrations_with_instance_uuid_filter(self):
        ml = self.cs.migrations.list('host1', 'finished', 'instance_id_456')
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)

        self.cs.assert_called(
            'GET',
            ('/os-migrations?host=host1&'
             'instance_uuid=instance_id_456&status=finished'))
        self.assertEqual(1, len(ml))
        self.assertEqual('instance_id_456', ml[0].instance_uuid)


class MigrationsV223Test(MigrationsTest):
    def setUp(self):
        super(MigrationsV223Test, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.23")

    def test_list_migrations(self):
        ml = self.cs.migrations.list()
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-migrations')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
            self.assertEqual(m.migration_type, 'live-migration')
            self.assertRaises(AttributeError, getattr, m, "uuid")


class MigrationsV259Test(MigrationsV223Test):
    def setUp(self):
        super(MigrationsV259Test, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.59")

    def test_list_migrations(self):
        ml = self.cs.migrations.list()
        self.assert_request_id(ml, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-migrations')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
            self.assertEqual(m.migration_type, 'live-migration')
            self.assertTrue(hasattr(m, 'uuid'))

    def test_list_migrations_with_limit_marker_params(self):
        marker = '12140183-c814-4ddf-8453-6df43028aa67'
        params = {'limit': 10,
                  'marker': marker,
                  'changes_since': '2012-02-29T06:23:22'}

        ms = self.cs.migrations.list(**params)
        self.assert_request_id(ms, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET',
                              '/os-migrations?'
                              'changes-since=%s&limit=10&marker=%s'
                              % ('2012-02-29T06%3A23%3A22', marker))
        for m in ms:
            self.assertIsInstance(m, migrations.Migration)


class MigrationsV266Test(MigrationsV259Test):
    def setUp(self):
        super(MigrationsV266Test, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.66")

    def test_list_migrations_with_changes_before(self):
        params = {'changes_before': '2012-02-29T06:23:22'}
        ms = self.cs.migrations.list(**params)
        self.assert_request_id(ms, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET',
                              '/os-migrations?'
                              'changes-before=%s' %
                              '2012-02-29T06%3A23%3A22')
        for m in ms:
            self.assertIsInstance(m, migrations.Migration)


class MigrationsV280Test(MigrationsV266Test):
    def setUp(self):
        super(MigrationsV280Test, self).setUp()
        self.cs.api_version = api_versions.APIVersion("2.80")

    def test_list_migrations_with_user_id(self):
        user_id = '13cc0930d27c4be0acc14d7c47a3e1f7'
        params = {'user_id': user_id}
        ms = self.cs.migrations.list(**params)
        self.assert_request_id(ms, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-migrations?user_id=%s' % user_id)
        for m in ms:
            self.assertIsInstance(m, migrations.Migration)

    def test_list_migrations_with_project_id(self):
        project_id = 'b59c18e5fa284fd384987c5cb25a1853'
        params = {'project_id': project_id}
        ms = self.cs.migrations.list(**params)
        self.assert_request_id(ms, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/os-migrations?project_id=%s'
                              % project_id)
        for m in ms:
            self.assertIsInstance(m, migrations.Migration)

    def test_list_migrations_with_user_and_project_id(self):
        user_id = '13cc0930d27c4be0acc14d7c47a3e1f7'
        project_id = 'b59c18e5fa284fd384987c5cb25a1853'
        params = {'user_id': user_id, 'project_id': project_id}
        ms = self.cs.migrations.list(**params)
        self.assert_request_id(ms, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET',
                              '/os-migrations?project_id=%s&user_id=%s'
                              % (project_id, user_id))
        for m in ms:
            self.assertIsInstance(m, migrations.Migration)

    def test_list_migrations_with_user_id_pre_v280(self):
        self.cs.api_version = api_versions.APIVersion('2.79')
        user_id = '13cc0930d27c4be0acc14d7c47a3e1f7'
        ex = self.assertRaises(TypeError,
                               self.cs.migrations.list,
                               user_id=user_id)
        self.assertIn("unexpected keyword argument 'user_id'", str(ex))

    def test_list_migrations_with_project_id_pre_v280(self):
        self.cs.api_version = api_versions.APIVersion('2.79')
        project_id = '23cc0930d27c4be0acc14d7c47a3e1f7'
        ex = self.assertRaises(TypeError,
                               self.cs.migrations.list,
                               project_id=project_id)
        self.assertIn("unexpected keyword argument 'project_id'", str(ex))

# Copyright (c) 2013, OpenStack
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

from unittest import mock

from novaclient import api_versions
from novaclient import base
from novaclient import exceptions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import flavors


class FlavorsTest(utils.TestCase):
    def setUp(self):
        super(FlavorsTest, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion("2.0"))
        self.flavor_type = self._get_flavor_type()

    def _get_flavor_type(self):
        return flavors.Flavor

    def test_list_flavors(self):
        fl = self.cs.flavors.list()
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/detail')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_list_flavors_undetailed(self):
        fl = self.cs.flavors.list(detailed=False)
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_list_flavors_with_marker_limit(self):
        fl = self.cs.flavors.list(marker=1234, limit=4)
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/detail?limit=4&marker=1234')

    def test_list_flavors_with_min_disk(self):
        fl = self.cs.flavors.list(min_disk=20)
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/detail?minDisk=20')

    def test_list_flavors_with_min_ram(self):
        fl = self.cs.flavors.list(min_ram=512)
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/detail?minRam=512')

    def test_list_flavors_with_sort_key_dir(self):
        fl = self.cs.flavors.list(sort_key='id', sort_dir='asc')
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET',
                              '/flavors/detail?sort_dir=asc&sort_key=id')

    def test_list_flavors_is_public_none(self):
        fl = self.cs.flavors.list(is_public=None)
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/detail?is_public=None')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_list_flavors_is_public_false(self):
        fl = self.cs.flavors.list(is_public=False)
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/detail?is_public=False')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_list_flavors_is_public_true(self):
        fl = self.cs.flavors.list(is_public=True)
        self.assert_request_id(fl, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/detail')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_get_flavor_details(self):
        f = self.cs.flavors.get(1)
        self.assert_request_id(f, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/1')
        self.assertIsInstance(f, self.flavor_type)
        self.assertEqual(256, f.ram)
        self.assertEqual(10, f.disk)
        self.assertEqual(10, f.ephemeral)
        self.assertTrue(f.is_public)

    def test_get_flavor_details_alphanum_id(self):
        f = self.cs.flavors.get('aa1')
        self.assert_request_id(f, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/aa1')
        self.assertIsInstance(f, self.flavor_type)
        self.assertEqual(128, f.ram)
        self.assertEqual(0, f.disk)
        self.assertEqual(0, f.ephemeral)
        self.assertTrue(f.is_public)

    def test_get_flavor_details_diablo(self):
        f = self.cs.flavors.get(3)
        self.assert_request_id(f, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/3')
        self.assertIsInstance(f, self.flavor_type)
        self.assertEqual(256, f.ram)
        self.assertEqual(10, f.disk)
        self.assertEqual('N/A', f.ephemeral)
        self.assertEqual('N/A', f.is_public)

    def test_find(self):
        f = self.cs.flavors.find(ram=256)
        self.assert_request_id(f, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('GET', '/flavors/detail')
        self.assertEqual('256 MiB Server', f.name)

        f = self.cs.flavors.find(disk=0)
        self.assert_request_id(f, fakes.FAKE_REQUEST_ID_LIST)
        self.assertEqual('128 MiB Server', f.name)

        self.assertRaises(exceptions.NotFound, self.cs.flavors.find,
                          disk=12345)

    @staticmethod
    def _create_body(name, ram, vcpus, disk, ephemeral, id, swap,
                     rxtx_factor, is_public):
        return {
            "flavor": {
                "name": name,
                "ram": ram,
                "vcpus": vcpus,
                "disk": disk,
                "OS-FLV-EXT-DATA:ephemeral": ephemeral,
                "id": id,
                "swap": swap,
                "rxtx_factor": rxtx_factor,
                "os-flavor-access:is_public": is_public,
            }
        }

    def test_create(self):
        f = self.cs.flavors.create("flavorcreate", 512, 1, 10, 1234,
                                   ephemeral=10, is_public=False)
        self.assert_request_id(f, fakes.FAKE_REQUEST_ID_LIST)

        body = self._create_body("flavorcreate", 512, 1, 10, 10, 1234, 0, 1.0,
                                 False)

        self.cs.assert_called('POST', '/flavors', body)
        self.assertIsInstance(f, self.flavor_type)

    def test_create_with_id_as_string(self):
        flavor_id = 'foobar'
        f = self.cs.flavors.create("flavorcreate", 512,
                                   1, 10, flavor_id, ephemeral=10,
                                   is_public=False)
        self.assert_request_id(f, fakes.FAKE_REQUEST_ID_LIST)

        body = self._create_body("flavorcreate", 512, 1, 10, 10, flavor_id, 0,
                                 1.0, False)

        self.cs.assert_called('POST', '/flavors', body)
        self.assertIsInstance(f, self.flavor_type)

    def test_create_ephemeral_ispublic_defaults(self):
        f = self.cs.flavors.create("flavorcreate", 512, 1, 10, 1234)
        self.assert_request_id(f, fakes.FAKE_REQUEST_ID_LIST)

        body = self._create_body("flavorcreate", 512, 1, 10, 0, 1234, 0,
                                 1.0, True)

        self.cs.assert_called('POST', '/flavors', body)
        self.assertIsInstance(f, self.flavor_type)

    def test_invalid_parameters_create(self):
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", "invalid", 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, "invalid", 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, "invalid", 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap="invalid",
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral="invalid", rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor="invalid", is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public='invalid')

    def test_delete(self):
        ret = self.cs.flavors.delete("flavordelete")
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('DELETE', '/flavors/flavordelete')

    def test_delete_with_flavor_instance(self):
        f = self.cs.flavors.get(2)
        ret = self.cs.flavors.delete(f)
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('DELETE', '/flavors/2')

    def test_delete_with_flavor_instance_method(self):
        f = self.cs.flavors.get(2)
        ret = f.delete()
        self.assert_request_id(ret, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('DELETE', '/flavors/2')

    def test_set_keys(self):
        f = self.cs.flavors.get(1)
        fk = f.set_keys({'k1': 'v1'})
        self.assert_request_id(fk, fakes.FAKE_REQUEST_ID_LIST)
        self.cs.assert_called('POST', '/flavors/1/os-extra_specs',
                              {"extra_specs": {'k1': 'v1'}})

    def test_set_with_valid_keys(self):
        valid_keys = ['key4', 'month.price', 'I-Am:AK-ey.44-',
                      'key with spaces and _']

        f = self.cs.flavors.get(4)
        for key in valid_keys:
            fk = f.set_keys({key: 'v4'})
            self.assert_request_id(fk, fakes.FAKE_REQUEST_ID_LIST)
            self.cs.assert_called('POST', '/flavors/4/os-extra_specs',
                                  {"extra_specs": {key: 'v4'}})

    def test_set_with_invalid_keys(self):
        invalid_keys = ['/1', '?1', '%1', '<', '>']

        f = self.cs.flavors.get(1)
        for key in invalid_keys:
            self.assertRaises(exceptions.CommandError, f.set_keys, {key: 'v1'})

    @mock.patch.object(flavors.FlavorManager, '_delete')
    def test_unset_keys(self, mock_delete):
        f = self.cs.flavors.get(1)
        keys = ['k1', 'k2']
        mock_delete.return_value = base.TupleWithMeta(
            (), fakes.FAKE_REQUEST_ID_LIST)
        fu = f.unset_keys(keys)
        self.assert_request_id(fu, fakes.FAKE_REQUEST_ID_LIST)
        mock_delete.assert_has_calls([
            mock.call("/flavors/1/os-extra_specs/k1"),
            mock.call("/flavors/1/os-extra_specs/k2")
        ])


class FlavorsTest_v2_55(utils.TestCase):
    """Tests creating/showing/updating a flavor with a description."""
    def setUp(self):
        super(FlavorsTest_v2_55, self).setUp()
        self.cs = fakes.FakeClient(api_versions.APIVersion('2.55'))

    def test_list_flavors(self):
        fl = self.cs.flavors.list()
        self.cs.assert_called('GET', '/flavors/detail')
        for flavor in fl:
            self.assertTrue(hasattr(flavor, 'description'),
                            "%s does not have a description set." % flavor)

    def test_list_flavors_undetailed(self):
        fl = self.cs.flavors.list(detailed=False)
        self.cs.assert_called('GET', '/flavors')
        for flavor in fl:
            self.assertTrue(hasattr(flavor, 'description'),
                            "%s does not have a description set." % flavor)

    def test_get_flavor_details(self):
        f = self.cs.flavors.get('with-description')
        self.cs.assert_called('GET', '/flavors/with-description')
        self.assertEqual('test description', f.description)

    def test_create(self):
        self.cs.flavors.create(
            'with-description', 512, 1, 10, 'with-description', ephemeral=10,
            is_public=False, description='test description')

        body = FlavorsTest._create_body(
            "with-description", 512, 1, 10, 10, 'with-description',
            0, 1.0, False)
        body['flavor']['description'] = 'test description'
        self.cs.assert_called('POST', '/flavors', body)

    def test_create_bad_version(self):
        """Tests trying to create a flavor with a description before 2.55."""
        self.cs.api_version = api_versions.APIVersion('2.54')
        self.assertRaises(exceptions.UnsupportedAttribute,
                          self.cs.flavors.create,
                          'with-description', 512, 1, 10, 'with-description',
                          description='test description')

    def test_update(self):
        updated_flavor = self.cs.flavors.update(
            'with-description', 'new description')
        body = {
            'flavor': {
                'description': 'new description'
            }
        }
        self.cs.assert_called('PUT', '/flavors/with-description', body)
        self.assertEqual('new description', updated_flavor.description)

    def test_update_bad_version(self):
        """Tests trying to update a flavor with a description before 2.55."""
        self.cs.api_version = api_versions.APIVersion('2.54')
        self.assertRaises(exceptions.VersionNotFoundForAPIMethod,
                          self.cs.flavors.update, 'foo', 'bar')

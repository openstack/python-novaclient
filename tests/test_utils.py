
from novaclient import exceptions
from novaclient import utils
from tests import utils as test_utils


class FakeResource(object):
    pass


class FakeManager(object):

    resource_class = FakeResource

    resources = {
        '1234': {'name': 'entity_one'},
        '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0': {'name': 'entity_two'},
        '5678': {'name': '9876'}
    }

    def get(self, resource_id):
        try:
            return self.resources[str(resource_id)]
        except KeyError:
            raise exceptions.NotFound(resource_id)

    def find(self, name=None):
        for resource_id, resource in self.resources.items():
            if resource['name'] == str(name):
                return resource
        raise exceptions.NotFound(name)


class FindResourceTestCase(test_utils.TestCase):

    def setUp(self):
        self.manager = FakeManager()

    def test_find_none(self):
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          'asdf')

    def test_find_by_integer_id(self):
        output = utils.find_resource(self.manager, 1234)
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_str_id(self):
        output = utils.find_resource(self.manager, '1234')
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_uuid(self):
        uuid = '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0'
        output = utils.find_resource(self.manager, uuid)
        self.assertEqual(output, self.manager.resources[uuid])

    def test_find_by_str_name(self):
        output = utils.find_resource(self.manager, 'entity_one')
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_int_name(self):
        output = utils.find_resource(self.manager, 9876)
        self.assertEqual(output, self.manager.resources['5678'])


from novaclient.v1_0 import images
from tests.v1_0 import fakes
from tests import utils


cs = fakes.FakeClient()


class ImagesTest(utils.TestCase):

    def test_list_images(self):
        il = cs.images.list()
        cs.assert_called('GET', '/images/detail')
        [self.assertTrue(isinstance(i, images.Image)) for i in il]

    def test_list_images_undetailed(self):
        il = cs.images.list(detailed=False)
        cs.assert_called('GET', '/images')
        [self.assertTrue(isinstance(i, images.Image)) for i in il]

    def test_get_image_details(self):
        i = cs.images.get(1)
        cs.assert_called('GET', '/images/1')
        self.assertTrue(isinstance(i, images.Image))
        self.assertEqual(i.id, 1)
        self.assertEqual(i.name, 'CentOS 5.2')

    def test_create_image(self):
        i = cs.images.create(server=1234, name="Just in case")
        cs.assert_called('POST', '/images')
        self.assertTrue(isinstance(i, images.Image))

    def test_delete_image(self):
        cs.images.delete(1)
        cs.assert_called('DELETE', '/images/1')

    def test_find(self):
        i = cs.images.find(name="CentOS 5.2")
        self.assertEqual(i.id, 1)
        cs.assert_called('GET', '/images/detail')

        iml = cs.images.findall(status='SAVING')
        self.assertEqual(len(iml), 1)
        self.assertEqual(iml[0].name, 'My Server Backup')

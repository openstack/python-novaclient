from __future__ import absolute_import

from nose.tools import assert_equal

from novaclient.v1_1 import images

from .fakes import FakeClient
from .utils import assert_isinstance

os = FakeClient()


def test_list_images():
    il = os.images.list()
    os.assert_called('GET', '/images/detail')
    [assert_isinstance(i, images.Image) for i in il]


def test_list_images_undetailed():
    il = os.images.list(detailed=False)
    os.assert_called('GET', '/images')
    [assert_isinstance(i, images.Image) for i in il]


def test_get_image_details():
    i = os.images.get(1)
    os.assert_called('GET', '/images/1')
    assert_isinstance(i, images.Image)
    assert_equal(i.id, 1)
    assert_equal(i.name, 'CentOS 5.2')


def test_create_image():
    i = os.images.create(server=1234, name="Just in case")
    os.assert_called('POST', '/images')
    assert_isinstance(i, images.Image)


def test_delete_image():
    os.images.delete(1)
    os.assert_called('DELETE', '/images/1')


def test_find():
    i = os.images.find(name="CentOS 5.2")
    assert_equal(i.id, 1)
    os.assert_called('GET', '/images/detail')

    iml = os.images.findall(status='SAVING')
    assert_equal(len(iml), 1)
    assert_equal(iml[0].name, 'My Server Backup')

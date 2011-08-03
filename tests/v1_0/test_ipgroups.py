from __future__ import absolute_import

from nose.tools import assert_equal

from novaclient.v1_0 import ipgroups

from .fakes import FakeClient
from .utils import assert_isinstance

os = FakeClient()


def test_list_ipgroups():
    ipl = os.ipgroups.list()
    os.assert_called('GET', '/shared_ip_groups/detail')
    [assert_isinstance(ipg, ipgroups.IPGroup) for ipg in ipl]


def test_list_ipgroups_undetailed():
    ipl = os.ipgroups.list(detailed=False)
    os.assert_called('GET', '/shared_ip_groups')
    [assert_isinstance(ipg, ipgroups.IPGroup) for ipg in ipl]


def test_get_ipgroup():
    ipg = os.ipgroups.get(1)
    os.assert_called('GET', '/shared_ip_groups/1')
    assert_isinstance(ipg, ipgroups.IPGroup)


def test_create_ipgroup():
    ipg = os.ipgroups.create("My group", 1234)
    os.assert_called('POST', '/shared_ip_groups')
    assert_isinstance(ipg, ipgroups.IPGroup)


def test_delete_ipgroup():
    ipg = os.ipgroups.get(1)
    ipg.delete()
    os.assert_called('DELETE', '/shared_ip_groups/1')
    os.ipgroups.delete(ipg)
    os.assert_called('DELETE', '/shared_ip_groups/1')
    os.ipgroups.delete(1)
    os.assert_called('DELETE', '/shared_ip_groups/1')


def test_find():
    ipg = os.ipgroups.find(name='group1')
    os.assert_called('GET', '/shared_ip_groups/detail')
    assert_equal(ipg.name, 'group1')
    ipgl = os.ipgroups.findall(id=1)
    assert_equal(ipgl, [ipgroups.IPGroup(None, {'id': 1})])

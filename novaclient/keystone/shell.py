# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack LLC.
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

import httplib2
import urllib
import urlparse

try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from novaclient import exceptions
from novaclient import utils
from novaclient import client


@utils.unauthenticated
def do_discover(cs, args):
    """
    Discover Keystone servers and show authentication protocols supported.

    Usage:
    $ nova discover
    Keystone found at http://localhost:35357
        - supports version v2.0 (beta) here http://localhost:35357/v2.0
    Keystone found at https://openstack.org/
        - supports version v1.0 (DEPRECATED) here https://openstack.org/v1.0
        - supports version v1.1 (CURRENT) here https://openstack.org/v1.1
        - supports version v2.0 (BETA) here https://openstack.org/v2.0
    """
    _local_keystone_exists()
    _check_keystone_versions(cs.client.auth_url)


def _local_keystone_exists():
    return _check_keystone_versions("http://localhost:35357")


def _check_keystone_versions(url):
    try:
        httpclient = client.HTTPClient(user=None, password=None,
                            projectid=None, auth_url=None)
        resp, body = httpclient.request(url, "GET",
                                  headers={'Accept': 'application/json'})
        if resp.status in (200, 204):  # in some cases we get No Content
            try:
                print "Keystone found at %s" % url
                if 'version' in body:
                    version = body['version']
                    # Stable/diablo incorrect format
                    _display_version_info(version, url)
                    return True
                if 'versions' in body:
                    # Correct format
                    for version in body['versions']['values']:
                        _display_version_info(version, url)
                    return True
                print "Unrecognized response from %s" % url
            except KeyError:
                raise exceptions.AuthorizationFailure()
        elif resp.status == 305:
            return _check_keystone_versions(resp['location'])
        else:
            raise exceptions.from_response(resp, body)
    except:
        return False


def _display_version_info(version, url):
    id = version['id']
    status = version['status']
    ref = urlparse.urljoin(url, id)
    if 'links' in version:
        for link in version['links']:
            if link['rel'] == 'self':
                ref = link['href']
                break
    print "    - supports version %s (%s) here %s" % (id, status, ref)

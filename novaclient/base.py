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

"""
Base utilities to build API operation managers and objects on top of.
"""

import contextlib
import os
from novaclient import exceptions
from novaclient import utils


# Python 2.4 compat
try:
    all
except NameError:
    def all(iterable):
        return True not in (not x for x in iterable)


def getid(obj):
    """
    Abstracts the common pattern of allowing both an object or an object's ID
    (UUID) as a parameter when dealing with relationships.
    """

    # Try to return the object's UUID first, if we have a UUID.
    try:
        if obj.uuid:
            return obj.uuid
    except AttributeError:
        pass
    try:
        return obj.id
    except AttributeError:
        return obj


class Manager(utils.HookableMixin):
    """
    Managers interact with a particular type of API (servers, flavors, images,
    etc.) and provide CRUD operations for them.
    """
    resource_class = None

    def __init__(self, api):
        self.api = api

    def _list(self, url, response_key, obj_class=None, body=None):
        resp = None
        if body:
            resp, body = self.api.client.post(url, body=body)
        else:
            resp, body = self.api.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        # NOTE(ja): keystone returns values as list as {'values': [ ... ]}
        #           unlike other services which just return the list...
        if isinstance(data, dict):
            try:
                data = data['values']
            except KeyError:
                pass

        with self.uuid_cache(obj_class, mode="w"):
            return [obj_class(self, res, loaded=True) for res in data if res]

    @contextlib.contextmanager
    def uuid_cache(self, obj_class, mode):
        """
        Cache UUIDs for bash autocompletion.

        The UUID cache works by checking to see whether an ID is UUID-like when
        we create a resource object (e.g. a Image or a Server), and if it is,
        we add it to a local cache file.  We maintain one cache file per
        resource type so that we can refresh them independently.

        A resource listing will clear and repopulate the UUID cache.

        A resource create will append to the UUID cache.

        Delete is not handled because listings are assumed to be performed
        often enough to keep the UUID cache reasonably up-to-date.
        """
        resource = obj_class.__name__.lower()
        filename = os.path.expanduser("~/.novaclient_cached_%s_uuids" %
                                      resource)

        try:
            self._uuid_cache = open(filename, mode)
        except IOError:
            # NOTE(kiall): This is typicaly a permission denied while
            #              attempting to write the cache file.
            pass

        try:
            yield
        finally:
            if hasattr(self, '_uuid_cache'):
                self._uuid_cache.close()
                del self._uuid_cache

    def write_uuid_to_cache(self, uuid):
        if hasattr(self, '_uuid_cache'):
            self._uuid_cache.write("%s\n" % uuid)

    def _get(self, url, response_key):
        resp, body = self.api.client.get(url)
        return self.resource_class(self, body[response_key])

    def _create(self, url, body, response_key, return_raw=False, **kwargs):
        self.run_hooks('modify_body_for_create', body, **kwargs)
        resp, body = self.api.client.post(url, body=body)
        if return_raw:
            return body[response_key]

        with self.uuid_cache(self.resource_class, mode="a"):
            return self.resource_class(self, body[response_key])

    def _delete(self, url):
        resp, body = self.api.client.delete(url)

    def _update(self, url, body, **kwargs):
        self.run_hooks('modify_body_for_update', body, **kwargs)
        resp, body = self.api.client.put(url, body=body)
        return body


class ManagerWithFind(Manager):
    """
    Like a `Manager`, but with additional `find()`/`findall()` methods.
    """
    def find(self, **kwargs):
        """
        Find a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        rl = self.findall(**kwargs)
        try:
            return rl[0]
        except IndexError:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise exceptions.NotFound(404, msg)

    def findall(self, **kwargs):
        """
        Find all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = kwargs.items()

        for obj in self.list():
            try:
                if all(getattr(obj, attr) == value
                                    for (attr, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue

        return found

    def list(self):
        raise NotImplementedError


class BootingManagerWithFind(ManagerWithFind):
    """Like a `ManagerWithFind`, but has the ability to boot servers."""
    def _boot(self, resource_url, response_key, name, image, flavor,
              ipgroup=None, meta=None, files=None, zone_blob=None,
              reservation_id=None, return_raw=False, min_count=None,
              max_count=None, **kwargs):
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param ipgroup: An initial :class:`IPGroup` for this server.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param files: A dict of files to overrwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.
        :param zone_blob: a single (encrypted) string which is used internally
                      by Nova for routing between Zones. Users cannot populate
                      this field.
        :param reservation_id: a UUID for the set of servers being requested.
        :param return_raw: If True, don't try to coearse the result into
                           a Resource object.
        """
        body = {"server": {
            "name": name,
            "imageId": getid(image),
            "flavorId": getid(flavor),
        }}
        if ipgroup:
            body["server"]["sharedIpGroupId"] = getid(ipgroup)
        if meta:
            body["server"]["metadata"] = meta
        if reservation_id:
            body["server"]["reservation_id"] = reservation_id
        if zone_blob:
            body["server"]["blob"] = zone_blob

        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        body["server"]["min_count"] = min_count
        body["server"]["max_count"] = max_count

        # Files are a slight bit tricky. They're passed in a "personality"
        # list to the POST. Each item is a dict giving a file name and the
        # base64-encoded contents of the file. We want to allow passing
        # either an open file *or* some contents as files here.
        if files:
            personality = body['server']['personality'] = []
            for filepath, file_or_string in files.items():
                if hasattr(file_or_string, 'read'):
                    data = file_or_string.read()
                else:
                    data = file_or_string
                personality.append({
                    'path': filepath,
                    'contents': data.encode('base64'),
                })

        return self._create(resource_url, body, response_key,
                            return_raw=return_raw, **kwargs)


class Resource(object):
    """
    A resource represents a particular instance of an object (server, flavor,
    etc). This is pretty much just a bag for attributes.

    :param manager: Manager object
    :param info: dictionary representing resource attributes
    :param loaded: prevent lazy-loading if set to True
    """
    def __init__(self, manager, info, loaded=False):
        self.manager = manager
        self._info = info
        self._add_details(info)
        self._loaded = loaded

        # NOTE(sirp): ensure `id` is already present because if it isn't we'll
        # enter an infinite loop of __getattr__ -> get -> __init__ ->
        # __getattr__ -> ...
        if 'id' in self.__dict__ and len(str(self.id)) == 36:
            self.manager.write_uuid_to_cache(self.id)

    def _add_details(self, info):
        for (k, v) in info.iteritems():
            try:
                setattr(self, k, v)
            except AttributeError:
                # In this case we already defined the attribute on the class
                pass

    def __getattr__(self, k):
        if k not in self.__dict__:
            #NOTE(bcwaldon): disallow lazy-loading if already loaded once
            if not self.is_loaded():
                self.get()
                return self.__getattr__(k)

            raise AttributeError(k)
        else:
            return self.__dict__[k]

    def __repr__(self):
        reprkeys = sorted(k for k in self.__dict__.keys() if k[0] != '_' and
                                                                k != 'manager')
        info = ", ".join("%s=%s" % (k, getattr(self, k)) for k in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)

    def get(self):
        # set_loaded() first ... so if we have to bail, we know we tried.
        self.set_loaded(True)
        if not hasattr(self.manager, 'get'):
            return

        new = self.manager.get(self.id)
        if new:
            self._add_details(new._info)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        return self._info == other._info

    def is_loaded(self):
        return self._loaded

    def set_loaded(self, val):
        self._loaded = val

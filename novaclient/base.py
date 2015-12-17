# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
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

import abc
import contextlib
import copy
import hashlib
import inspect
import os
import threading

from oslo_utils import strutils
import six

from novaclient import exceptions
from novaclient import utils


def getid(obj):
    """Get object's ID or object.

    Abstracts the common pattern of allowing both an object or an object's ID
    as a parameter when dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return obj


# TODO(aababilov): call run_hooks() in HookableMixin's child classes
class HookableMixin(object):
    """Mixin so classes can register and run hooks."""
    _hooks_map = {}

    @classmethod
    def add_hook(cls, hook_type, hook_func):
        """Add a new hook of specified type.

        :param cls: class that registers hooks
        :param hook_type: hook type, e.g., '__pre_parse_args__'
        :param hook_func: hook function
        """
        if hook_type not in cls._hooks_map:
            cls._hooks_map[hook_type] = []

        cls._hooks_map[hook_type].append(hook_func)

    @classmethod
    def run_hooks(cls, hook_type, *args, **kwargs):
        """Run all hooks of specified type.

        :param cls: class that registers hooks
        :param hook_type: hook type, e.g., '__pre_parse_args__'
        :param args: args to be passed to every hook function
        :param kwargs: kwargs to be passed to every hook function
        """
        hook_funcs = cls._hooks_map.get(hook_type) or []
        for hook_func in hook_funcs:
            hook_func(*args, **kwargs)


class Resource(object):
    """Base class for OpenStack resources (tenant, user, etc.).

    This is pretty much just a bag for attributes.
    """

    HUMAN_ID = False
    NAME_ATTR = 'name'

    def __init__(self, manager, info, loaded=False):
        """Populate and bind to a manager.

        :param manager: BaseManager object
        :param info: dictionary representing resource attributes
        :param loaded: prevent lazy-loading if set to True
        """
        self.manager = manager
        self._info = info
        self._add_details(info)
        self._loaded = loaded

    def __repr__(self):
        reprkeys = sorted(k
                          for k in self.__dict__.keys()
                          if k[0] != '_' and k != 'manager')
        info = ", ".join("%s=%s" % (k, getattr(self, k)) for k in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)

    @property
    def human_id(self):
        """Human-readable ID which can be used for bash completion.
        """
        if self.HUMAN_ID:
            name = getattr(self, self.NAME_ATTR, None)
            if name is not None:
                return strutils.to_slug(name)
        return None

    def _add_details(self, info):
        for (k, v) in six.iteritems(info):
            try:
                setattr(self, k, v)
                self._info[k] = v
            except AttributeError:
                # In this case we already defined the attribute on the class
                pass

    def __getattr__(self, k):
        if k not in self.__dict__:
            # NOTE(bcwaldon): disallow lazy-loading if already loaded once
            if not self.is_loaded():
                self.get()
                return self.__getattr__(k)

            raise AttributeError(k)
        else:
            return self.__dict__[k]

    def get(self):
        """Support for lazy loading details.

        Some clients, such as novaclient have the option to lazy load the
        details, details which can be loaded with this function.
        """
        # set_loaded() first ... so if we have to bail, we know we tried.
        self.set_loaded(True)
        if not hasattr(self.manager, 'get'):
            return

        new = self.manager.get(self.id)
        if new:
            self._add_details(new._info)
            if self.manager.client.last_request_id:
                self._add_details(
                    {'x_request_id': self.manager.client.last_request_id})

    def __eq__(self, other):
        if not isinstance(other, Resource):
            return NotImplemented
        # two resources of different types are not equal
        if not isinstance(other, self.__class__):
            return False
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        return self._info == other._info

    def is_loaded(self):
        return self._loaded

    def set_loaded(self, val):
        self._loaded = val

    def to_dict(self):
        return copy.deepcopy(self._info)


class Manager(HookableMixin):
    """Manager for API service.

    Managers interact with a particular type of API (servers, flavors, images,
    etc.) and provide CRUD operations for them.
    """
    resource_class = None
    cache_lock = threading.RLock()

    def __init__(self, api):
        self.api = api

    @property
    def client(self):
        return self.api.client

    @property
    def api_version(self):
        return self.api.api_version

    def _list(self, url, response_key, obj_class=None, body=None):
        if body:
            _resp, body = self.api.client.post(url, body=body)
        else:
            _resp, body = self.api.client.get(url)

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

        with self.completion_cache('human_id', obj_class, mode="w"):
            with self.completion_cache('uuid', obj_class, mode="w"):
                return [obj_class(self, res, loaded=True)
                        for res in data if res]

    @contextlib.contextmanager
    def alternate_service_type(self, default, allowed_types=()):
        original_service_type = self.api.client.service_type
        if original_service_type in allowed_types:
            yield
        else:
            self.api.client.service_type = default
            try:
                yield
            finally:
                self.api.client.service_type = original_service_type

    @contextlib.contextmanager
    def completion_cache(self, cache_type, obj_class, mode):
        """The completion cache for bash autocompletion.

        The completion cache store items that can be used for bash
        autocompletion, like UUIDs or human-friendly IDs.

        A resource listing will clear and repopulate the cache.

        A resource create will append to the cache.

        Delete is not handled because listings are assumed to be performed
        often enough to keep the cache reasonably up-to-date.
        """
        # NOTE(wryan): This lock protects read and write access to the
        # completion caches
        with self.cache_lock:
            base_dir = utils.env('NOVACLIENT_UUID_CACHE_DIR',
                                 default="~/.novaclient")

            # NOTE(sirp): Keep separate UUID caches for each username +
            # endpoint pair
            username = utils.env('OS_USERNAME', 'NOVA_USERNAME')
            url = utils.env('OS_URL', 'NOVA_URL')
            uniqifier = hashlib.md5(username.encode('utf-8') +
                                    url.encode('utf-8')).hexdigest()

            cache_dir = os.path.expanduser(os.path.join(base_dir, uniqifier))

            try:
                os.makedirs(cache_dir, 0o755)
            except OSError:
                # NOTE(kiall): This is typically either permission denied while
                #              attempting to create the directory, or the
                #              directory already exists. Either way, don't
                #              fail.
                pass

            resource = obj_class.__name__.lower()
            filename = "%s-%s-cache" % (resource, cache_type.replace('_', '-'))
            path = os.path.join(cache_dir, filename)

            cache_attr = "_%s_cache" % cache_type

            try:
                setattr(self, cache_attr, open(path, mode))
            except IOError:
                # NOTE(kiall): This is typically a permission denied while
                #              attempting to write the cache file.
                pass

            try:
                yield
            finally:
                cache = getattr(self, cache_attr, None)
                if cache:
                    cache.close()
                    delattr(self, cache_attr)

    def write_to_completion_cache(self, cache_type, val):
        cache = getattr(self, "_%s_cache" % cache_type, None)
        if cache:
            cache.write("%s\n" % val)

    def _get(self, url, response_key):
        _resp, body = self.api.client.get(url)
        return self.resource_class(self, body[response_key], loaded=True)

    def _create(self, url, body, response_key, return_raw=False, **kwargs):
        self.run_hooks('modify_body_for_create', body, **kwargs)
        _resp, body = self.api.client.post(url, body=body)
        if return_raw:
            return body[response_key]

        with self.completion_cache('human_id', self.resource_class, mode="a"):
            with self.completion_cache('uuid', self.resource_class, mode="a"):
                return self.resource_class(self, body[response_key])

    def _delete(self, url):
        _resp, _body = self.api.client.delete(url)

    def _update(self, url, body, response_key=None, **kwargs):
        self.run_hooks('modify_body_for_update', body, **kwargs)
        _resp, body = self.api.client.put(url, body=body)
        if body:
            if response_key:
                return self.resource_class(self, body[response_key])
            else:
                return self.resource_class(self, body)


@six.add_metaclass(abc.ABCMeta)
class ManagerWithFind(Manager):
    """Like a `Manager`, but with additional `find()`/`findall()` methods."""

    @abc.abstractmethod
    def list(self):
        pass

    def find(self, **kwargs):
        """Find a single item with attributes matching ``**kwargs``."""
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise exceptions.NotFound(404, msg)
        elif num_matches > 1:
            raise exceptions.NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        """Find all items with attributes matching ``**kwargs``."""
        found = []
        searches = kwargs.items()

        detailed = True
        list_kwargs = {}

        list_argspec = inspect.getargspec(self.list)
        if 'detailed' in list_argspec.args:
            detailed = ("human_id" not in kwargs and
                        "name" not in kwargs and
                        "display_name" not in kwargs)
            list_kwargs['detailed'] = detailed

        if 'is_public' in list_argspec.args and 'is_public' in kwargs:
            is_public = kwargs['is_public']
            list_kwargs['is_public'] = is_public
            if is_public is None:
                tmp_kwargs = kwargs.copy()
                del tmp_kwargs['is_public']
                searches = tmp_kwargs.items()

        if 'search_opts' in list_argspec.args:
            # pass search_opts in to do server side based filtering.
            # TODO(jogo) not all search_opts support regex, find way to
            # identify when to use regex and when to use string matching.
            # volumes does not support regex while servers does. So when
            # doing findall on servers some client side filtering is still
            # needed.
            if "human_id" in kwargs:
                list_kwargs['search_opts'] = {"name": kwargs["human_id"]}
            elif "name" in kwargs:
                list_kwargs['search_opts'] = {"name": kwargs["name"]}
            elif "display_name" in kwargs:
                list_kwargs['search_opts'] = {"name": kwargs["display_name"]}
            if "all_tenants" in kwargs:
                all_tenants = kwargs['all_tenants']
                list_kwargs['search_opts']['all_tenants'] = all_tenants
                searches = [(k, v) for k, v in searches if k != 'all_tenants']

        listing = self.list(**list_kwargs)

        for obj in listing:
            try:
                if all(getattr(obj, attr) == value
                        for (attr, value) in searches):
                    if detailed:
                        found.append(obj)
                    else:
                        found.append(self.get(obj.id))
            except AttributeError:
                continue

        return found


class BootingManagerWithFind(ManagerWithFind):
    """Like a `ManagerWithFind`, but has the ability to boot servers."""

    def _parse_block_device_mapping(self, block_device_mapping):
        """Parses legacy block device mapping."""
        # FIXME(andreykurilin): make it work with block device mapping v2

        bdm = []

        for device_name, mapping in six.iteritems(block_device_mapping):
            #
            # The mapping is in the format:
            # <id>:[<type>]:[<size(GB)>]:[<delete_on_terminate>]
            #
            bdm_dict = {'device_name': device_name}

            mapping_parts = mapping.split(':')
            source_id = mapping_parts[0]

            if len(mapping_parts) == 1:
                bdm_dict['volume_id'] = source_id
            elif len(mapping_parts) > 1:
                source_type = mapping_parts[1]
                if source_type.startswith('snap'):
                    bdm_dict['snapshot_id'] = source_id
                else:
                    bdm_dict['volume_id'] = source_id

            if len(mapping_parts) > 2 and mapping_parts[2]:
                bdm_dict['volume_size'] = str(int(mapping_parts[2]))

            if len(mapping_parts) > 3:
                bdm_dict['delete_on_termination'] = mapping_parts[3]

            bdm.append(bdm_dict)
        return bdm

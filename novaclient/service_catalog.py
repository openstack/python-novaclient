# Copyright 2011, Piston Cloud Computing, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re


def get_resource(key):
    resource_classes = {
        "glance": GlanceCatalog,
        "identity": IdentityCatalog,
        "keystone": KeystoneCatalog,
        "nova": NovaCatalog,
        "nova_compat": NovaCompatCatalog,
        "swift": SwiftCatalog,
        "serviceCatalog": ServiceCatalog,
    }
    return resource_classes.get(key)


def snake_case(string):
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', string).lower()


class CatalogResource(object):
    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.public_url)

    def __init__(self, resource_dict):
        for key, value in resource_dict.items():
            if self.__catalog_key__ in value:
                for res_key, res_value in value.items():
                    for attr, val in res_value.items():
                        res = get_resource(attr)
                        if res:
                            attribute = [res(x) for x in val]
                            setattr(self, snake_case(attr), attribute)
            else:
                for key, attr in resource_dict.items():
                    setattr(self, snake_case(key), attr)


class TokenCatalog(CatalogResource):
    __catalog_key__ = "token"

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.id)


class NovaCatalog(CatalogResource):
    __catalog_key__ = "nova"


class KeystoneCatalog(CatalogResource):
    __catalog_key__ = 'keystone'


class GlanceCatalog(CatalogResource):
    __catalog_key__ = 'glance'


class SwiftCatalog(CatalogResource):
    __catalog_key__ = 'swift'


class IdentityCatalog(CatalogResource):
    __catalog_key__ = 'identity'


class NovaCompatCatalog(CatalogResource):
    __catalog_key__ = "nova_compat"


class ServiceCatalog(CatalogResource):
    __catalog_key__ = "serviceCatalog"

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.token.id)

    def __init__(self, resource):
        super(ServiceCatalog, self).__init__(resource)

        self.token = TokenCatalog(resource["auth"]["token"])

    def url_for(self, catalog_class, url, attr=None, filter_value=None):
        catalog = getattr(self, catalog_class)
        if attr and filter_value:
            catalog = [item for item in catalog
                            if hasattr(item, attr) and
                               getattr(item, attr) == filter_value]
            if not catalog:
                raise ValueError("No catalog entries for %s=%s" % 
                                  (attr, filter_value))
        if catalog:
            return getattr(catalog[0], url + "_url")

# Copyright 2010 Jacob Kaplan-Moss
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
Flavor interface.
"""

from oslo_utils import strutils

from novaclient import api_versions
from novaclient import base
from novaclient import exceptions
from novaclient.i18n import _
from novaclient import utils


class Flavor(base.Resource):
    """A flavor is an available hardware configuration for a server."""
    HUMAN_ID = True

    def __repr__(self):
        return "<Flavor: %s>" % self.name

    @property
    def ephemeral(self):
        """Provide a user-friendly accessor to OS-FLV-EXT-DATA:ephemeral."""
        return self._info.get("OS-FLV-EXT-DATA:ephemeral", 'N/A')

    @property
    def is_public(self):
        """Provide a user-friendly accessor to os-flavor-access:is_public."""
        return self._info.get("os-flavor-access:is_public", 'N/A')

    def get_keys(self):
        """
        Get extra specs from a flavor.

        :returns: An instance of novaclient.base.DictWithMeta
        """
        resp, body = self.manager.api.client.get(
            "/flavors/%s/os-extra_specs" % base.getid(self))
        return self.manager.convert_into_with_meta(body["extra_specs"], resp)

    def set_keys(self, metadata):
        """Set extra specs on a flavor.

        :param metadata: A dict of key/value pairs to be set
        """
        utils.validate_flavor_metadata_keys(metadata.keys())

        body = {'extra_specs': metadata}
        return self.manager._create(
            "/flavors/%s/os-extra_specs" % base.getid(self), body,
            "extra_specs", return_raw=True)

    def unset_keys(self, keys):
        """Unset extra specs on a flavor.

        :param keys: A list of keys to be unset
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        result = base.TupleWithMeta((), None)
        for k in keys:
            ret = self.manager._delete(
                "/flavors/%s/os-extra_specs/%s" % (base.getid(self), k))
            result.append_request_ids(ret.request_ids)

        return result

    def delete(self):
        """
        Delete this flavor.

        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self.manager.delete(self)

    @api_versions.wraps('2.55')
    def update(self, description=None):
        """
        Update the description for this flavor.

        :param description: The description to set on the flavor.
        :returns: :class:`Flavor`
        """
        return self.manager.update(self, description=description)


class FlavorManager(base.ManagerWithFind):
    """Manage :class:`Flavor` resources."""
    resource_class = Flavor
    is_alphanum_id_allowed = True

    def list(self, detailed=True, is_public=True, marker=None, min_disk=None,
             min_ram=None, limit=None, sort_key=None, sort_dir=None):
        """Get a list of all flavors.

        :param detailed: Whether flavor needs to be return with details
                         (optional).
        :param is_public: Filter flavors with provided access type (optional).
                          None means give all flavors and only admin has query
                          access to all flavor types.
        :param marker: Begin returning flavors that appear later in the flavor
                       list than that represented by this flavor id (optional).
        :param min_disk: Filters the flavors by a minimum disk space, in GiB.
        :param min_ram: Filters the flavors by a minimum RAM, in MB.
        :param limit: maximum number of flavors to return (optional).
        :param sort_key: Flavors list sort key (optional).
        :param sort_dir: Flavors list sort direction (optional).
        :returns: list of :class:`Flavor`.
        """
        qparams = {}
        # is_public is ternary - None means give all flavors.
        # By default Nova assumes True and gives admins public flavors
        # and flavors from their own projects only.
        if marker:
            qparams['marker'] = str(marker)
        if min_disk:
            qparams['minDisk'] = int(min_disk)
        if min_ram:
            qparams['minRam'] = int(min_ram)
        if limit:
            qparams['limit'] = int(limit)
        if sort_key:
            qparams['sort_key'] = str(sort_key)
        if sort_dir:
            qparams['sort_dir'] = str(sort_dir)
        if not is_public:
            qparams['is_public'] = is_public
        detail = ""
        if detailed:
            detail = "/detail"

        return self._list("/flavors%s" % detail, "flavors", filters=qparams)

    def get(self, flavor):
        """Get a specific flavor.

        :param flavor: The ID of the :class:`Flavor` to get.
        :returns: :class:`Flavor`
        """
        return self._get("/flavors/%s" % base.getid(flavor), "flavor")

    def delete(self, flavor):
        """Delete a specific flavor.

        :param flavor: Instance of :class:`Flavor` to delete or ID of the
                       flavor to delete.
        :returns: An instance of novaclient.base.TupleWithMeta
        """
        return self._delete("/flavors/%s" % base.getid(flavor))

    def _build_body(self, name, ram, vcpus, disk, id, swap,
                    ephemeral, rxtx_factor, is_public):
        return {
            "flavor": {
                "name": name,
                "ram": ram,
                "vcpus": vcpus,
                "disk": disk,
                "id": id,
                "swap": swap,
                "OS-FLV-EXT-DATA:ephemeral": ephemeral,
                "rxtx_factor": rxtx_factor,
                "os-flavor-access:is_public": is_public,
            }
        }

    def create(self, name, ram, vcpus, disk, flavorid="auto",
               ephemeral=0, swap=0, rxtx_factor=1.0, is_public=True,
               description=None):
        """Create a flavor.

        :param name: Descriptive name of the flavor
        :param ram: Memory in MB for the flavor
        :param vcpus: Number of VCPUs for the flavor
        :param disk: Size of local disk in GiB
        :param flavorid: ID for the flavor (optional). You can use the reserved
                         value ``"auto"`` to have Nova generate a UUID for the
                         flavor in cases where you cannot simply pass ``None``.
        :param ephemeral: Ephemeral disk space in GiB.
        :param swap: Swap space in MB
        :param rxtx_factor: RX/TX factor
        :param is_public: Whether or not the flavor is public.
        :param description: A free form description of the flavor.
                            Limited to 65535 characters in length.
                            Only printable characters are allowed.
                            (Available starting with microversion 2.55)
        :returns: :class:`Flavor`
        """

        try:
            ram = int(ram)
        except (TypeError, ValueError):
            raise exceptions.CommandError(_("Ram must be an integer."))
        try:
            vcpus = int(vcpus)
        except (TypeError, ValueError):
            raise exceptions.CommandError(_("VCPUs must be an integer."))
        try:
            disk = int(disk)
        except (TypeError, ValueError):
            raise exceptions.CommandError(_("Disk must be an integer."))

        if flavorid == "auto":
            flavorid = None

        try:
            swap = int(swap)
        except (TypeError, ValueError):
            raise exceptions.CommandError(_("Swap must be an integer."))
        try:
            ephemeral = int(ephemeral)
        except (TypeError, ValueError):
            raise exceptions.CommandError(_("Ephemeral must be an integer."))
        try:
            rxtx_factor = float(rxtx_factor)
        except (TypeError, ValueError):
            raise exceptions.CommandError(_("rxtx_factor must be a float."))

        try:
            is_public = strutils.bool_from_string(is_public, True)
        except Exception:
            raise exceptions.CommandError(_("is_public must be a boolean."))

        supports_description = api_versions.APIVersion('2.55')
        if description and self.api_version < supports_description:
            raise exceptions.UnsupportedAttribute('description', '2.55')

        body = self._build_body(name, ram, vcpus, disk, flavorid, swap,
                                ephemeral, rxtx_factor, is_public)
        if description:
            body['flavor']['description'] = description

        return self._create("/flavors", body, "flavor")

    @api_versions.wraps('2.55')
    def update(self, flavor, description=None):
        """
        Update the description of the flavor.

        :param flavor: The :class:`Flavor` (or its ID) to update.
        :param description: The description to set on the flavor.
        """
        body = {
            'flavor': {
                'description': description
            }
        }
        return self._update('/flavors/%s' % base.getid(flavor), body, 'flavor')

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

import base64

from novaclient import base


# FIXME(sirp): Now that v1_0 has been removed, this can be merged with
# base.ManagerWithFind
class BootingManagerWithFind(base.ManagerWithFind):
    """Like a `ManagerWithFind`, but has the ability to boot servers."""
    def _boot(self, resource_url, response_key, name, image, flavor,
              meta=None, files=None, zone_blob=None, userdata=None,
              reservation_id=None, return_raw=False, min_count=None,
              max_count=None, security_groups=None, key_name=None,
              availability_zone=None, block_device_mapping=None, nics=None,
              scheduler_hints=None, **kwargs):
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
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
        :param security_groups: list of security group names
        :param key_name: (optional extension) name of keypair to inject into
                         the instance
        :param availability_zone: The :class:`Zone`.
        :param block_device_mapping: A dict of block device mappings for this
                                     server.
        :param nics:  (optional extension) an ordered list of nics to be
                      added to this server, with information about
                      connected networks, fixed ips, etc.
        :param scheduler_hints: (optional extension) arbitrary key-value pairs
                              specified by the client to help boot an instance.
        """
        body = {"server": {
            "name": name,
            "imageRef": base.getid(image),
            "flavorRef": base.getid(flavor),
        }}
        if userdata:
            if hasattr(userdata, 'read'):
                userdata = userdata.read()
            body["server"]["user_data"] = base64.b64encode(userdata)
        if meta:
            body["server"]["metadata"] = meta
        if reservation_id:
            body["server"]["reservation_id"] = reservation_id
        if zone_blob:
            body["server"]["blob"] = zone_blob
        if key_name:
            body["server"]["key_name"] = key_name
        if scheduler_hints:
            body['os:scheduler_hints'] = scheduler_hints
        if not min_count:
            min_count = 1
        if not max_count:
            max_count = min_count
        body["server"]["min_count"] = min_count
        body["server"]["max_count"] = max_count

        if security_groups:
            body["server"]["security_groups"] =\
             [{'name': sg} for sg in security_groups]

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

        if availability_zone:
            body["server"]["availability_zone"] = availability_zone

        # Block device mappings are passed as a list of dictionaries
        if block_device_mapping:
            bdm = body['server']['block_device_mapping'] = []
            for device_name, mapping in block_device_mapping.items():
                #
                # The mapping is in the format:
                # <id>:[<type>]:[<size(GB)>]:[<delete_on_terminate>]
                #
                bdm_dict = {'device_name': device_name}

                mapping_parts = mapping.split(':')
                id = mapping_parts[0]
                if len(mapping_parts) == 1:
                    bdm_dict['volume_id'] = id
                if len(mapping_parts) > 1:
                    type = mapping_parts[1]
                    if type.startswith('snap'):
                        bdm_dict['snapshot_id'] = id
                    else:
                        bdm_dict['volume_id'] = id
                if len(mapping_parts) > 2:
                    bdm_dict['volume_size'] = mapping_parts[2]
                if len(mapping_parts) > 3:
                    bdm_dict['delete_on_termination'] = mapping_parts[3]
                bdm.append(bdm_dict)

        if nics:
            all_net_data = []
            for nic_info in nics:
                net_data = {}
                # if value is empty string, do not send value in body
                if nic_info['net-id']:
                    net_data['uuid'] = nic_info['net-id']
                if nic_info['v4-fixed-ip']:
                    net_data['fixed_ip'] = nic_info['v4-fixed-ip']
                all_net_data.append(net_data)
            body['server']['networks'] = all_net_data

        return self._create(resource_url, body, response_key,
                            return_raw=return_raw, **kwargs)

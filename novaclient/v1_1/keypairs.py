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
Keypair interface (1.1 extension).
"""

from novaclient import base


class Keypair(base.Resource):
    """
    A keypair is a ssh key that can be injected into a server on launch.
    """

    def __repr__(self):
        return "<Keypair: %s>" % self.uuid

    @property
    def uuid(self):
        return self.key_name

    def delete(self):
        self.manager.delete(self)


class KeypairManager(base.ManagerWithFind):
    resource_class = Keypair

    def create(self, key_name):
        """
        Create a keypair

        :param key_name: name for the keypair to create
        """
        body = {'keypair': {'key_name': key_name}}
        return self._create('/extras/keypairs', body, 'keypair')

    def delete(self, key):
        """
        Delete a keypair

        :param key: The :class:`Keypair` (or its ID) to delete.
        """
        self._delete('/extras/keypairs/%s' % (base.getid(key)))

    def list(self):
        """
        Get a list of keypairs.
        """
        return self._list('/extras/keypairs', 'keypairs')

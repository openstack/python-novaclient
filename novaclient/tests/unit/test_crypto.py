# Copyright 2018 NTT Corporation
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
import subprocess

import mock

from novaclient import crypto
from novaclient.tests.unit import utils


class CryptoTest(utils.TestCase):

    def setUp(self):
        super(CryptoTest, self).setUp()
        # The password string that passed as the method argument
        self.password_string = 'Test Password'
        # The return value of Popen.communicate
        self.decrypt_password = b'Decrypt Password'
        self.private_key = 'Test Private Key'

    @mock.patch('subprocess.Popen')
    def test_decrypt_password(self, mock_open):
        mocked_proc = mock.Mock()
        mock_open.return_value = mocked_proc
        mocked_proc.returncode = 0
        mocked_proc.communicate.return_value = (self.decrypt_password, '')

        decrypt_password = crypto.decrypt_password(self.private_key,
                                                   self.password_string)

        # The return value is 'str' in both python 2 and python 3
        self.assertIsInstance(decrypt_password, str)
        self.assertEqual('Decrypt Password', decrypt_password)

        mock_open.assert_called_once_with(
            ['openssl', 'rsautl', '-decrypt', '-inkey', self.private_key],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        mocked_proc.communicate.assert_called_once_with(
            base64.b64decode(self.password_string))
        mocked_proc.stdin.close.assert_called_once_with()

    @mock.patch('subprocess.Popen')
    def test_decrypt_password_failure(self, mock_open):
        mocked_proc = mock.Mock()
        mock_open.return_value = mocked_proc
        mocked_proc.returncode = 1  # Error case
        mocked_proc.communicate.return_value = (self.decrypt_password, '')

        self.assertRaises(crypto.DecryptionFailure, crypto.decrypt_password,
                          self.private_key, self.password_string)

        mock_open.assert_called_once_with(
            ['openssl', 'rsautl', '-decrypt', '-inkey', self.private_key],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        mocked_proc.communicate.assert_called_once_with(
            base64.b64decode(self.password_string))
        mocked_proc.stdin.close.assert_called_once_with()

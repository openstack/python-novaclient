#!/bin/bash -xe

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is executed inside post_test_hook function in devstack gate.

function generate_testr_results {
    if [ -f .testrepository/0 ]; then
        sudo .tox/functional/bin/testr last --subunit > $WORKSPACE/testrepository.subunit
        sudo mv $WORKSPACE/testrepository.subunit $BASE/logs/testrepository.subunit
        sudo /usr/os-testr-env/bin/subunit2html $BASE/logs/testrepository.subunit $BASE/logs/testr_results.html
        sudo gzip -9 $BASE/logs/testrepository.subunit
        sudo gzip -9 $BASE/logs/testr_results.html
        sudo chown jenkins:jenkins $BASE/logs/testrepository.subunit.gz $BASE/logs/testr_results.html.gz
        sudo chmod a+r $BASE/logs/testrepository.subunit.gz $BASE/logs/testr_results.html.gz
    fi
}

export NOVACLIENT_DIR="$BASE/new/python-novaclient"

sudo chown -R jenkins:stack $NOVACLIENT_DIR

# FIXME(melwitt): Currently, novaclient requires version in the
# auth url in order to work and it doesn't support keystone v3.
# Use v2.0 in the auth url in clouds.yaml to enable the functional
# test job to work until novaclient is updated to support v3
sudo sed -i -e 's/auth_url: \([^v ]\+\)\(\/v[0-9]\+\.\?[0-9]*\)\?$/auth_url: \1\/v2.0/g' /etc/openstack/clouds.yaml

# Go to the novaclient dir
cd $NOVACLIENT_DIR

# Run tests
echo "Running novaclient functional test suite"
set +e
# Preserve env for OS_ credentials
sudo -E -H -u jenkins tox -efunctional
EXIT_CODE=$?
set -e

# Collect and parse result
generate_testr_results
exit $EXIT_CODE

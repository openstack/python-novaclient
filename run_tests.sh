#!/bin/bash
#
# Copyright 2011, Piston Cloud Computing, Inc.
#
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

function usage {
    echo "Usage: $0 [OPTION] [nosearg1[=val]] [nosearg2[=val]]..."
    echo 
    echo "Run python-novaclient test suite"
    echo
    echo "  -f, --force             Delete the virtualenv before running tests."
    echo "  -h, --help              Print this usage message"
    echo "  -N, --no-virtual-env    Don't use a virtualenv" 
    echo "  -p, --pep8              Run pep8 in addition"
}


function die {
    echo $@
    exit 1
}


function process_args {
    case "$1" in
        -h|--help) usage && exit ;;
        -p|--pep8) let just_pep8=1; let use_venv=0 ;;
        -N|--no-virtual-env) let use_venv=0;;
        -f|--force) let force=1;;
        *) noseargs="$noseargs $1"
    esac
}


function run-command {
    res=$($@)

    if [ $? -ne 0 ]; then
        die "Command failed:", $res
    fi
}


function install-dependency {
    echo -n "installing $@..."
    run-command "pip install -E $venv $@"
    echo done
}


function build-venv-if-necessary {
    if [ $force -eq 1 ]; then
        echo -n "Removing virtualenv..."
        rm -rf $venv
        echo done
    fi

    if [ -d $venv ]; then 
        echo -n  # nothing to be done
    else
        if [ -z $(which virtualenv) ]; then 
            echo "Installing virtualenv"
            run-command "easy_install virtualenv"
        fi

        echo -n "creating virtualenv..."
        run-command "virtualenv -q --no-site-packages ${venv}"
        echo done

        for dep in $dependencies; do 
            install-dependency $dep
        done
    fi
}


function wrapper {
    if [ $use_venv -eq 1 ]; then
        build-venv-if-necessary
        source "$(dirname $0)/${venv}/bin/activate" && $@
    else
        $@
    fi
}


dependencies="httplib2 argparse prettytable simplejson nose mock coverage"
force=0
venv=.novaclient-venv
use_venv=1
verbose=0
noseargs=
just_pep8=0

for arg in "$@"; do 
    process_args $arg
done

NOSETESTS="nosetests ${noseargs}"

if [ $just_pep8 -ne 0 ]; then
    wrapper "pep8 -r --show-pep8 novaclient tests"
else
    wrapper $NOSETESTS
fi

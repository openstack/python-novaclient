# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2010 OpenStack, LLC
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
Installation script for Nova's development virtualenv
"""

import optparse
import os
import subprocess
import sys
import platform


ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
VENV = os.path.join(ROOT, '.venv')
PIP_REQUIRES = os.path.join(ROOT, 'tools', 'pip-requires')
TEST_REQUIRES = os.path.join(ROOT, 'tools', 'test-requires')
PY_VERSION = "python%s.%s" % (sys.version_info[0], sys.version_info[1])


def die(message, *args):
    print(message % args, file=sys.stderr)
    sys.exit(1)


def check_python_version():
    if sys.version_info < (2, 6):
        die("Need Python Version >= 2.6")


def run_command_with_code(cmd, redirect_output=True, check_exit_code=True):
    """
    Runs a command in an out-of-process shell, returning the
    output of that command.  Working directory is ROOT.
    """
    if redirect_output:
        stdout = subprocess.PIPE
    else:
        stdout = None

    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=stdout)
    output = proc.communicate()[0]
    if check_exit_code and proc.returncode != 0:
        die('Command "%s" failed.\n%s', ' '.join(cmd), output)
    return (output, proc.returncode)


def run_command(cmd, redirect_output=True, check_exit_code=True):
    return run_command_with_code(cmd, redirect_output, check_exit_code)[0]


class Distro(object):

    def check_cmd(self, cmd):
        return bool(run_command(['which', cmd], check_exit_code=False).strip())

    def install_virtualenv(self):
        if self.check_cmd('virtualenv'):
            return

        if self.check_cmd('easy_install'):
            print('Installing virtualenv via easy_install...')
            if run_command(['easy_install', 'virtualenv']):
                print('Succeeded')
                return
            else:
                print('Failed')

        die('ERROR: virtualenv not found.\n\nDevelopment'
            ' requires virtualenv, please install it using your'
            ' favorite package management tool')

    def post_process(self):
        """Any distribution-specific post-processing gets done here.

        In particular, this is useful for applying patches to code inside
        the venv."""
        pass


class Debian(Distro):
    """This covers all Debian-based distributions."""

    def check_pkg(self, pkg):
        return run_command_with_code(['dpkg', '-l', pkg],
                                     check_exit_code=False)[1] == 0

    def apt_install(self, pkg, **kwargs):
        run_command(['sudo', 'apt-get', 'install', '-y', pkg], **kwargs)

    def apply_patch(self, originalfile, patchfile):
        run_command(['patch', originalfile, patchfile])

    def install_virtualenv(self):
        if self.check_cmd('virtualenv'):
            return

        if not self.check_pkg('python-virtualenv'):
            self.apt_install('python-virtualenv', check_exit_code=False)

        super(Debian, self).install_virtualenv()


class Fedora(Distro):
    """This covers all Fedora-based distributions.

    Includes: Fedora, RHEL, CentOS, Scientific Linux"""

    def check_pkg(self, pkg):
        return run_command_with_code(['rpm', '-q', pkg],
                                     check_exit_code=False)[1] == 0

    def yum_install(self, pkg, **kwargs):
        run_command(['sudo', 'yum', 'install', '-y', pkg], **kwargs)

    def apply_patch(self, originalfile, patchfile):
        run_command(['patch', originalfile, patchfile])

    def install_virtualenv(self):
        if self.check_cmd('virtualenv'):
            return

        if not self.check_pkg('python-virtualenv'):
            self.yum_install('python-virtualenv', check_exit_code=False)

        super(Fedora, self).install_virtualenv()


def get_distro():
    if os.path.exists('/etc/fedora-release') or \
       os.path.exists('/etc/redhat-release'):
        return Fedora()
    elif os.path.exists('/etc/debian_version'):
        return Debian()
    else:
        return Distro()


def check_dependencies():
    get_distro().install_virtualenv()


def create_virtualenv(venv=VENV, no_site_packages=True):
    """Creates the virtual environment and installs PIP only into the
    virtual environment
    """
    print('Creating venv...')
    if no_site_packages:
        run_command(['virtualenv', '-q', '--no-site-packages', VENV])
    else:
        run_command(['virtualenv', '-q', VENV])
    print('done.')
    print('Installing pip in virtualenv...')
    if not run_command(['tools/with_venv.sh', 'easy_install',
                        'pip>1.0']).strip():
        die("Failed to install pip.")
    print('done.')


def pip_install(*args):
    run_command(['tools/with_venv.sh',
                 'pip', 'install', '--upgrade'] + list(args),
                redirect_output=False)


def install_dependencies(venv=VENV):
    print('Installing dependencies with pip (this can take a while)...')

    # First things first, make sure our venv has the latest pip and distribute.
    pip_install('pip')
    pip_install('distribute')

    pip_install('-r', PIP_REQUIRES)
    pip_install('-r', TEST_REQUIRES)

    # Tell the virtual env how to "import nova"
    pthfile = os.path.join(venv, "lib", PY_VERSION, "site-packages",
                        "novaclient.pth")
    f = open(pthfile, 'w')
    f.write("%s\n" % ROOT)


def post_process():
    get_distro().post_process()


def print_help():
    help = """
    python-novaclient development environment setup is complete.

    python-novaclient development uses virtualenv to track and manage Python
    dependencies while in development and testing.

    To activate the python-novaclient virtualenv for the extent of your current
    shell session you can run:

    $ source .venv/bin/activate

    Or, if you prefer, you can run commands in the virtualenv on a case by case
    basis by running:

    $ tools/with_venv.sh <your command>

    Also, make test will automatically use the virtualenv.
    """
    print(help)


def parse_args():
    """Parse command-line arguments"""
    parser = optparse.OptionParser()
    parser.add_option("-n", "--no-site-packages", dest="no_site_packages",
        default=False, action="store_true",
        help="Do not inherit packages from global Python install")
    return parser.parse_args()


def main(argv):
    (options, args) = parse_args()
    check_python_version()
    check_dependencies()
    create_virtualenv(no_site_packages=options.no_site_packages)
    install_dependencies()
    post_process()
    print_help()

if __name__ == '__main__':
    main(sys.argv)

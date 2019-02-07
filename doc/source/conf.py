# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# python-novaclient documentation build configuration file

# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'openstackdocstheme',
    'sphinx.ext.autodoc',
    'sphinxcontrib.apidoc',
]

# sphinxcontrib.apidoc options
apidoc_module_dir = '../../novaclient'
apidoc_output_dir = 'reference/api'
apidoc_excluded_paths = [
    'tests/*']
apidoc_separate_modules = True

# The content that will be inserted into the main body of an autoclass
# directive.
autoclass_content = 'both'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# openstackdocstheme options
repository_name = 'openstack/python-novaclient'
bug_project = 'python-novaclient'
bug_tag = 'doc'
project = 'python-novaclient'
copyright = 'OpenStack Contributors'

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = []

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'openstackdocs'

# Add any paths that contain "extra" files, such as .htaccess or
# robots.txt.
html_extra_path = ['_extra']

# -- Options for openstackdocstheme -------------------------------------------

repository_name = 'openstack/python-novaclient'
bug_project = 'python-novaclient'
bug_tag = ''
openstack_projects = [
    'keystoneauth',
    'os-client-config',
    'python-openstackclient',
]

# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('cli/nova', 'nova', 'OpenStack Nova command line client',
     ['OpenStack Contributors'], 1),
]

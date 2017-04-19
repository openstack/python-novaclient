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

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

sys.path.insert(0, ROOT)
sys.path.insert(0, BASE_DIR)


def gen_ref(ver, title, names):
    refdir = os.path.join(BASE_DIR, "ref")
    pkg = "novaclient"
    if ver:
        pkg = "%s.%s" % (pkg, ver)
        refdir = os.path.join(refdir, ver)
    if not os.path.exists(refdir):
        os.makedirs(refdir)
    idxpath = os.path.join(refdir, "index.rst")
    with open(idxpath, "w") as idx:
        idx.write(("%(title)s\n"
                   "%(signs)s\n"
                   "\n"
                   ".. toctree::\n"
                   "   :maxdepth: 1\n"
                   "\n") % {"title": title, "signs": "=" * len(title)})
        for name in names:
            idx.write("   %s\n" % name)
            rstpath = os.path.join(refdir, "%s.rst" % name)
            with open(rstpath, "w") as rst:
                rst.write(("%(title)s\n"
                           "%(signs)s\n"
                           "\n"
                           ".. automodule:: %(pkg)s.%(name)s\n"
                           "   :members:\n"
                           "   :undoc-members:\n"
                           "   :show-inheritance:\n"
                           "   :noindex:\n")
                          % {"title": name.capitalize(),
                             "signs": "=" * len(name),
                             "pkg": pkg, "name": name})


def get_module_names():
    names = os.listdir(os.path.join(ROOT, 'novaclient', 'v2'))
    exclude = ['shell.py', '__init__.py']
    for name in names:
        if name.endswith('.py') and name not in exclude:
            yield name.strip('.py')


gen_ref(None, "Exceptions", ["exceptions"])
gen_ref("v2", "Version 2 API", sorted(get_module_names()))

# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'oslosphinx']

autoclass_content = 'both'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
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
html_theme = 'default'

# Output file base name for HTML help builder.
htmlhelp_basename = 'python-novaclientdoc'

# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('man/nova', 'nova', 'OpenStack Nova command line client',
     ['OpenStack Contributors'], 1),
]

# -*- coding: utf-8 -*-
#
# python-novaclient Release Notes documentation build configuration file

# -- General configuration ------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'reno.sphinxext',
    'openstackdocstheme',
]

# The master toctree document.
master_doc = 'index'


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'openstackdocs'


# -- Options for Internationalization output ------------------------------

locale_dirs = ['locale/']

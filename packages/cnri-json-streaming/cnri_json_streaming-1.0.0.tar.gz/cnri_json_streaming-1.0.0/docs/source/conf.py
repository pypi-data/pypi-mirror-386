import datetime
import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'CNRI JSON Streaming'
copyright = f'{datetime.date.today().year}, CNRI'
author = 'CNRI'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = []

# autodoc options
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    # 'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}
add_module_names = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

# Required to document constructors, because sphinx-apidoc doesn't read conf.py autodoc_default_options. Sigh.
# See https://stackoverflow.com/a/75941415/6558116 and https://stackoverflow.com/a/5599712/6558116
def include_init(app, what, name, obj, would_skip, options):
    if name == "__init__" and getattr(obj, "__doc__", None):
        return False
    return would_skip

def setup(app):
    app.connect("autodoc-skip-member", include_init)

# Configuration file for the Sphinx documentation builder

# Add the project source directory to the path
import os
import sys

sys.path.insert(0, os.path.abspath('..'))
from naturtag import __version__

# Basic config
project = 'Naturtag'
copyright = '2020, Jordan Cook'
author = 'Jordan Cook'
version = __version__
html_static_path = ['_static']
templates_path = ['_templates']
exclude_patterns = []

# Sphinx extension modules
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
    'sphinxcontrib.apidoc',
]

intersphinx_mapping = {
    'click': ('https://click.palletsprojects.com/en/7.x/', None),
    'kivy': ('https://kivy.org/doc/stable', None),
    'kivymd': ('https://kivymd.readthedocs.io/en/latest', None),
    'pillow': ('https://pillow.readthedocs.io/en/stable', None),
    'pyinaturalist': ('https://pyinaturalist.readthedocs.io/en/latest/', None),
}
intersphinx_timeout = 30

# Use apidoc to auto-generate rst sources
apidoc_module_dir = '../naturtag'
apidoc_output_dir = 'modules'
apidoc_module_first = True
apidoc_toc_file = False

# Enable Google-style docstrings
napoleon_google_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False

# HTML theme settings
pygments_style = 'friendly'
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'collapse_navigation': True,
    'navigation_depth': 3,
    'sticky_navigation': True,
    'style_external_links': True,
}

# Favicon & sidebar logo
# html_logo = 'logo.jpg'
# html_favicon = 'favicon.ico'

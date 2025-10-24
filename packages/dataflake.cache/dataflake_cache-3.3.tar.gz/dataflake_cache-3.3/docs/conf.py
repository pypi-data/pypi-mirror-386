# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
import os
import sys
from importlib.metadata import distribution


sys.path.append(os.path.abspath('../src'))
rqmt = distribution('dataflake.cache')
year = datetime.datetime.now().year

# -- Project information -----------------------------------------------------

project = 'dataflake.cache'
copyright = '2008-%i, Jens Vagelpohl and Contributors' % year
author = 'Jens Vagelpohl'

# The short X.Y version.
version = '%s.%s' % tuple(map(int, rqmt.version.split('.')[:2]))
# The full version, including alpha/beta/rc tags.
release = rqmt.version

# -- General configuration ---------------------------------------------------

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.doctest',
              'repoze.sphinx.autointerface']
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
language = 'en'

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_static_path = ['_static']

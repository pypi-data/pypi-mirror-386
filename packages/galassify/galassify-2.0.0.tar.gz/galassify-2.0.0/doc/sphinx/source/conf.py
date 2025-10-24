# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('../../../src'))
import galassify
import get_images

from sphinx_pyproject import SphinxConfig

#from myproject import __version__ as myproject_version

version = galassify.__version__

config = SphinxConfig("../../../pyproject.toml", globalns=globals(), config_overrides = {"version": version})

#config = SphinxConfig("../../../pyproject.toml", globalns=globals())

project = "GALAssify"
copyright = "2024, " + config.author
author = config.author
release = config.version



# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage',
                'sphinx.ext.napoleon', 'sphinx.ext.autosummary',
                'myst_parser']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_context = {
  'current_version' : version,
  'versions' : [[version, f"link to {version}"], ],
  'current_language': 'en',
  'languages': [["en", "link to en"], ]
}

# -- myst_parser configuration -----------------------------------------------
myst_heading_anchors = 5
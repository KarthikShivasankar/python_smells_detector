import os
import sys

# Add the project source directory to the Python path
sys.path.insert(0, os.path.abspath('../../src'))

# Project information
project = 'Code Quality Analyzer'
copyright = '2024, Your Name'
author = 'Your Name'

# The full version, including alpha/beta/rc tags
release = '0.1'

# Extensions needed for API documentation
extensions = [
    'sphinx.ext.autodoc',  # Core extension for API documentation
    'sphinx.ext.napoleon',  # Support for Google/NumPy-style docstrings
    'sphinx.ext.viewcode',  # Add links to source code
    'sphinx.ext.intersphinx',  # Link to other project's documentation
    'sphinx_autodoc_typehints',  # Support for type hints
    'myst_parser',  # Support for Markdown files
]

# Theme settings
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autoclass_content = 'both'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Napoleon settings for docstring parsing
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# The master toctree document
master_doc = 'index'

# List of patterns to ignore when looking for source files
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use
pygments_style = 'sphinx'
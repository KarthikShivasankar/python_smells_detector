import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))



project = 'Code Quality Analyzer'
copyright = '2024, Anon'
author = 'Anon'

release = '0.1'
# ... other configurations ...

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

html_theme = 'sphinx_rtd_theme'
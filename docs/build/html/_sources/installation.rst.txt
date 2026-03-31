Installation
============

Prerequisites
-------------

Before installing Code Quality Analyzer, ensure you have:

* Python 3.8 or higher
* pip or `uv <https://docs.astral.sh/uv/>`_ package manager

Installation Methods
--------------------

Using uv (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^

`uv <https://docs.astral.sh/uv/>`_ is the recommended way to install and manage the project:

.. code-block:: bash

   git clone https://github.com/KarthikShivasankar/python_smells_detector.git
   cd python_smells_detector
   uv sync

For development (includes sphinx, pytest, and other dev tools):

.. code-block:: bash

   uv sync --extra dev

Using pip
^^^^^^^^^

.. code-block:: bash

   git clone https://github.com/KarthikShivasankar/python_smells_detector.git
   cd python_smells_detector
   pip install -e .

Development Installation
^^^^^^^^^^^^^^^^^^^^^^^^

For development, install with additional dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

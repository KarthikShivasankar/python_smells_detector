Architectural Smell Detection
=============================

The Architectural Smell Detector identifies design and architectural issues in Python projects by building a module-level dependency graph with ``networkx``.

Detected Smells
---------------

* **Hub-like Dependencies** — modules with an unusually high number of incoming and outgoing dependencies
* **Scattered Functionality** — related functionality split across too many unrelated modules
* **Redundant Abstractions** — abstractions (classes/modules) that duplicate existing functionality
* **God Objects** — modules containing an excessive number of functions or classes
* **Improper API Usage** — incorrect or unsafe use of external library APIs
* **Orphan Modules** — modules with no imports and not imported by any other module
* **Cyclic Dependencies** — circular import chains between modules
* **Unstable Dependencies** — modules that depend on less stable (more volatile) modules

Usage
-----

Command Line
^^^^^^^^^^^^

.. code-block:: bash

   analyze_code_quality /path/to/project --type architectural


API Reference
-------------

.. automodule:: code_quality_analyzer.architectural_smell_detector
   :members:
   :undoc-members:
   :show-inheritance:

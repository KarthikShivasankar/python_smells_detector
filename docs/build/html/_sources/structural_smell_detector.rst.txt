Structural Smell Detection
========================

The Structural Smell Detector identifies structural issues and complexity problems in Python code.

Detected Smells
-------------

* High Cyclomatic Complexity
* Deep Inheritance Trees
* High Coupling (CBO)
* Low Cohesion (LCOM)
* Excessive Fan-in/Fan-out
* Large File Sizes
* Complex Conditional Structures

Usage
-----

Command Line
^^^^^^^^^^^

.. code-block:: bash

   analyze_code_quality /path/to/project --type structural


API Reference
-----------

.. automodule:: code_quality_analyzer.structural_smell_detector
   :members:
   :undoc-members:
   :show-inheritance: 
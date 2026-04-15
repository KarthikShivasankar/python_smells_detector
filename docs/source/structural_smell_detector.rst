Structural Smell Detection
==========================

The Structural Smell Detector identifies structural issues and object-oriented design problems in Python code using stdlib ``ast`` and ``networkx`` graphs. It computes a suite of OO metrics and flags violations against configurable thresholds.

Detected Metrics / Smells
--------------------------

* **NOM** (Number of Methods) — classes with too many methods
* **WMPC** (Weighted Methods Per Class) — sum of cyclomatic complexities of all methods in a class
* **SIZE2** — combined count of methods and attributes per class
* **WAC** (Weighted Attribute Count) — number of attributes weighted by visibility
* **LCOM** (Lack of Cohesion in Methods) — measures how unrelated the methods of a class are to each other
* **RFC** (Response For a Class) — number of methods that can be invoked in response to a message
* **NOCC** (Number of Children Classes) — direct subclass count
* **DIT** (Depth of Inheritance Tree) — length of the longest path from the class to a root class
* **LOC** (Lines of Code) — total lines per class
* **MPC** (Message Passing Coupling) — number of method calls made to other classes
* **CBO** (Coupling Between Objects) — number of classes a class is coupled to
* **NOC** (Number of Children) — total direct and indirect subclass count
* **Cyclomatic Complexity** — decision-path count per method
* **Fan-out** — number of other modules a module depends on
* **Fan-in** — number of modules that depend on a given module
* **File Length** — files exceeding the configured line-count threshold
* **Branches** — excessive conditional branching within methods

Usage
-----

Command Line
^^^^^^^^^^^^

.. code-block:: bash

   analyze_code_quality /path/to/project --type structural


API Reference
-------------

.. automodule:: code_quality_analyzer.structural_smell_detector
   :members:
   :undoc-members:
   :show-inheritance:

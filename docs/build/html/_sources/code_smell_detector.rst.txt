Code Smell Detection
====================

The Code Smell Detector identifies common code quality issues in Python code using ``astroid`` for rich AST parsing and type inference.

Detected Smells
---------------

Per-file smells:

* **Long Methods** — methods exceeding the configured line threshold
* **Large Classes** — classes with too many methods
* **Primitive Obsession** — overuse of primitive types instead of domain objects
* **Long Parameter Lists** — methods with too many parameters
* **Data Clumps** — groups of data that always appear together
* **Switch Statements** — excessive ``if/elif`` chains that should use polymorphism
* **Temporary Fields** — instance variables only set in some code paths
* **Alternative Classes with Different Interfaces** — classes doing similar things with different method names
* **Divergent Change** — a class that changes for many different reasons
* **Parallel Inheritance Hierarchies** — mirrored class hierarchies that change together
* **Shotgun Surgery** — a change that forces many small edits across many classes
* **Comments** — excessive or misleading inline comments masking bad code
* **Duplicate Code** — repeated code blocks that should be extracted
* **Data Class** — classes that only hold data with no behaviour
* **Dead Code** — unreachable or unused code
* **Lazy Class** — classes that do too little to justify their existence
* **Speculative Generality** — over-engineering for hypothetical future use
* **Feature Envy** — methods that use another class's data more than their own
* **Inappropriate Intimacy** — classes that access each other's private members
* **Message Chains** — long chains of method calls (``a.b().c().d()``)
* **Middle Man** — classes that only delegate to another class

Cross-file smells (detected after all files are processed):

* **Alternative Classes** — similar classes across files with different interfaces
* **Data Clumps** — repeated parameter groups across files
* **Duplicate Code** — duplicate blocks across files
* **Inappropriate Intimacy** — cross-file private member access
* **Parallel Inheritance** — mirrored hierarchies across modules

Usage
-----

Command Line
^^^^^^^^^^^^

.. code-block:: bash

   analyze_code_quality /path/to/project --type code

API Reference
-------------

.. automodule:: code_quality_analyzer.code_smell_detector
   :members:
   :undoc-members:
   :show-inheritance:

Code Smell Detection
==================

The Code Smell Detector identifies common code quality issues in Python code.

Detected Smells
-------------

* Long Methods
* Large Classes
* Primitive Obsession
* Long Parameter Lists
* Data Clumps
* Feature Envy
* Message Chains
* Middle Man Classes

Usage
-----

Command Line
^^^^^^^^^^^

.. code-block:: bash

   analyze_code_quality /path/to/project --type code


API Reference
-----------

.. automodule:: code_quality_analyzer.code_smell_detector
   :members:
   :undoc-members:
   :show-inheritance: 
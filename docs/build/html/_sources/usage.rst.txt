Usage Guide
===========

Command Line Interface
----------------------

Basic Usage
^^^^^^^^^^^

.. code-block:: bash

   analyze_code_quality /path/to/project

This will analyze all types of code smells in the specified project directory.

Analyze Specific Smell Types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To analyze only specific types of smells:

.. code-block:: bash

   # Analyze only code smells
   analyze_code_quality /path/to/project --type code

   # Analyze only architectural smells
   analyze_code_quality /path/to/project --type architectural

   # Analyze only structural smells
   analyze_code_quality /path/to/project --type structural

Additional Options
^^^^^^^^^^^^^^^^^^

Configure analysis with additional options:

.. code-block:: bash

   # Use custom configuration file
   analyze_code_quality /path/to/project --config custom_config.yaml

   # Specify output file
   analyze_code_quality /path/to/project --output report.txt

   # Enable debug logging
   analyze_code_quality /path/to/project --debug

   # Ignore specific directories (e.g. tests, docs, virtual environments)
   analyze_code_quality /path/to/project --ignore tests docs venv

   # Combine multiple options
   analyze_code_quality /path/to/project --config custom_config.yaml --output report.txt --ignore tests venv --debug

Using uv (before the entry-point is on PATH)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv run analyze_code_quality /path/to/project

Output Formats
--------------

The tool generates reports in multiple formats:

* Text report (default): Detailed human-readable analysis
* CSV report: Structured data for further processing
* Log file (``code_analysis.log``): Detailed analysis process and any errors encountered

Example Output
--------------

.. code-block:: text

    Code Quality Analysis Report
    ============================

    Structural Smells:
    -------------------
    - High Cyclomatic Complexity: Method 'process_data' has complexity of 15
      Line: 45
      File: src/processor.py
      Severity: high

    Code Smells:
    ------------
    - Large Class: Class 'DataManager' has 20 methods
    - Feature Envy: Method 'calculate_metrics' makes 5 calls to 'Statistics' class

    Architectural Smells:
    ---------------------
    - Cyclic Dependency: Detected cycle between modules: module_a -> module_b -> module_c -> module_a

    Summary:
    --------
    Total Structural Smells: 5
    Total Code Smells: 8
    Total Architectural Smells: 3

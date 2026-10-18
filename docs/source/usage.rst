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

   # Analyze a single file, report only medium and high severity findings
   analyze_code_quality src/app.py --min-severity medium

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

Machine-readable output (agents, scripts, CI)
---------------------------------------------

``--format json`` prints one JSON report to stdout (or to ``--output``) and
writes no other files. The library function returns the same report:

.. code-block:: bash

   python -m code_quality_analyzer /path/to/project --format json
   analyze_code_quality src/ --format json --min-severity medium --fail-on high

.. code-block:: python

   from code_quality_analyzer import analyze

   report = analyze("/path/to/project", types=["code"], ignore=["tests"])
   for finding in report["findings"]:
       print(finding["severity"], finding["name"], finding["file_path"], finding["line_number"])

The report has the keys ``schema_version`` (1), ``tool``, ``target``,
``summary`` (count per type, ``total`` and ``by_severity``), ``findings`` and
``errors``. Each finding has ``type``, ``name``, ``description``, ``file_path``,
``module_class``, ``line_number`` and ``severity`` (``low``, ``medium`` or
``high``); findings are sorted by file and line. ``errors`` lists files that
could not be parsed; the rest of the project is still analyzed.

Exit codes: ``0`` the analysis completed, ``1`` a finding reached
``--fail-on``, ``2`` usage error (bad arguments, missing path or config file).

Output Formats
--------------

The tool generates reports in multiple formats:

* Text report (default): Detailed human-readable analysis
* CSV report: Structured data for further processing
* JSON report (``--format json``): see above
* Log file (``code_analysis.log``, text mode only): Detailed analysis process and any errors encountered

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

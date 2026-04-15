Usage Guide
==========

Command Line Interface
--------------------

Basic Usage
^^^^^^^^^^

.. code-block:: bash

   analyze_code_quality /path/to/project

Analyze Specific Smell Types
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Analyze only code smells
   analyze_code_quality /path/to/project --type code

   # Analyze only architectural smells
   analyze_code_quality /path/to/project --type architectural

   # Analyze only structural smells
   analyze_code_quality /path/to/project --type structural

Additional Options
^^^^^^^^^^^^^^^

.. code-block:: bash

   analyze_code_quality /path/to/project \
       --config custom_config.yaml \
       --output report \
       --debug

Python API
---------

Basic Usage
^^^^^^^^^^

.. code-block:: python

   from code_quality_analyzer import CodeAnalyzer
   
   analyzer = CodeAnalyzer('/path/to/project', config_file='code_quality_config.yaml')
   results = analyzer.analyze()
   print(results)

Analyzing Specific Smells
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from code_quality_analyzer import (
       CodeSmellDetector,
       ArchitecturalSmellDetector,
       StructuralSmellDetector
   )
   
   # Analyze code smells
   code_detector = CodeSmellDetector(thresholds)
   code_detector.detect_smells('/path/to/file.py')
   
   # Analyze architectural smells
   arch_detector = ArchitecturalSmellDetector(thresholds)
   arch_detector.detect_smells('/path/to/project')
   
   # Analyze structural smells
   struct_detector = StructuralSmellDetector(thresholds)
   struct_detector.detect_smells('/path/to/project')

Output Formats
------------

The tool generates reports in multiple formats:

* Text report (default): Detailed human-readable analysis
* CSV report: Structured data for further processing
* Log file: Detailed analysis process and any errors encountered
Configuration
============

The Code Quality Analyzer uses a YAML configuration file to set thresholds for various code smells and metrics.

Configuration File
----------------

The default configuration file is ``code_quality_config.yaml``. You can specify a custom configuration file using the ``--config`` option.

Example Configuration
-------------------

.. code-block:: yaml

   code_smells:
     LONG_METHOD_LINES:
       value: 45
       explanation: "Methods longer than this many lines may be too complex"
     
     LARGE_CLASS_METHODS:
       value: 15
       explanation: "Classes with more than this many methods may have too many responsibilities"

   architectural_smells:
     GOD_OBJECT_FUNCTIONS:
       value: 20
       explanation: "Modules with more than this many functions may be trying to do too much"

   structural_smells:
     CYCLOMATIC_COMPLEXITY_THRESHOLD:
       value: 10
       explanation: "Methods with cyclomatic complexity higher than this may be too complex"

Customizing Thresholds
--------------------

You can customize any threshold by creating your own configuration file based on the default template. 
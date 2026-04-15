Usage
=====

Command Line Interface
----------------------

You can use the Code Quality Analyzer as a command-line tool:

.. code-block:: bash

   analyze_code_quality sample_project --config code_quality_config.YAML

Where `sample_project` is the directory containing the code you want to analyze, and `code_quality_config.YAML` is your configuration file.

Python API
----------

You can also use the Code Quality Analyzer as a Python library:

.. code-block:: python

   from code_quality_analyzer import CodeAnalyzer

   analyzer = CodeAnalyzer('sample_project', config_file='code_quality_config.YAML')
   results = analyzer.analyze()
   print(results)

Configuration
-------------

The Code Quality Analyzer uses a YAML configuration file to set thresholds for various code smells. You can customize these thresholds by editing the `code_quality_config.YAML` file and specifying it with the `--config` option.
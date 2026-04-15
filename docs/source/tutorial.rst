Tutorial
========

Getting Started
---------------

1. Install the Code Quality Analyzer:

   .. code-block:: bash

      pip install code-quality-analyzer

2. Create a configuration file named `code_quality_config.YAML` in your project root:

   .. code-block:: yaml

      code_smells:
        LONG_METHOD_LINES:
          value: 20
          explanation: "Methods longer than this many lines may be too complex and should be refactored."
      
      # ... add other configurations ...

3. Run the analyzer on your project:

   .. code-block:: bash

      analyze_code_quality sample_project --config code_quality_config.YAML

   Where `sample_project` is the directory containing the code you want to analyze.

4. Review the generated report for code smells and suggestions for improvement.

Advanced Usage
--------------

Custom Thresholds
^^^^^^^^^^^^^^^^^

You can customize the thresholds for code smells by editing the `code_quality_config.YAML` file. For example:

.. code-block:: yaml

   code_smells:
     LONG_METHOD_LINES:
       value: 30
       explanation: "Our project allows slightly longer methods."

Integrating with CI/CD
^^^^^^^^^^^^^^^^^^^^^^

You can integrate the Code Quality Analyzer into your CI/CD pipeline. Here's an example for GitHub Actions:

.. code-block:: yaml

   name: Code Quality Check
   on: [push, pull_request]
   jobs:
     analyze:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v2
       - name: Set up Python
         uses: actions/setup-python@v2
         with:
           python-version: '3.x'
       - name: Install dependencies
         run: |
           pip install code-quality-analyzer
       - name: Run Code Quality Analyzer
         run: |
           analyze_code_quality . --config code_quality_config.YAML
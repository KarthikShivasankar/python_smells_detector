Tutorial
========

Getting Started
---------------

1. Install the Code Quality Analyzer:

   Using uv (recommended):

   .. code-block:: bash

      git clone https://github.com/KarthikShivasankar/python_smells_detector.git
      cd python_smells_detector
      uv sync

   Using pip:

   .. code-block:: bash

      git clone https://github.com/KarthikShivasankar/python_smells_detector.git
      cd python_smells_detector
      pip install -e .

2. Create a configuration file named ``code_quality_config.yaml`` in your project root:

   .. code-block:: yaml

      code_smells:
        LONG_METHOD_LINES:
          value: 20
          explanation: "Methods longer than this many lines may be too complex and should be refactored."

      # ... add other configurations ...

3. Run the analyzer on your project:

   .. code-block:: bash

      analyze_code_quality sample_project --config code_quality_config.yaml

   Where ``sample_project`` is the directory containing the code you want to analyze.

4. Review the generated report for code smells and suggestions for improvement.

Advanced Usage
--------------

Custom Thresholds
^^^^^^^^^^^^^^^^^

You can customize the thresholds for code smells by editing the ``code_quality_config.yaml`` file. For example:

.. code-block:: yaml

   code_smells:
     LONG_METHOD_LINES:
       value: 30
       explanation: "Our project allows slightly longer methods."

Ignoring Directories
^^^^^^^^^^^^^^^^^^^^

Skip directories like tests, virtual environments, or generated code:

.. code-block:: bash

   analyze_code_quality /path/to/project --ignore tests docs venv .tox

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
       - uses: actions/checkout@v3
       - name: Set up Python
         uses: actions/setup-python@v4
         with:
           python-version: '3.x'
       - name: Install dependencies
         run: pip install code-quality-analyzer
       - name: Run Code Quality Analyzer
         run: analyze_code_quality . --config code_quality_config.yaml --ignore tests venv

Testing
=======

Running Tests
-------------

Using uv (recommended):

.. code-block:: bash

   uv sync --extra dev
   uv run pytest tests/

Using pip:

.. code-block:: bash

   pip install -e ".[dev]"
   pytest tests/

Run a specific test file or class:

.. code-block:: bash

   uv run pytest tests/test_code_smell_detector.py
   uv run pytest tests/test_code_smell_detector.py::TestFoo

Run with coverage:

.. code-block:: bash

   uv run pytest tests/ --cov=code_quality_analyzer

Test Structure
--------------

The test suite includes:

* ``test_code_smell_detector.py`` — unit tests for all per-file and cross-file code smells
* ``test_architectural_smell_detector.py`` — unit tests for architectural smell detection
* ``test_structural_smell_detector.py`` — unit tests for OO metrics and structural smells
* ``test_config_handler.py`` — tests for configuration loading and validation
* ``test_main.py`` — integration tests for the CLI and overall analysis flow

Example Tests
-------------

.. code-block:: python

   def test_detect_long_method(code_smell_detector, tmp_path):
       test_file = tmp_path / "long_method.py"
       test_file.write_text("\n".join([f"    x = {i}" for i in range(50)]))

       code_smell_detector.detect_smells(str(test_file))
       assert any("Long Method" in smell.smell_type for smell in code_smell_detector.code_smells)

   def test_detect_god_object(architectural_smell_detector, tmp_path):
       test_file = tmp_path / "god_object.py"
       test_file.write_text("\n".join([f"def func{i}(): pass" for i in range(26)]))

       architectural_smell_detector.detect_smells(str(tmp_path))
       assert any("God Object" in smell.smell_type for smell in architectural_smell_detector.architectural_smells)

Writing New Tests
-----------------

When adding new features or smell detectors, add corresponding tests. Follow the existing test structure and use the pytest fixtures defined in ``conftest.py``.

Testing
=======

Running Tests
-------------

To run the tests for the Code Quality Analyzer, follow these steps:

1. Install the development dependencies:

   .. code-block:: bash

      pip install -e .[dev]

2. Run the tests using pytest:

   .. code-block:: bash

      pytest tests/

Test Structure
--------------

The test suite includes:

1. Unit tests for individual smell detectors
2. Integration tests for the overall analysis process
3. Performance tests to ensure efficiency on large codebases

Example Tests
-------------

Here are some example tests from the project:

.. code-block:: python

   def test_detect_long_method(code_smell_detector, tmp_path):
       test_file = tmp_path / "long_method.py"
       test_file.write_text("\n".join([f"print('Line {i}')" for i in range(21)]))

       code_smell_detector.detect_smells(str(test_file))
       assert any("Long Method" in smell for smell in code_smell_detector.code_smells)

   def test_detect_god_object(architectural_smell_detector, tmp_path):
       test_file = tmp_path / "god_object.py"
       test_file.write_text("\n".join([f"def func{i}(): pass" for i in range(26)]))

       architectural_smell_detector.detect_smells(str(tmp_path))
       assert any("God Object" in smell for smell in architectural_smell_detector.architectural_smells)

Writing New Tests
-----------------

When adding new features or smell detectors, make sure to add corresponding tests. Follow the existing test structure and use pytest fixtures where appropriate.
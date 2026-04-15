# Code Quality Analyzer

This package provides advanced tools to analyze Python projects for code smells and architectural smells, offering insights into code quality and maintainability.

## Installation


```bash
pip install -e .
```

## Usage

You can use the package as a command-line tool:

```bash
analyze_code_quality sample_project --config code_quality_config.YAML --output report.txt  
```
Where sample_project is the directory containing the code you want to analyze, and code_quality_config.YAML is your configuration file.
### Python API



analyzer = CodeAnalyzer('/path/to/your/project')
results = analyzer.analyze()
print(results)
```

## Features

- Detects various code smells such as long methods, large classes, primitive obsession, etc.
- Identifies architectural smells like hub-like dependencies, scattered functionality, and more.
- Customizable thresholds for smell detection.
- Detailed reports with actionable insights.

## Metrics Calculation

### Code Smells

1. **Long Method**
   - Calculation: Count the number of lines in a method.
   - Threshold: Configurable, default is 15 lines.

2. **Large Class**
   - Calculation: Count the number of methods in a class.
   - Threshold: Configurable, default is 10 methods.

3. **Primitive Obsession**
   - Calculation: Count the number of primitive type parameters in a method.
   - Threshold: Configurable, default is 3 primitive parameters.

4. **Long Parameter List**
   - Calculation: Count the number of parameters in a method.
   - Threshold: Configurable, default is 5 parameters.

5. **Data Clumps**
   - Calculation: Identify groups of parameters that frequently appear together in multiple functions.
   - Threshold: Groups of 3 or more parameters appearing in multiple functions.

6. **Switch Statements**
   - Calculation: Count the number of elif statements in an if-else chain.
   - Threshold: Configurable, default is more than 2 elif statements.

7. **Temporary Field**
   - Calculation: Identify class fields that are only used in certain methods.
   - Detection: Fields initialized in __init__ but not used in all methods.

8. **Refused Bequest**
   - Calculation: Identify subclasses that use less than half of their parent's methods.
   - Threshold: Using less than 50% of inherited methods.

9. **Alternative Classes with Different Interfaces**
   - Calculation: Identify classes with similar methods but different interfaces.
   - Detection: Classes with similar method sets.

10. **Divergent Change**
    - Calculation: Count distinct method name prefixes in a class.
    - Threshold: Configurable, default is more than 5 distinct prefixes.

11. **Shotgun Surgery**
    - Calculation: Count the number of places a method is called.
    - Threshold: Configurable, default is called in more than 5 places.

12. **Feature Envy**
    - Calculation: Count method calls to another object's properties/methods.
    - Threshold: Configurable, default is more than 3 calls to another object.

13. **Data Class**
    - Calculation: Identify classes with only getters, setters, and fields.
    - Detection: Classes with no methods other than getters/setters.

14. **Lazy Class**
    - Calculation: Count the number of methods in a class.
    - Threshold: Configurable, default is 2 or fewer methods.

15. **Message Chains**
    - Calculation: Count the length of method call chains (e.g., a.b().c().d()).
    - Threshold: Configurable, default is chains longer than 3 calls.

16. **Middle Man**
    - Calculation: Identify classes where more than half of the methods delegate to another class.
    - Threshold: Over 50% of methods simply delegating to another class.

### Architectural Smells

1. **Hub-like Dependency**
   - Calculation: Analyze the number of incoming and outgoing dependencies for each module.
   - Threshold: Modules with dependencies > 50% of total modules.

2. **Scattered Functionality**
   - Calculation: Identify functions with similar names spread across multiple modules.
   - Detection: Functions with the same name appearing in multiple modules.

3. **Redundant Abstractions**
   - Calculation: Identify modules with very similar sets of functions.
   - Detection: Modules with nearly identical function signatures.

4. **God Objects**
   - Calculation: Count the number of functions in a module.
   - Threshold: Modules with more than 20 functions (configurable).

5. **Improper API Usage**
   - Calculation: Analyze repetitive API calls within a module.
   - Detection: Modules with many repeated API calls.

6. **Orphan Modules**
   - Calculation: Identify modules with no incoming or outgoing dependencies.
   - Detection: Modules completely isolated in the dependency graph.

7. **Cyclic Dependencies**
   - Calculation: Detect cycles in the module dependency graph.
   - Detection: Any circular dependencies between modules.

8. **Unstable Dependencies**
   - Calculation: Analyze the ratio of incoming to outgoing dependencies for each module.
   - Threshold: Modules with instability > 0.7 (configurable).

### Structural Smells

1. **High Number of Methods (NOM)**
   - Calculation: Count the number of methods in a class.
   - Threshold: Configurable, default is 5 methods.

2. **Weighted Methods per Class (WMC)**
   - Calculation: Sum of cyclomatic complexities of all methods in a class.
   - Threshold: Configurable, default is 10.

3. **Class Size (SIZE2)**
   - Calculation: Sum of the number of methods and number of attributes in a class.
   - Threshold: Configurable, default is 10.

4. **Weighted Attribute Count (WAC)**
   - Calculation: Count the number of attributes in a class.
   - Threshold: Configurable, default is 5.

5. **Lack of Cohesion in Methods (LCOM)**
   - Calculation: Number of method pairs not sharing instance variables minus number of method pairs sharing instance variables.
   - Threshold: Configurable, default is 5.

6. **Response for Class (RFC)**
   - Calculation: Number of methods in the class plus number of unique method calls made by the class.
   - Threshold: Configurable, default is 10.

7. **Number of Children (NOC)**
   - Calculation: Count the number of immediate subclasses of a class.
   - Threshold: Configurable, default is 5.

8. **Depth of Inheritance Tree (DIT)**
   - Calculation: Maximum length from the class to the root of the inheritance tree.
   - Threshold: Configurable, default is 3.

9. **Lines of Code (LOC)**
   - Calculation: Count the number of lines of code in a module.
   - Threshold: Configurable, default is 50.

10. **Message Passing Coupling (MPC)**
    - Calculation: Number of method calls to other classes.
    - Threshold: Configurable, default is 10.

11. **Coupling Between Object Classes (CBO)**
    - Calculation: Number of other classes a class is directly coupled to.
    - Threshold: Configurable, default is 5.

12. **Number of Classes (NOC)**
    - Calculation: Total number of classes in the project.
    - Threshold: Configurable, default is 10.

These structural metrics provide insights into the complexity, coupling, and cohesion of classes and modules in a Python project. They can help identify areas that may need refactoring or redesign to improve maintainability and reduce technical debt.

## Advantages over Other Frameworks

1. **Customizable Thresholds**: Unlike many static analysis tools, our analyzer allows users to set custom thresholds for each smell, adapting to project-specific needs.

2. **Architectural Analysis**: While many tools focus on code-level smells, we also provide insights into architectural issues, offering a more comprehensive view of code quality.

3. **Performance**: Our tool is optimized for large codebases, using efficient algorithms to analyze code quickly without compromising on accuracy.

4. **Integration**: Easy integration with CI/CD pipelines and popular IDEs, making it simple to incorporate into existing workflows.

5. **Detailed Reports**: Generate comprehensive reports with visualizations, making it easier to understand and act on the analysis results.

## Testing

We use pytest for automated testing. To run the tests:

1. Install the development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run the tests:
   ```bash
   pytest tests/
   ```

### Test Structure

Our test suite includes:

1. Unit tests for individual smell detectors
2. Integration tests for the overall analysis process
3. Performance tests to ensure efficiency on large codebases

Example test for the Long Method detector:

```python
def test_long_method_detector():
    code = """
    def long_method():
        # ... 60 lines of code ...
    """
    detector = LongMethodDetector(threshold=50)
    result = detector.analyze(code)
    assert result['is_smell'] == True
    assert result['lines'] == 60
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Documentation

To build the documentation:

1. Install the development dependencies:
   ```bash
   pip install -e .[dev]
   ```

2. Navigate to the `docs` directory:
   ```bash
   cd docs
   ```

3. Build the documentation:
   ```bash
   make html
   ```

4. Open `docs/build/html/index.html` in your web browser to view the documentation.


4. Change to the `docs` directory:

   .. code-block:: console

      cd docs

5. Run the Sphinx build command:

   .. code-block:: console

      sphinx-build -b html source build/html

This will generate the HTML documentation in the `docs/build/html` directory. You can open the `index.html` file in this directory to view the updated documentation.

# Code Quality Analyzer

A comprehensive Python code quality analysis tool that detects code smells, architectural smells, and structural issues in Python projects. This tool helps developers identify potential maintainability issues and technical debt early in the development process.

## Features

### Code Smell Detection
- Long methods and large classes
- Primitive obsession and data clumps
- Feature envy and inappropriate intimacy
- Message chains and middle man classes
- Duplicate code and speculative generality
- Temporary fields and lazy classes
- Switch statements and cyclic dependencies

### Architectural Smell Detection
- Hub-like dependencies
- Scattered functionality
- Cyclic dependencies
- God objects
- Unstable dependencies
- Improper API usage
- Redundant abstractions

### Structural Smell Detection
- High cyclomatic complexity
- Deep inheritance trees
- High coupling (CBO)
- Low cohesion (LCOM)
- Excessive fan-in/fan-out
- Large file sizes
- Complex conditional structures

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install from source
```bash
git clone https://github.com/yourusername/code-quality-analyzer.git
cd code-quality-analyzer
pip install -e .
```

## Usage

### Command Line Interface

Basic usage:
```bash
analyze_code_quality /path/to/project --config code_quality_config.yaml
```

Analyze specific smell types:
```bash
# Analyze only code smells
analyze_code_quality /path/to/project --type code

# Analyze only architectural smells
analyze_code_quality /path/to/project --type architectural

# Analyze only structural smells
analyze_code_quality /path/to/project --type structural
```

Additional options:
```bash
analyze_code_quality /path/to/project \
    --config custom_config.yaml \
    --output report \
    --debug
```

### Configuration

The tool uses a YAML configuration file to set thresholds for various metrics. You can customize these thresholds by creating your own configuration file based on the provided template:

```yaml
code_smells:
  LONG_METHOD_LINES:
    value: 45
    explanation: "Methods longer than this many lines may be too complex"
  LARGE_CLASS_METHODS:
    value: 15
    explanation: "Classes with more than this many methods may have too many responsibilities"
  # ... other thresholds
```

### Output Formats

The tool generates reports in multiple formats:

- Text report (default): Detailed human-readable analysis
- CSV report: Structured data for further processing
- Log file: Detailed analysis process and any errors encountered

## Example Output

```text
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
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Run tests:
   ```bash
   pytest tests/
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on Martin Fowler's work on code smells and refactoring
- Inspired by various software quality metrics and best practices
- Uses abstract syntax tree analysis for Python code

## Troubleshooting

### Common Issues

1. **ParseError in Python Files**
   - Ensure the Python files being analyzed are valid Python syntax
   - Check file encoding (tool supports utf-8, utf-8-sig, latin1, cp1252)

2. **Missing Dependencies**
   - Ensure all required packages are installed:
     ```bash
     pip install -r requirements.txt
     ```

### Debug Mode

Enable debug mode for detailed logging:
```bash
analyze_code_quality /path/to/project --debug
```

## Support

For bug reports and feature requests, please use the GitHub issue tracker.

## Documentation

The documentation is built using Sphinx and hosted on Read the Docs.

### Building the Documentation Locally

1. Install the documentation requirements:
```bash
pip install -r docs/requirements.txt
```

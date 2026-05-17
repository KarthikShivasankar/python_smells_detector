# Code Quality Analyzer (PyExamine)

A comprehensive Python static analysis tool that detects **code smells**, **architectural smells**, and **structural smells** in Python projects. Helps developers identify maintainability issues and technical debt before they compound.

---

## Table of Contents

- [Features](#features)
- [Use Cases](#use-cases)
- [Requirements](#requirements)
- [Installation](#installation)
  - [From PyPI with uv (recommended)](#from-pypi-with-uv-recommended)
  - [From PyPI with pip](#from-pypi-with-pip)
  - [From source with uv](#from-source-with-uv)
  - [From source with pip](#from-source-with-pip)
- [Usage](#usage)
  - [Basic analysis](#basic-analysis)
  - [Analyze a specific category](#analyze-a-specific-category)
  - [Ignore folders](#ignore-folders)
  - [Save a report](#save-a-report)
  - [Full example](#full-example)
  - [CLI reference](#cli-reference)
- [Ways to Run](#ways-to-run)
  - [As a CLI command](#as-a-cli-command)
  - [As a Python module](#as-a-python-module)
  - [Python API](#python-api)
  - [Pre-commit hook](#pre-commit-hook)
  - [GitHub Actions](#github-actions)
  - [GitLab CI](#gitlab-ci)
- [Configuration](#configuration)
  - [Code smell thresholds](#code-smell-thresholds)
  - [Architectural smell thresholds](#architectural-smell-thresholds)
  - [Structural smell thresholds](#structural-smell-thresholds)
- [Output formats](#output-formats)
- [Example output](#example-output)
- [Development](#development)
  - [Setup](#setup)
  - [Running tests](#running-tests)
  - [Linting](#linting)
  - [Building docs](#building-docs)
  - [Building and publishing to PyPI](#building-and-publishing-to-pypi)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)
- [Citation](#citation)
- [Acknowledgments](#acknowledgments)

---

## Features

### Code Smells — 18 detectors + 5 cross-file detectors

| Smell | What it flags |
|-------|--------------|
| Long Method | Methods exceeding a line count threshold |
| Large Class | Classes with too many methods |
| Primitive Obsession | Functions overusing primitive types instead of objects |
| Long Parameter List | Functions with too many parameters |
| Switch Statements | Long if/elif chains that should be polymorphism |
| Divergent Change | Classes that change for many different reasons |
| Shotgun Surgery | Methods called across too many unrelated contexts |
| Excessive Comments | Files where comment density is unusually high |
| Lazy Class | Classes too small to justify their existence |
| Feature Envy | Methods that access another object's data more than their own |
| Message Chains | Long chains of method calls (Law of Demeter violations) |
| Middle Man | Classes that mostly delegate to another class |
| Speculative Generality | Abstract classes or unused hooks added "just in case" |
| Temporary Field | Instance fields set only in some code paths |
| Dead Code | Functions defined but never called |
| Unused Parameters | Method signatures more complex than the implementation needs |
| Data Class | Classes with only fields and no real behaviour |
| Large Comment Blocks | Oversized comment blocks suggesting code that needs refactoring |
| *(cross-file)* Data Clumps | Parameter groups that appear together across many functions |
| *(cross-file)* Duplicate Code | Identical or near-identical code blocks across files |
| *(cross-file)* Inappropriate Intimacy | Pairs of classes that share too many internals |
| *(cross-file)* Alternative Classes | Classes with identical public interfaces but different names |
| *(cross-file)* Parallel Inheritance | Parallel class hierarchies that change together |

### Architectural Smells — 8 detectors

| Smell | What it flags |
|-------|--------------|
| God Object | Modules with an excessive number of public functions |
| Cyclic Dependency | Circular import chains between modules |
| Hub-like Dependency | Modules that are overly central (high fan-in + fan-out) |
| Scattered Functionality | The same function name repeated across many modules |
| Unstable Dependency | Modules that depend far more on others than others depend on them |
| Orphan Module | Modules with no connections to the rest of the project |
| Improper API Usage | Modules that repeat the same API call patterns excessively |
| Redundant Abstractions | Module pairs with nearly identical public function sets |

### Structural Smells — 12 metric-based detectors

| Smell | Metric | What it flags |
|-------|--------|--------------|
| Too Many Methods | NOM | Classes with more methods than the threshold |
| Low Cohesion | LCOM | Classes whose methods don't share fields |
| High Response | RFC | Classes that trigger too many responses to a message |
| Too Many Classes in Module | NOCC | Modules with an excessive number of classes |
| Deep Inheritance | DIT | Classes with deep inheritance chains |
| Large Module | LOC | Modules exceeding a line count |
| Too Many Classes in Project | NOC | Projects with an excessive class count |
| High Cyclomatic Complexity | CC | Methods with too many decision branches |
| High Fan-out | Fan-out | Modules depending on too many others |
| High Fan-in | Fan-in | Modules depended upon by too many others |
| Large File | File length | Files exceeding a line count |
| Too Many Branches | Branches | Methods with too many conditional branches |

---

## Use Cases

### Auditing a legacy codebase

Before refactoring a large project, get a full picture of its technical debt:

```bash
analyze_code_quality /path/to/legacy_project \
    --output reports/initial_audit \
    --ignore venv .tox build dist
```

Open `reports/initial_audit.csv` in Excel or a BI tool to sort smells by severity and prioritize which modules to tackle first.

### Enforcing quality gates in CI

Fail a pull request if new smells are introduced. Add the tool to your CI pipeline (see [GitHub Actions](#github-actions) and [GitLab CI](#gitlab-ci) below) and compare reports between the base and head commits.

### Focused structural review

When reviewing a new service or library for object-oriented design issues, run only the structural detector to get OO metric violations (LCOM, CBO, DIT, cyclomatic complexity) without noise from the other categories:

```bash
analyze_code_quality src/my_service --type structural --output oo_review
```

### Tracking technical debt over time

Run the tool on every merge to `main`, save the CSV to a time-series store or artifact, and chart smell counts per category over sprints to measure whether debt is being paid down.

### Pre-merge code review assistance

Developers run the tool locally before opening a PR:

```bash
analyze_code_quality . --ignore tests docs venv --type code
```

This surfaces code smells (long methods, large classes, dead code, etc.) in the diff before reviewers see it.

### Onboarding onto an unfamiliar codebase

Run all three detectors and read the architectural smells report first — cyclic dependencies, god objects, and hub-like modules give a high-level map of the system's problem areas before diving into individual files.

---

## Requirements

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

---

## Installation

### From PyPI with uv (recommended)

Install [uv](https://docs.astral.sh/uv/) first if you haven't:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install the tool globally:

```bash
uv tool install code-quality-analyzer
```

The `analyze_code_quality` command is now available everywhere. Make sure `~/.local/bin` (Linux/macOS) or `%USERPROFILE%\.local\bin` (Windows) is on your `PATH`.

### From PyPI with pip

```bash
pip install code-quality-analyzer
```

### From source with uv

```bash
git clone https://github.com/KarthikShivasankar/python_smells_detector
cd python_smells_detector
uv sync
```

Run the tool without installing it globally:

```bash
uv run analyze_code_quality /path/to/project
```

### From source with pip

```bash
git clone https://github.com/KarthikShivasankar/python_smells_detector
cd python_smells_detector
pip install -e .
analyze_code_quality /path/to/project
```

---

## Usage

### Basic analysis

Analyze all three smell categories in a project:

```bash
analyze_code_quality /path/to/project
```

### Analyze a specific category

```bash
analyze_code_quality /path/to/project --type code
analyze_code_quality /path/to/project --type architectural
analyze_code_quality /path/to/project --type structural
```

### Ignore folders

Skip directories you don't want analyzed — useful for vendored code, test fixtures, virtual environments, or build output:

```bash
analyze_code_quality /path/to/project --ignore tests docs venv build
```

Multiple names are space-separated. The names are matched against directory basenames (not full paths), so `--ignore tests` skips any folder named `tests` anywhere in the tree.

### Save a report

By default the report is printed to stdout. Use `--output` to write files instead:

```bash
# Creates report.txt (human-readable) and report.csv (structured)
analyze_code_quality /path/to/project --output report
```

The `.txt` and `.csv` suffixes are added automatically — just provide the base name.

### Full example

```bash
analyze_code_quality /path/to/project \
    --type code \
    --config my_thresholds.yaml \
    --output results/analysis \
    --ignore tests docs venv __pycache__ \
    --debug
```

### CLI reference

| Argument | Type | Description | Default |
|----------|------|-------------|---------|
| `directory` | positional | Path to the project directory to analyze | *(required)* |
| `--type` | option | Limit analysis to `code`, `architectural`, or `structural` | all three |
| `--config` | option | Path to a YAML threshold configuration file | `code_quality_config.yaml` |
| `--output` | option | Base name for output files — generates `<name>.txt` + `<name>.csv` | print to stdout |
| `--ignore` | option (repeatable) | Directory names to skip during traversal | none |
| `--debug` | flag | Enable verbose debug logging to console and `code_analysis.log` | off |

---

## Ways to Run

### As a CLI command

The primary interface. Works after `pip install code-quality-analyzer` or `uv tool install code-quality-analyzer`:

```bash
analyze_code_quality /path/to/project
analyze_code_quality /path/to/project --type structural --output report
```

### As a Python module

If the entry point is not on your `PATH` (e.g., after `uv sync` from source), invoke the module directly:

```bash
python -m code_quality_analyzer.main /path/to/project
# or via uv
uv run python -m code_quality_analyzer.main /path/to/project
```

### Python API

Use the detectors programmatically inside your own scripts or tooling:

```python
from code_quality_analyzer.config_handler import ConfigHandler
from code_quality_analyzer.code_smell_detector import CodeSmellDetector
from code_quality_analyzer.structural_smell_detector import StructuralSmellDetector
from code_quality_analyzer.architectural_smell_detector import ArchitecturalSmellDetector
from code_quality_analyzer.main import (
    analyze_code_smells,
    analyze_structural_smells,
    analyze_architectural_smells,
    generate_report,
)

config = ConfigHandler("code_quality_config.yaml")

# Run only code smell detection
code_detector = CodeSmellDetector(config.get_thresholds("code_smells"))
code_smells = analyze_code_smells("src/", code_detector, ignore_dirs={"tests", "venv"})

# Run structural detection
struct_detector = StructuralSmellDetector(config.get_thresholds("structural_smells"))
structural_smells = analyze_structural_smells("src/", struct_detector)

# Run architectural detection
arch_detector = ArchitecturalSmellDetector(config.get_thresholds("architectural_smells"))
architectural_smells = analyze_architectural_smells("src/", arch_detector)

# Generate text + CSV reports
generate_report(code_smells, architectural_smells, structural_smells,
                output_txt="report.txt", output_csv="report.csv")

# Or just inspect the results in code
for smell in code_smells:
    print(smell.name, smell.file_path, smell.severity)
```

Each `smell` object is a dataclass with fields: `name`, `description`, `file_path`, `module_class`, `line_number`, `severity`.

### Pre-commit hook

Run the analyzer automatically before every commit. Add this to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: code-quality-analyzer
        name: Code Quality Analyzer
        entry: analyze_code_quality
        args: ['.', '--type', 'code', '--ignore', 'tests', 'venv', 'build']
        language: system
        pass_filenames: false
```

Install the hooks:

```bash
pip install pre-commit
pre-commit install
```

### GitHub Actions

Add this workflow to `.github/workflows/code-quality.yml` to analyze every pull request:

```yaml
name: Code Quality Analysis

on:
  pull_request:
    branches: [main, dev]
  push:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: pip install uv

      - name: Install code-quality-analyzer
        run: uv tool install code-quality-analyzer

      - name: Run analysis
        run: |
          analyze_code_quality src/ \
            --output reports/quality \
            --ignore tests venv build dist \
            --type code

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: code-quality-report
          path: reports/
```

### GitLab CI

Add to `.gitlab-ci.yml`:

```yaml
code-quality:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install uv
    - uv tool install code-quality-analyzer
  script:
    - analyze_code_quality src/
        --output reports/quality
        --ignore tests venv build
  artifacts:
    paths:
      - reports/
    expire_in: 7 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

---

## Configuration

All detection thresholds are defined in `code_quality_config.yaml`. The tool looks for this file in the current working directory by default; use `--config` to point to a different file.

Copy the file and edit the `value` fields to tune sensitivity for your project:

```bash
cp code_quality_config.yaml my_project_thresholds.yaml
# edit my_project_thresholds.yaml
analyze_code_quality /path/to/project --config my_project_thresholds.yaml
```

### Code smell thresholds

| Key | Default | Description |
|-----|---------|-------------|
| `LONG_METHOD_LINES` | `45` | Methods longer than this many lines are flagged |
| `LARGE_CLASS_METHODS` | `15` | Classes with more than this many methods are flagged |
| `PRIMITIVE_OBSESSION_COUNT` | `4` | Functions with more than this many primitive parameters are flagged |
| `LONG_PARAMETER_LIST` | `5` | Functions with more parameters than this are flagged |
| `COMPLEX_CONDITIONAL` | `3` | if/elif chains longer than this trigger a switch-statement smell |
| `DIVERGENT_CHANGE_PREFIXES` | `4` | Classes with more distinct method-name prefixes than this are flagged |
| `DIVERGENT_CHANGE_METHODS` | `5` | Classes with more methods changing for different reasons than this are flagged |
| `SHOTGUN_SURGERY_CALLS` | `5` | Methods called in more places than this are flagged |
| `SHOTGUN_SURGERY_CONTEXTS` | `3` | Methods called in more different contexts than this are flagged |
| `EXCESSIVE_COMMENTS_RATIO` | `0.3` | Files where comment lines exceed this fraction of total lines are flagged |
| `LARGE_COMMENT_BLOCKS` | `5` | Consecutive comment blocks larger than this are flagged |
| `LAZY_CLASS_METHODS` | `4` | Classes with this few methods or fewer are flagged as lazy |
| `FEATURE_ENVY_CALLS` | `3` | Methods making more calls to another object than this are flagged |
| `INAPPROPRIATE_INTIMACY_SHARED` | `3` | Class pairs sharing more internals than this are flagged |
| `MESSAGE_CHAIN_LENGTH` | `3` | Call chains longer than this are flagged |
| `MIDDLE_MAN_RATIO` | `0.5` | Classes where more than this fraction of methods only delegate are flagged |
| `DATA_CLUMPS_THRESHOLD` | `6` | Parameter groups appearing together more than this many times are flagged |
| `TEMPORARY_FIELD_THRESHOLD` | `3` | Fields used in fewer methods than this are flagged as temporary |
| `ALTERNATIVE_CLASSES_THRESHOLD` | `3` | Classes with more shared methods than this are checked for identical interfaces |
| `DUPLICATE_CODE_THRESHOLD` | `15` | Functions with more shared lines than this are flagged as duplicates |
| `DUPLICATE_CODE_MIN_LINES` | `5` | Minimum block length (lines) to consider when detecting duplicate code |
| `DEAD_CODE_THRESHOLD` | `3` | Functions not called more than this many times are flagged as dead code |
| `SPECULATIVE_GENERALITY_THRESHOLD` | `4` | Abstract classes with fewer concrete subclasses than this are flagged |
| `UNUSED_PARAMETERS_THRESHOLD` | `6` | Accumulation of unused parameters across methods above this is flagged |

### Architectural smell thresholds

| Key | Default | Description |
|-----|---------|-------------|
| `GOD_OBJECT_FUNCTIONS` | `20` | Modules with more public functions than this are flagged as god objects |
| `UNSTABLE_DEPENDENCY_THRESHOLD` | `0.8` | Modules with instability (out / total) above this ratio are flagged |
| `HUB_LIKE_DEPENDENCY_RATIO` | `0.3` | Modules connected to more than this fraction of all modules are flagged as hubs |
| `REDUNDANT_ABSTRACTION_SIMILARITY` | `0.7` | Module pairs sharing more than this fraction of functions are flagged as redundant |
| `IMPROPER_API_USAGE_RATIO` | `0.7` | Modules where repetitive API calls exceed this fraction of total calls are flagged |
| `CYCLIC_DEPENDENCY_MAX_LENGTH` | `3` | Cyclic dependency chains longer than this are flagged |

### Structural smell thresholds

| Key | Default | Metric | Description |
|-----|---------|--------|-------------|
| `NOM_THRESHOLD` | `10` | NOM | Classes with more methods than this are flagged |
| `WMPC1_THRESHOLD` | `20` | WMPC1 | Weighted Methods per Class (complexity-based) above this |
| `WMPC2_THRESHOLD` | `20` | WMPC2 | Weighted Methods per Class (parameter-based) above this |
| `SIZE2_THRESHOLD` | `15` | SIZE2 | Classes with more total members (methods + fields) than this |
| `WAC_THRESHOLD` | `10` | WAC | Classes with more fields than this are flagged |
| `LCOM_THRESHOLD` | `10` | LCOM | Lack of Cohesion in Methods above this threshold |
| `RFC_THRESHOLD` | `20` | RFC | Response for a Class above this threshold |
| `NOCC_THRESHOLD` | `10` | NOCC | Modules with more classes than this are flagged |
| `DIT_THRESHOLD` | `3` | DIT | Classes with inheritance depth greater than this are flagged |
| `LOC_THRESHOLD` | `150` | LOC | Modules with more lines than this are flagged |
| `MPC_THRESHOLD` | `25` | MPC | Message Passing Coupling above this threshold |
| `CBO_THRESHOLD` | `5` | CBO | Coupling Between Object classes above this threshold |
| `NOC_THRESHOLD` | `7` | NOC | Projects with more distinct classes than this are flagged |
| `CYCLOMATIC_COMPLEXITY_THRESHOLD` | `10` | CC | Methods with cyclomatic complexity above this are flagged |
| `MAX_FANOUT` | `15` | Fan-out | Modules depending on more than this many others are flagged |
| `MAX_FANIN` | `15` | Fan-in | Modules depended upon by more than this many others are flagged |
| `MAX_FILE_LENGTH` | `250` | — | Files with more lines than this are flagged |
| `MAX_BRANCHES` | `10` | — | Methods with more conditional branches than this are flagged |
| `MAX_NESTING_DEPTH` | `4` | — | Code nested deeper than this is flagged |

---

## Output formats

The tool produces three output types:

| Format | How to get it | Contents |
|--------|--------------|----------|
| **Console** | Default (no `--output`) | Human-readable report printed to stdout |
| **Text file** (`*.txt`) | `--output <name>` | Same human-readable report, saved to `<name>.txt` |
| **CSV file** (`*.csv`) | `--output <name>` | One row per smell: Type, Name, Description, File, Module/Class, Line Number, Severity |
| **Log file** (`code_analysis.log`) | Always written | Detailed analysis trace, warnings, and parse errors |

The CSV is useful for importing into spreadsheets, dashboards, or CI tools for trend tracking.

---

## Example output

```
Code Quality Analysis Report
============================

Structural Smells:
-------------------
- High Cyclomatic Complexity: Method 'process_data' has complexity of 15
  Line: 45
  File: src/processor.py
  Severity: high

- Large Module (LOC): Module 'data_manager' has 320 lines
  File: src/data_manager.py
  Severity: medium

Code Smells:
------------
- Large Class: 'DataManager' has 22 non-trivial methods in src/data_manager.py at line 10
- Long Method: 'DataManager.transform' has 68 lines in src/data_manager.py at line 145
- Feature Envy: Method 'calculate_metrics' makes 8 calls to 'stats' but only 1 local call
- Data Clumps: Parameters user_id, user_name, user_email appear together in 7 functions

Architectural Smells:
---------------------
- Cyclic Dependency: Strong cyclic dependency detected: loader -> parser -> loader
  Cycle strength: 3 mutual dependencies
- God Object: Module 'utils' has too many public functions (27)

Summary:
--------
Total Structural Smells: 2
Total Code Smells: 4
Total Architectural Smells: 2
```

---

## Development

### Setup

```bash
git clone https://github.com/KarthikShivasankar/code_quality_analyzer
cd code_quality_analyzer

# Install runtime + dev dependencies (pytest, sphinx, etc.)
uv sync --extra dev
```

### Running tests

The test suite covers all three detectors (code, structural, architectural), the config handler, and the main orchestration layer. Tests write real Python source files into temporary directories — no mocking.

```bash
# Install dev dependencies first (includes pytest)
uv sync --extra dev

# Run the full test suite (123 tests)
uv run python -m pytest tests/

# Run a specific test file
uv run python -m pytest tests/test_code_smell_detector.py
uv run python -m pytest tests/test_structural_smell_detector.py
uv run python -m pytest tests/test_architectural_smell_detector.py
uv run python -m pytest tests/test_config_handler.py
uv run python -m pytest tests/test_main.py

# Run a single test class
uv run python -m pytest tests/test_code_smell_detector.py::TestLargeClass
uv run python -m pytest tests/test_structural_smell_detector.py::TestLOC

# Run a single test by name
uv run python -m pytest tests/test_code_smell_detector.py::TestLongMethod::test_detects_method_over_threshold

# Run with verbose output
uv run python -m pytest tests/ -v

# Run with coverage report
uv run python -m pytest tests/ --cov=src/code_quality_analyzer --cov-report=term-missing

# Verify all 123 tests pass (exit 0 = success)
uv run python -m pytest tests/ -q && echo "All tests passed"
```

#### Test structure

| File | What it covers |
|------|---------------|
| `tests/test_code_smell_detector.py` | 18 per-file detectors + cross-file smells (data clumps, duplicate code, alternative classes, parallel inheritance). Positive and negative cases for each. |
| `tests/test_structural_smell_detector.py` | 12 metric-based detectors: NOM, LOC, NOC, NOCC, DIT, LCOM, RFC, WAC, SIZE2, cyclomatic complexity, fan-in/out, branches, file length. |
| `tests/test_architectural_smell_detector.py` | All 8 architectural smell detectors: God Object, Scattered Functionality, Redundant Abstraction, Improper API Usage, Orphan Module, Cyclic Dependency, Unstable Dependency, Hub-like Dependency. |
| `tests/test_config_handler.py` | Config file loading, threshold validation, unknown-key handling, malformed YAML error handling. |
| `tests/test_main.py` | CLI parser flags, `analyze_*` functions, `generate_report`, `generate_csv_report` (field names, row contents, empty input). |

> **Note:** `pytest` is blocked by an application control policy on some Windows setups — use `python -m pytest` instead of the bare `pytest` command.

### Linting

```bash
uv run flake8 src/ --max-line-length=100
```

### Building docs

```bash
# Build HTML docs with Sphinx
uv run sphinx-build docs/source docs/build/html

# Windows legacy script
cd docs && make.bat html
```

### Building and publishing to PyPI

```bash
# 1. Build the wheel and source distribution
uv build
# → creates dist/code_quality_analyzer-0.2.0-py3-none-any.whl
# → creates dist/code_quality_analyzer-0.2.0.tar.gz

# 2a. Test on TestPyPI first (optional but recommended)
uv publish --index https://test.pypi.org/simple/

# 2b. Publish to PyPI
uv publish
```

**Authentication:** create an API token at [pypi.org → Account Settings → API tokens](https://pypi.org/manage/account/#api-tokens), then:

```bash
# Set once in your shell profile to avoid being prompted every time
export UV_PUBLISH_TOKEN=pypi-xxxxxxxxxxxx   # Linux / macOS
$env:UV_PUBLISH_TOKEN="pypi-xxxxxxxxxxxx"   # Windows PowerShell
```

Or pass it inline:

```bash
UV_PUBLISH_TOKEN=pypi-xxxx uv publish
```

---

## Troubleshooting

**`analyze_code_quality: command not found`**
- Installed via `uv tool install` → make sure `~/.local/bin` (Linux/macOS) or `%USERPROFILE%\.local\bin` (Windows) is on your `PATH`
- Installed via `uv sync` (source) → use `uv run analyze_code_quality ...` instead of invoking the script directly
- Installed via `pip install -e .` → make sure the pip scripts directory is on your `PATH`

**Parse errors / files being skipped**
- Ensure files being analyzed are valid Python 3 syntax
- Files with syntax errors are skipped and logged — check `code_analysis.log` for details
- The analysis continues for all other files

**`KeyError` or missing threshold**
- Your config file is missing a required key — use the bundled `code_quality_config.yaml` as a base and add missing keys

**Analysis is slow on large projects**
- Use `--type code` / `--type architectural` / `--type structural` to run one category at a time
- Use `--ignore` to skip large directories that don't need analysis (e.g., `venv`, `node_modules`, `build`)
- The `networkx` graph construction in the architectural and structural detectors is the main performance cost on large trees

**No smells detected**
- The thresholds in your config may be too high for the project being analyzed
- Try lowering key values in `code_quality_config.yaml` and re-running
- Use `--debug` to see per-file analysis trace

---

## Architecture

```
src/code_quality_analyzer/
├── main.py                       # CLI entry point, orchestration, report generation
├── code_smell_detector.py        # CodeSmellDetector  — astroid-based, 18+5 detectors
├── structural_smell_detector.py  # StructuralSmellDetector — ast + networkx, OO metrics
├── architectural_smell_detector.py # ArchitecturalSmellDetector — ast + networkx, module graphs
├── config_handler.py             # Loads and validates code_quality_config.yaml
└── exceptions.py                 # CodeAnalysisError with file/line/function context
```

| Module | Detector Class | Parser | Scope |
|--------|---------------|--------|-------|
| `code_smell_detector.py` | `CodeSmellDetector` | `astroid` | Per-file + cross-file |
| `structural_smell_detector.py` | `StructuralSmellDetector` | stdlib `ast` + `networkx` | Directory |
| `architectural_smell_detector.py` | `ArchitecturalSmellDetector` | stdlib `ast` + `networkx` | Directory |

**Two-phase API for code smells:** `detect_smells(file_path)` is called once per file (accumulates internal state), then `detect_cross_file_smells()` is called once after all files to report smells requiring multi-file context (data clumps, duplicate code, inappropriate intimacy, alternative classes, parallel inheritance).

**Configuration flow:** `ConfigHandler` reads `code_quality_config.yaml` and hands a threshold dict to each detector constructor. Thresholds can be tuned without touching code.

**Error handling:** `CodeAnalysisError` (in `exceptions.py`) carries `file_path`, `line_number`, and `function_name`. Parse errors are caught per-file and logged to `code_analysis.log` without aborting the run.

---

## Contributing

Contributions are welcome. Please open an issue before submitting large changes.

1. Fork the repository and create a feature branch
2. Set up the dev environment: `uv sync --extra dev`
3. Make your changes and add or update tests
4. `uv run pytest tests/` — all tests must pass
5. `uv run flake8 src/ --max-line-length=100` — no new lint errors
6. Open a pull request with a clear description

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Citation

If you use PyExamine in academic work, please cite the following paper:

```bibtex
@inproceedings{shivashankar2025pyexamine,
  title     = {PyExamine: A Comprehensive, Un-Opinionated Smell Detection Tool for Python},
  author    = {Shivashankar, Karthik and Martini, Antonio},
  booktitle = {2025 IEEE/ACM 22nd International Conference on Mining Software Repositories (MSR)},
  pages     = {763--774},
  year      = {2025},
  publisher = {IEEE}
}
```

> Shivashankar, K., & Martini, A. (2025, April). PyExamine: A Comprehensive, Un-Opinionated Smell Detection Tool for Python. In *2025 IEEE/ACM 22nd International Conference on Mining Software Repositories (MSR)* (pp. 763–774). IEEE.

---

## Acknowledgments

- Code smell taxonomy from Martin Fowler's *Refactoring: Improving the Design of Existing Code*
- Structural metrics (CBO, LCOM, DIT, RFC, NOM) from standard object-oriented quality literature
- AST parsing powered by [astroid](https://github.com/pylint-dev/astroid) and Python's stdlib `ast` module
- Dependency graph analysis powered by [networkx](https://networkx.org/)
- Progress reporting powered by [tqdm](https://tqdm.github.io/)

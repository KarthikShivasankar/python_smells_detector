# Code Quality Analyzer (PyExamine)

[![CI](https://github.com/KarthikShivasankar/python_smells_detector/actions/workflows/ci.yml/badge.svg)](https://github.com/KarthikShivasankar/python_smells_detector/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/code-quality-analyzer.svg)](https://pypi.org/project/code-quality-analyzer/)
[![Python versions](https://img.shields.io/pypi/pyversions/code-quality-analyzer.svg)](https://pypi.org/project/code-quality-analyzer/)
[![License: MIT](https://img.shields.io/pypi/l/code-quality-analyzer.svg)](LICENSE)

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
  - [Verifying across Python versions](#verifying-across-python-versions)
  - [Updating the documentation](#updating-the-documentation)
  - [Continuous integration (CI/CD)](#continuous-integration-cicd)
  - [Maintaining & releasing the package](#maintaining--releasing-the-package)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)
- [Citation](#citation)
- [Acknowledgments](#acknowledgments)

---

## Features

### Code Smells — 20 per-file detectors + 7 cross-file passes

| Smell | What it flags |
|-------|--------------|
| Long Method | Functions with too many lines of code (blank lines, comments and docstrings excluded) |
| Large Class | Classes with too many non-trivial methods |
| Primitive Obsession | Functions whose parameters are mostly annotated `int`/`str`/`float`/`bool` |
| Long Parameter List | Functions with too many parameters (positional-only, regular and keyword-only; `self`/`cls` excluded) |
| Switch Statements | Long `if`/`elif` chains and `match` statements with many cases |
| Divergent Change | Classes whose public methods start with many different verbs (snake_case or camelCase) |
| Shotgun Surgery | Functions called from many different contexts (builtins and raised exceptions excluded) |
| Excessive Comments | Files where comment density is unusually high |
| Lazy Class | Stand-alone classes (no bases, no decorators) with one small method |
| Feature Envy | Instance methods that use another object's attributes far more than their own |
| Message Chains | Long attribute chains such as `a.b.c.d.e` (Law of Demeter); module paths are not chains |
| Middle Man | Classes whose methods mostly just forward calls to another object |
| Speculative Generality | Classes with many empty (`pass` / `...`) methods or unused parameters |
| Temporary Field | Fields set in `__init__` that nothing in the project ever reads |
| Data Class | Classes made only of one-line `get_*` / `set_*` accessors |
| *(cross-file)* Dead Code | Private (`_name`) functions and methods never referenced anywhere in the project |
| *(cross-file)* Data Clumps | Parameter groups that appear together across many functions |
| *(cross-file)* Duplicate Code | Functions with identical structure (names ignored), within or across files |
| *(cross-file)* Inappropriate Intimacy | Classes that read or write another class's private (`_x`) fields |
| *(cross-file)* Alternative Classes | Unrelated classes with identical public interfaces |
| *(cross-file)* Parallel Inheritance | Parallel class hierarchies that change together |

### Architectural Smells — 8 detectors

Imports are resolved to project modules (absolute, relative, `from pkg import mod`,
`src/` layouts and analyzing a package directory itself); standard-library and
third-party imports are tracked separately and never become graph nodes. Imports
under `if TYPE_CHECKING:` are ignored.

| Smell | What it flags |
|-------|--------------|
| God Object | Modules with an excessive number of public functions |
| Cyclic Dependency | One finding per group of modules that import each other (strongly connected component), with an example cycle |
| Hub-like Dependency | Modules with both high fan-in and high fan-out inside the project |
| Scattered Functionality | The same function name repeated across many modules |
| Unstable Dependency | Modules depending on a less stable, highly unstable module (Stable Dependencies Principle) |
| Orphan Module | Modules with no import connections to the rest of the project |
| Improper API Usage | Modules that repeat the same API call patterns excessively |
| Redundant Abstractions | Module pairs with nearly identical public function sets |

### Structural Smells — 18 metric-based detectors

Function-level metrics cover module-level functions as well as methods, and `async` code.

| Smell | Metric | What it flags |
|-------|--------|--------------|
| High Number of Methods | NOM | Classes with more methods than the threshold |
| High Weighted Methods per Class | WMPC1 / WMPC2 | Classes whose methods are, in sum, too complex or take too many parameters |
| Large Class | SIZE2 | Classes with too many methods plus fields |
| High Weight of a Class | WAC | Classes with too many fields (class attributes and `self.x` assignments) |
| Low Cohesion | LCOM | Classes whose methods don't share fields |
| High Response | RFC | Classes that trigger too many responses to a message |
| High Message Passing Coupling | MPC | Classes sending too many messages to other objects |
| High Coupling Between Object Classes | CBO | Classes using too many distinct imported or project classes/modules |
| Too Many Classes in Module | NOCC | Modules with an excessive number of classes |
| Deep Inheritance | DIT | Classes with deep inheritance chains, followed across modules |
| Large Module | LOC | Modules with too many lines of code |
| Too Many Classes in Project | NOC | Projects with an excessive class count |
| High Cyclomatic Complexity | CC | Functions with too many decision points (McCabe, incl. comprehensions, `match`, conditional expressions) |
| High Fan-out | Fan-out | Modules depending on too many non-stdlib modules |
| High Fan-in | Fan-in | Project modules imported by too many others |
| Long File | File length | Files with too many lines of code |
| Too Many Branches | Branches | Functions with too many branches |
| Deep Nesting | Nesting | Functions nesting `if`/`for`/`while`/`try`/`with`/`match` blocks too deeply |

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

Fail a build when findings of a given severity appear:

```bash
analyze_code_quality src/ --format json --output quality.json --fail-on high
```

The exit code is `1` when any reported finding is at least `--fail-on`, so the
step fails without any scripting. See [GitHub Actions](#github-actions) and
[GitLab CI](#gitlab-ci) below.

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

Multiple names are space-separated. The names are matched against directory basenames (not full paths), so `--ignore tests` skips any folder named `tests` anywhere in the tree. Hidden folders (`.git`, `.venv`, `.tox`, ...), `__pycache__`, `venv`, `node_modules` and `site-packages` are always skipped.

The target can also be a single `.py` file.

### Save a report

A text run writes `code_quality_report.txt` and `code_quality_report.csv` to the current directory. Use `--output` to choose the base name:

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
| `directory` | positional | Project directory, or a single `.py` file, to analyze | *(required)* |
| `--type` | option | Limit analysis to `code`, `architectural`, or `structural` | all three |
| `--config` | option | Path to a YAML threshold configuration file. If omitted and no `code_quality_config.yaml` exists in the current directory, the config bundled with the package is used. | `code_quality_config.yaml` |
| `--output` | option | Base name for output files — generates `<name>.txt` + `<name>.csv` (with `--format json`: the JSON file to write) | `code_quality_report` |
| `--ignore` | option (repeatable) | Directory names to skip during traversal | none |
| `--format` | option | `text` (txt/csv reports) or `json` (one JSON document on stdout, or in the `--output` file; writes no other files, only warnings on stderr) | `text` |
| `--min-severity` | option | Only report findings of at least `low`, `medium` or `high` | `low` |
| `--fail-on` | option | Exit with code 1 if any reported finding is at least `low`, `medium` or `high` | never |
| `--debug` | flag | Enable verbose debug logging (and, in text mode, to `code_analysis.log`) | off |
| `--version` | flag | Print the version and exit | |

**Exit codes:** `0` the analysis completed (and `--fail-on`, if given, was not
reached); `1` `--fail-on` was reached; `2` usage error — bad arguments, or the
path or config file does not exist. A file that cannot be parsed does not change
the exit code; it is listed under `errors` in the JSON report.

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
python -m code_quality_analyzer /path/to/project
# or via uv
uv run python -m code_quality_analyzer /path/to/project
```

### Agents, scripts and test harnesses

The CLI with `--format json` and the `analyze()` function return the same report:

```bash
analyze_code_quality /path/to/project --format json            # report on stdout
analyze_code_quality src/app.py --format json --min-severity medium
analyze_code_quality /path/to/project --format json --output report.json --fail-on high
```

```python
from code_quality_analyzer import analyze

report = analyze("/path/to/project", types=["code", "structural"], ignore=["tests"])
for f in report["findings"]:
    print(f["severity"], f["name"], f["file_path"], f["line_number"])
assert not report["errors"], report["errors"]  # files that could not be parsed
```

Report schema (`schema_version` 1):

```json
{
  "schema_version": 1,
  "tool": {"name": "code-quality-analyzer", "version": "0.3.0"},
  "target": "/path/to/project",
  "summary": {"Code": 3, "Architectural": 1, "Structural": 2, "total": 6,
              "by_severity": {"low": 1, "medium": 4, "high": 1}},
  "findings": [
    {"type": "Code", "name": "Long Parameter List",
     "description": "'create_order' has 7 parameters in shop/orders.py",
     "file_path": "shop/orders.py", "module_class": "create_order",
     "line_number": 4, "severity": "medium"}
  ],
  "errors": [{"file": "shop/broken.py", "detector": "CodeSmellDetector",
              "error": "SyntaxError: invalid syntax (line 1)"}]
}
```

- `type` is `Code`, `Architectural` or `Structural`; `severity` is `low`, `medium` or `high`.
- `line_number` and `module_class` may be `null` (project-level findings); `file_path` lists several files, comma-separated, for cross-file findings.
- Findings are sorted by file, line, type and name, so two runs on the same code produce identical output.
- `errors` lists files that could not be read or parsed; the rest of the project is still analyzed.
- JSON mode writes nothing to disk except `--output`, and `analyze()` prints nothing to stdout and never configures logging.

`tests/fixtures/sample_project/` is a deliberately smelly project with known
findings (used by `tests/test_e2e.py`); point the CLI at it to see every field in use.

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

      - name: Run analysis (fails the job on high-severity findings)
        run: |
          mkdir -p reports
          analyze_code_quality src/ \
            --format json \
            --output reports/quality.json \
            --ignore tests build dist \
            --fail-on high

      - name: Upload report
        if: always()
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

All detection thresholds are defined in `code_quality_config.yaml`. The tool looks for this file in the current working directory by default, and if it isn't found there it falls back to the configuration bundled with the installed package — so a fresh `pip install code-quality-analyzer` works out of the box with no config file present. Use `--config` to point to a different file.

A config only needs the thresholds it changes: anything it leaves out keeps the bundled default (unknown keys are reported as warnings). Copy the file and edit the `value` fields to tune sensitivity for your project:

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
| `LAZY_CLASS_METHODS` | `1` | Stand-alone classes with this many methods or fewer (besides dunder methods)... |
| `LAZY_CLASS_LINES` | `10` | ...spanning this many lines or fewer are flagged as lazy |
| `DATA_CLASS_METHODS` | `4` | Classes made only of at least this many one-line `get_`/`set_` accessors are data classes |
| `FEATURE_ENVY_CALLS` | `3` | Methods making more calls to another object than this are flagged |
| `INAPPROPRIATE_INTIMACY_SHARED` | `2` | Classes accessing more than this many private fields of another class are flagged |
| `MESSAGE_CHAIN_LENGTH` | `3` | Call chains longer than this are flagged |
| `MIDDLE_MAN_RATIO` | `0.5` | Classes where more than this fraction of methods only delegate are flagged |
| `DATA_CLUMPS_THRESHOLD` | `6` | Minimum number of parameters two or more functions must share to be flagged. Only the maximal shared group is reported (not every subset), and a cross-file finding replaces the per-file finding for the same group |
| `TEMPORARY_FIELD_THRESHOLD` | `3` | Classes with at least this many `__init__` fields that nothing reads are flagged |
| `ALTERNATIVE_CLASSES_THRESHOLD` | `3` | Minimum number of classes with an identical public method set to be flagged |
| `DUPLICATE_CODE_THRESHOLD` | `2` | Minimum number of functions with identical normalized bodies to be flagged |
| `DUPLICATE_CODE_MIN_LINES` | `5` | Minimum function length (statements) to consider when detecting duplicate code |
| `DEAD_CODE_THRESHOLD` | `1` | Unreferenced private functions are reported for files with at least this many |
| `SPECULATIVE_GENERALITY_THRESHOLD` | `4` | Abstract classes with fewer concrete subclasses than this are flagged |
| `UNUSED_PARAMETERS_THRESHOLD` | `6` | Accumulation of unused parameters across methods above this is flagged |

### Architectural smell thresholds

| Key | Default | Description |
|-----|---------|-------------|
| `GOD_OBJECT_FUNCTIONS` | `20` | Modules with more public functions than this are flagged as god objects |
| `UNSTABLE_DEPENDENCY_THRESHOLD` | `0.8` | Depending on a less stable module whose instability Ce/(Ca+Ce) is above this is flagged |
| `HUB_LIKE_DEPENDENCY_RATIO` | `0.3` | Modules with balanced fan-in/fan-out connected to more than this fraction of all modules are hubs |
| `REDUNDANT_ABSTRACTION_SIMILARITY` | `0.7` | Module pairs sharing more than this fraction of functions are flagged as redundant |
| `IMPROPER_API_USAGE_RATIO` | `0.7` | Modules where repetitive API calls exceed this fraction of total calls are flagged |
| `CYCLIC_DEPENDENCY_MAX_LENGTH` | `3` | Every cycle is reported; cycles with more modules than this get high severity |

### Structural smell thresholds

| Key | Default | Metric | Description |
|-----|---------|--------|-------------|
| `NOM_THRESHOLD` | `10` | NOM | Classes with more methods than this are flagged |
| `WMPC1_THRESHOLD` | `20` | WMPC1 | Weighted Methods per Class (complexity-based) above this |
| `WMPC2_THRESHOLD` | `20` | WMPC2 | Weighted Methods per Class (parameter-based) above this |
| `SIZE2_THRESHOLD` | `15` | SIZE2 | Classes with more total members (methods + fields) than this |
| `WAC_THRESHOLD` | `10` | WAC | Classes with more fields (class attributes and `self.x`) than this are flagged |
| `LCOM_THRESHOLD` | `10` | LCOM | Lack of Cohesion in Methods above this threshold |
| `RFC_THRESHOLD` | `20` | RFC | Response for a Class above this threshold |
| `NOCC_THRESHOLD` | `10` | NOCC | Modules with more classes than this are flagged |
| `DIT_THRESHOLD` | `3` | DIT | Classes with inheritance depth greater than this are flagged |
| `LOC_THRESHOLD` | `150` | LOC | Modules with more lines than this are flagged |
| `MPC_THRESHOLD` | `25` | MPC | Message Passing Coupling above this threshold |
| `CBO_THRESHOLD` | `8` | CBO | Classes using more distinct imported (non-stdlib) or project classes/modules than this |
| `NOC_THRESHOLD` | `7` | NOC | Projects with more distinct classes than this are flagged |
| `CYCLOMATIC_COMPLEXITY_THRESHOLD` | `10` | CC | Methods with cyclomatic complexity above this are flagged |
| `MAX_FANOUT` | `15` | Fan-out | Modules depending on more than this many others are flagged |
| `MAX_FANIN` | `15` | Fan-in | Modules depended upon by more than this many others are flagged |
| `MAX_FILE_LENGTH` | `250` | — | Files with more lines than this are flagged |
| `MAX_BRANCHES` | `10` | — | Methods with more conditional branches than this are flagged |
| `MAX_NESTING_DEPTH` | `4` | — | Functions nesting blocks deeper than this are flagged as Deep Nesting |

---

## Output formats

The tool produces these output types:

| Format | How to get it | Contents |
|--------|--------------|----------|
| **Console** | Default (no `--output`) | Human-readable report printed to stdout |
| **Text file** (`*.txt`) | `--output <name>` | Same human-readable report, saved to `<name>.txt` |
| **CSV file** (`*.csv`) | `--output <name>` | One row per smell: Type, Name, Description, File, Module/Class, Line Number, Severity |
| **JSON** | `--format json` | One report document (see [Agents, scripts and test harnesses](#agents-scripts-and-test-harnesses)) |
| **Log file** (`code_analysis.log`) | Text mode only | Detailed analysis trace, warnings, and parse errors |

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
- Data Clumps: Parameters database, host, password, port, timeout, username appear together in functions: create, connect in src/db.py

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
git clone https://github.com/KarthikShivasankar/python_smells_detector
cd python_smells_detector

# Install runtime + dev dependencies (pytest, sphinx, etc.)
uv sync --extra dev
```

### Running tests

The test suite covers all three detectors (code, structural, architectural), the config handler, and the main orchestration layer. Tests write real Python source files into temporary directories — no mocking.

```bash
# Install dev dependencies first (includes pytest)
uv sync --extra dev

# Run the full test suite (216 tests)
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

# Verify all tests pass (exit 0 = success)
uv run python -m pytest tests/ -q && echo "All tests passed"
```

#### Test structure

| File | What it covers |
|------|---------------|
| `tests/test_code_smell_detector.py` | 20 per-file detectors + cross-file smells (data clumps, duplicate code, alternative classes, parallel inheritance). Positive and negative cases for each. |
| `tests/test_structural_smell_detector.py` | 18 metric-based detectors: NOM, WMPC, SIZE2, WAC, LCOM, RFC, MPC, CBO, NOCC, DIT, LOC, NOC, cyclomatic complexity, fan-in/out, branches, nesting, file length. |
| `tests/test_architectural_smell_detector.py` | All 8 architectural smell detectors: God Object, Scattered Functionality, Redundant Abstraction, Improper API Usage, Orphan Module, Cyclic Dependency, Unstable Dependency, Hub-like Dependency. |
| `tests/test_config_handler.py` | Config file loading, threshold validation, unknown-key handling, malformed YAML error handling. |
| `tests/test_main.py` | CLI parser flags, `analyze_*` functions, `generate_report`, `generate_csv_report` (field names, row contents, empty input). |
| `tests/test_e2e.py` | Runs `python -m code_quality_analyzer` in a subprocess on `tests/fixtures/sample_project/` and checks the JSON schema, the expected findings, the `errors` list and exit codes. |

> **Note:** `pytest` is blocked by an application control policy on some Windows setups — use `python -m pytest` instead of the bare `pytest` command.

### Linting

Linting is handled by [ruff](https://docs.astral.sh/ruff/) (configured in `pyproject.toml`):

```bash
uv run ruff check src/ tests/
uv run ruff check src/ tests/ --fix   # auto-fix
```

> Ruff is pinned to `target-version = "py310"`, which guards against
> accidentally introducing Python 3.12-only f-string syntax (line breaks inside
> `{...}` replacement fields) that would break the package on Python 3.10/3.11.

### Verifying across Python versions

The package supports Python 3.10–3.14. To run the suite against a specific
interpreter without touching your project venv:

```bash
uv run --no-project --python 3.10 --with . --with pytest python -m pytest tests/
```

### Updating the documentation

Documentation lives in `docs/source/` as reStructuredText and is built with
[Sphinx](https://www.sphinx-doc.org/) (config in `docs/source/conf.py`). The API
reference is generated from docstrings via autodoc, so updating a docstring
updates the docs.

```bash
# Build the HTML docs (sphinx ships in the dev extra). Expect zero warnings.
uv run --extra dev sphinx-build docs/source docs/build/html

# Windows legacy script
cd docs && make.bat html
```

What to update when you change docs:

1. Edit the relevant `docs/source/*.rst` (or the docstring being rendered).
2. If you add a new page, add it to the toctree in `docs/source/index.rst`.
3. Bump `release` in `docs/source/conf.py` when the version changes.
4. Rebuild with the command above and confirm **no warnings**.
5. Commit both the `docs/source/` change and the regenerated `docs/build/html/`
   (the built HTML is tracked in this repo).

> **Read the Docs:** `.readthedocs.yaml` drives the hosted docs build, which
> happens automatically from `docs/source/` on push — you do not need to commit
> `docs/build/` for Read the Docs, only for the in-repo copy.

### Continuous integration (CI/CD)

Workflows live in `.github/workflows/`. Every action is pinned to a commit SHA
(Dependabot keeps the pins current) and jobs get read-only permissions unless
they need more.

| Workflow | File | Trigger | What it does |
|----------|------|---------|--------------|
| **CI** | `ci.yml` | push / PR to `main`/`dev`, manual, and called by Release | `uv lock --check` + ruff; tests on Python 3.10–3.14 (Linux) and 3.13 (Windows, macOS) from the exact lockfile, with coverage (gate: 85%) on one leg; tests on the **oldest** declared dependency versions; the docs built exactly as Read the Docs builds them, warnings as errors; the tool analyzing its own `src/` (no file may fail to parse); `pip-audit`; then builds the sdist and wheel, `twine check --strict`s them and smoke-tests the installed wheel on its own (version, bundled config, JSON report, exit codes). |
| **Release** | `publish.yml` | GitHub Release published (or manual dry run) | Checks the tag matches `pyproject.toml` and that `CHANGELOG.md` has an entry, runs the whole CI workflow, publishes the very `dist` CI built and tested to PyPI via Trusted Publishing (OIDC, PEP 740 attestations), and attaches the same files to the GitHub Release. A manual run stops before publishing. |
| **CodeQL** | `codeql.yml` | push / PR + weekly | GitHub static security analysis of the Python source. |

[Dependabot](https://docs.github.com/code-security/dependabot) (`.github/dependabot.yml`)
opens weekly PRs for outdated Python deps and GitHub Actions. `.github/CODEOWNERS`
auto-requests review from the maintainer.

A change is "green" when **every CI job passes**. The main checks locally:

```bash
uv lock --check && uv run ruff check src/ tests/
uv run python -m pytest tests/ --cov=code_quality_analyzer --cov-fail-under=85
uv run --isolated --no-project --python 3.10 --resolution lowest-direct \
    --with-editable . --with "pytest>=8" python -m pytest tests/ -q -p no:cacheprovider
uv run --isolated --no-project --with . --with-requirements docs/requirements.txt \
    sphinx-build -W -b html docs/source docs/_build/html
uv build && uvx twine check --strict dist/*
```

### Maintaining & releasing the package

The package is `code-quality-analyzer` on PyPI; the import name is
`code_quality_analyzer`. Releases are automated through Trusted Publishing — no
API token is stored anywhere.

**One-time setup** — add a trusted publisher at
PyPI → Project → Settings → Publishing
([docs](https://docs.pypi.org/trusted-publishers/)), and create a GitHub
environment named `pypi` (optionally with required reviewers):

| Field | Value |
|-------|-------|
| Owner | `KarthikShivasankar` |
| Repository name | `python_smells_detector` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

**Release checklist:**

1. Bump the version in **both** `pyproject.toml` (`version`) and
   `docs/source/conf.py` (`release`), and run `uv lock`. This project uses
   [semantic versioning](https://semver.org/).
2. Add a `## X.Y.Z` section to `CHANGELOG.md` (the release workflow refuses to
   publish without one).
3. Rebuild the docs (`uv run --extra dev sphinx-build docs/source docs/build/html`).
4. Commit, push, and wait for CI on `main` to be green.
5. Optional dry run: **Actions → Release → Run workflow** runs the version check
   and the full CI without publishing.
6. Publish a GitHub Release; the tag is created from `main`:
   ```bash
   gh release create vX.Y.Z --target main --title "vX.Y.Z" --notes-file notes.md
   ```
7. Watch the **Release** workflow; confirm the version on
   <https://pypi.org/project/code-quality-analyzer/> and the files on the GitHub Release.

> **Note:** PyPI versions are immutable — you cannot re-upload an existing
> version. If a release is broken, bump to the next patch version and
> [yank](https://pypi.org/help/#yanked) the bad one in the PyPI UI
> (Project → Releases → Options → Yank). Yanking hides it from new installs
> without breaking existing pins.

**Manual publish (fallback, if Trusted Publishing isn't set up):**

```bash
uv build
uv run --with twine python -m twine check dist/*
uv publish --token pypi-xxxxxxxx          # or set UV_PUBLISH_TOKEN
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
4. `uv run python -m pytest tests/` — all tests must pass
5. `uv run ruff check src/ tests/` — no lint errors
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

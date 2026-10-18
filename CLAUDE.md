# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Installation (uv)
```bash
uv sync                    # install all runtime deps
uv sync --extra dev        # also installs sphinx, pytest
```

### Installation (pip fallback)
```bash
pip install -e .
pip install -e ".[dev]"
```

### Running the CLI
```bash
analyze_code_quality /path/to/project --config code_quality_config.yaml
analyze_code_quality /path/to/project --type code --output report
analyze_code_quality /path/to/project --ignore tests docs venv
analyze_code_quality /path/to/project --debug
```
`--type` accepts: `code`, `architectural`, or `structural`
`--ignore` accepts one or more directory names to skip

With uv (before the package entry-point is on PATH):
```bash
uv run analyze_code_quality /path/to/project
```

### Tests
```bash
uv run python -m pytest tests/
uv run python -m pytest tests/test_e2e.py                 # end-to-end CLI run on tests/fixtures/sample_project
uv run pytest tests/test_code_smell_detector.py           # single file
uv run pytest tests/test_code_smell_detector.py::TestFoo  # single class
```

### Build & publish
```bash
uv build                   # produces dist/*.whl and dist/*.tar.gz
uv publish                 # upload to PyPI (requires UV_PUBLISH_TOKEN)
uv publish --index https://test.pypi.org/simple/  # TestPyPI
```

### Documentation
```bash
uv run --extra dev sphinx-build docs/source docs/build/html
# or the legacy way:
cd docs && make.bat html   # Windows
cd docs && make html       # Linux/Mac
```

## Architecture

The tool detects three smell categories, each handled by a dedicated detector:

| Module | Detector Class | Analysis Method |
|--------|---------------|-----------------|
| `code_smell_detector.py` | `CodeSmellDetector` | Uses `astroid` AST parsing; 21 per-file detection methods + 7 cross-file passes |
| `structural_smell_detector.py` | `StructuralSmellDetector` | Uses stdlib `ast` + `networkx`; 17 detection methods for OO and function metrics (CBO, LCOM, DIT, cyclomatic complexity, nesting, etc.) over methods and module-level functions |
| `architectural_smell_detector.py` | `ArchitecturalSmellDetector` | Uses `ast` + `networkx` for module-level dependency graphs; 8 detection methods (cyclic deps, god objects, hub-like deps, etc.) |

**Shared discovery** (`project.py`): `iter_python_files()` (sorted, skips hidden/venv/cache dirs, accepts a single file), `module_name()`, `iter_imports()` (relative imports, `TYPE_CHECKING` skipped) and `ModuleIndex` (resolves imported names to project modules). Both graph detectors use it, so module names and dependency edges agree.

**Orchestration** (`main.py`): `analyze_project()` is the CLI entry point; `analyze()` is the library entry point returning the JSON report dict (`findings`, `summary`, `errors`) that `--format json` prints. Exit codes: 0 ok, 1 `--fail-on` reached, 2 usage error. It runs all three detectors over a directory, aggregates results into `CodeSmell`/`StructuralSmell`/`ArchitecturalSmell` dataclasses, then calls `generate_report()` (text) and `generate_csv_report()` (CSV). Detection can be narrowed to one category via `--type`.

**Configuration** (`config_handler.py` + `code_quality_config.yaml`): All thresholds (e.g., `LONG_METHOD_LINES: 45`, `CYCLOMATIC_COMPLEXITY_THRESHOLD: 10`) live in `code_quality_config.yaml`. `ConfigHandler` loads the YAML over the bundled defaults (missing keys keep their default, unknown keys warn) and hands per-category threshold dicts to each detector constructor. Customize thresholds here before running analyses.

**Error handling**: `CodeAnalysisError` (in `exceptions.py`) carries `file_path`, `line_number`, and `function_name`. File-level parse errors (syntax errors, encoding errors) are recorded in each detector's `errors` list (surfaced as `errors` in the JSON report) without aborting the full run.

## Key Design Notes

- `astroid` (not stdlib `ast`) is the parser for `CodeSmellDetector` — it provides richer type inference. `StructuralSmellDetector` and `ArchitecturalSmellDetector` use stdlib `ast`.
- `networkx` graphs are built per-analysis run (not cached); for large projects, the graph construction in `ArchitecturalSmellDetector` and `StructuralSmellDetector` is the primary performance cost.
- `CodeSmellDetector` has a two-phase API: `detect_smells(file_path)` is called per-file (accumulates state internally), then `detect_cross_file_smells()` is called once after all files to report smells that span multiple files (alternative classes, data clumps, duplicate code, inappropriate intimacy, parallel inheritance, temporary fields read elsewhere, dead code). `StructuralSmellDetector` and `ArchitecturalSmellDetector` take a directory path directly and handle multi-file traversal internally.
- All detection methods in `CodeSmellDetector` use `module.nodes_of_class(nodes.XxxDef)` for full AST traversal — this finds smells inside nested classes and methods, not just top-level definitions.

# AGENTS.md

Guidance for coding agents working in this repository. Humans: see `README.md`
for full docs and `CLAUDE.md` for an architecture deep-dive.

## What this is

`code-quality-analyzer` (aka **PyExamine**) is a Python static-analysis CLI that
detects **code smells**, **architectural smells**, and **structural smells**.
Published to PyPI as `code-quality-analyzer`; the import package is
`code_quality_analyzer` (under `src/`). CLI entry point: `analyze_code_quality`.

## Setup

```bash
uv sync --extra dev        # runtime + dev deps (pytest, ruff, sphinx)
# pip fallback:
pip install -e ".[dev]"
```

## Core commands

```bash
# Tests (full suite is 216 tests; tests/test_e2e.py runs the real CLI in a subprocess)
uv run python -m pytest tests/
uv run python -m pytest tests/test_main.py::TestResolveConfigPath   # single class

# Lint (config in pyproject.toml [tool.ruff])
uv run ruff check src/ tests/
uv run ruff check src/ tests/ --fix   # autofix

# Run the CLI against the package itself / the smelly sample project
uv run python -m code_quality_analyzer src/ --type structural
uv run python -m code_quality_analyzer tests/fixtures/sample_project --format json

# Build + validate distribution
uv build
uv run --with twine python -m twine check dist/*

# Build docs (Sphinx, zero warnings expected)
uv run --extra dev sphinx-build docs/source docs/build/html
```

## Using PyExamine from an agent or harness

- Python: `from code_quality_analyzer import analyze; analyze(path, types=["code"], ignore=["tests"])`
  returns a list of JSON-serialisable dicts with keys `type`, `name`, `description`,
  `file_path`, `module_class`, `line_number`, `severity`. No stdout output, no files written.
- CLI: `analyze_code_quality PATH --format json [--type code] [--output out.json]` prints one
  JSON document `{"findings": [...], "summary": {...}}` to stdout; all progress and logs go
  to stderr.

## Critical gotchas (read before editing)

- **Python 3.10+ support is real.** `requires-python = ">=3.10"`. Do **not**
  use line breaks inside single/double-quoted f-string replacement fields
  (e.g. `f"x {\n   value}"`) — that is PEP 701 syntax valid only on 3.12+ and
  will raise `SyntaxError` on 3.10/3.11. Keep each `{...}` field on one line.
  Ruff's `target-version = "py310"` (in `pyproject.toml`) catches this in CI.
- **Verify across versions** with the interpreters CI uses (3.10–3.14):
  `uv run --no-project --python 3.10 --with . --with pytest python -m pytest tests/`
- **Dependency floors are tested, not guessed** (astroid 3.0, networkx 3.0, PyYAML 6.0.1,
  tqdm 4.60): `uv run --isolated --no-project --python 3.10 --resolution lowest-direct
  --with "pytest>=8" --with-editable . python -m pytest tests/`
- **Config fallback:** the CLI loads `code_quality_config.yaml` from the CWD, and
  falls back to the copy bundled in the package
  (`src/code_quality_analyzer/code_quality_config.yaml`) via
  `resolve_config_path()` in `main.py`. Keep the root and packaged copies in sync.
- **Line endings are LF.** Avoid bulk reformatting that flips line endings.
- **`tests/fixtures/sample_project/` is smelly on purpose** (and `shop/broken.py`
  does not parse). Do not fix it; ruff excludes it. If you change a detector so
  that its findings move, update `EXPECTED` in `tests/test_e2e.py`.
- **Measure precision on real code** before changing a heuristic or default:
  run `--format json` over a few packages in `.venv/lib/python3.*/site-packages`
  (astroid, networkx, yaml) and read samples of the findings, not only counts.
- **`pytest` bare command may be blocked** by an application-control policy on
  some Windows setups — always invoke as `python -m pytest`.

## Using the tool from an agent or harness

```bash
python -m code_quality_analyzer <dir-or-file> --format json [--type code|architectural|structural]
    [--min-severity low|medium|high] [--fail-on low|medium|high] [--ignore DIR ...]
```

- stdout is exactly one JSON report; nothing is written to disk unless `--output`.
- Report keys: `schema_version` (1), `tool`, `target`, `summary` (per type,
  `total`, `by_severity`), `findings`, `errors`. Each finding has `type`,
  `name`, `description`, `file_path`, `module_class`, `line_number`, `severity`
  (`low`/`medium`/`high`). Findings are sorted, so output is deterministic.
- `errors` lists files that could not be parsed; the rest is still analyzed.
- Exit codes: `0` done, `1` `--fail-on` reached, `2` usage error (missing path/config).
- In Python: `from code_quality_analyzer import analyze; report = analyze(path)`
  returns the same dict and prints nothing to stdout.

## Layout

```
src/code_quality_analyzer/
  main.py                        # CLI entry, orchestration, report generation
  code_smell_detector.py         # CodeSmellDetector (astroid)
  structural_smell_detector.py   # StructuralSmellDetector (ast + networkx)
  architectural_smell_detector.py# ArchitecturalSmellDetector (ast + networkx)
  project.py                     # file discovery + import resolution shared by the graph detectors
  config_handler.py              # loads code_quality_config.yaml over the bundled defaults
  __main__.py                    # python -m code_quality_analyzer
  exceptions.py                  # CodeAnalysisError
tests/                           # pytest suite (writes real .py files to tmp dirs)
tests/fixtures/sample_project/   # deliberately smelly project for the end-to-end test
docs/source/                     # Sphinx docs
```

## CI and releases

- `ci.yml` is the single definition of "green" (lint + `uv lock --check`, tests on
  3.10–3.14 Linux and 3.13 Windows/macOS, oldest deps, docs as RTD builds them,
  self-analysis, pip-audit, built-wheel smoke test). `publish.yml` calls it.
- Actions are pinned to commit SHAs with a `# vX.Y.Z` comment; keep that format.
- If you change dependencies, run `uv lock` (CI fails on a stale lockfile).
- Releasing: bump `pyproject.toml` + `docs/source/conf.py`, add `## X.Y.Z` to
  `CHANGELOG.md`, push, then `gh release create vX.Y.Z --target main`. Only do
  this when explicitly asked.

## Conventions

- Add or update tests for any behavior change; the full suite must pass on 3.10–3.14.
- `uv run ruff check src/ tests/` must be clean before committing.
- Detection thresholds live in `code_quality_config.yaml` — tune there, not in code.
- Only commit when explicitly asked.

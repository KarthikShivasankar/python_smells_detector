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
# Tests (full suite is 127 tests)
uv run python -m pytest tests/
uv run python -m pytest tests/test_main.py::TestResolveConfigPath   # single class

# Lint (config in pyproject.toml [tool.ruff])
uv run ruff check src/ tests/
uv run ruff check src/ tests/ --fix   # autofix

# Run the CLI against the package itself
uv run analyze_code_quality src/ --type structural --ignore tests docs

# Build + validate distribution
uv build
uv run --with twine python -m twine check dist/*

# Build docs (Sphinx, zero warnings expected)
uv run --extra dev sphinx-build docs/source docs/build/html
```

## Critical gotchas (read before editing)

- **Python 3.10+ support is real.** `requires-python = ">=3.10"`. Do **not**
  use line breaks inside single/double-quoted f-string replacement fields
  (e.g. `f"x {\n   value}"`) — that is PEP 701 syntax valid only on 3.12+ and
  will raise `SyntaxError` on 3.10/3.11. Keep each `{...}` field on one line.
  Ruff's `target-version = "py310"` (in `pyproject.toml`) catches this in CI.
- **Verify across versions** with the interpreters CI uses:
  `uv run --no-project --python 3.10 --with . --with pytest python -m pytest tests/`
- **Config fallback:** the CLI loads `code_quality_config.yaml` from the CWD, and
  falls back to the copy bundled in the package
  (`src/code_quality_analyzer/code_quality_config.yaml`) via
  `resolve_config_path()` in `main.py`. Keep the root and packaged copies in sync.
- **Line endings are CRLF.** Avoid bulk reformatting that flips line endings.
- **`pytest` bare command may be blocked** by an application-control policy on
  some Windows setups — always invoke as `python -m pytest`.

## Layout

```
src/code_quality_analyzer/
  main.py                        # CLI entry, orchestration, report generation
  code_smell_detector.py         # CodeSmellDetector (astroid)
  structural_smell_detector.py   # StructuralSmellDetector (ast + networkx)
  architectural_smell_detector.py# ArchitecturalSmellDetector (ast + networkx)
  config_handler.py              # loads/validates code_quality_config.yaml
  exceptions.py                  # CodeAnalysisError
tests/                           # pytest suite (writes real .py files to tmp dirs)
docs/source/                     # Sphinx docs
```

## Conventions

- Add or update tests for any behavior change; the full suite must pass on 3.10–3.13.
- `uv run ruff check src/ tests/` must be clean before committing.
- Detection thresholds live in `code_quality_config.yaml` — tune there, not in code.
- Only commit when explicitly asked.

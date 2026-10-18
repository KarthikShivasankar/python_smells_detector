# Changelog

## 0.3.0

Merges `fix/detector-precision` and follows it with a full review of the detectors.

### Agent and harness interface
- `--format json` / `analyze()` return one report: `schema_version`, `tool`, `target`,
  `summary` (per type, `total`, `by_severity`), sorted `findings`, and `errors` (files
  that could not be parsed). `analyze()` now returns this dict instead of a list.
- Exit codes: `0` done, `1` `--fail-on {low,medium,high}` reached, `2` usage error
  (missing path or config). New `--min-severity`, `--version`, and `python -m code_quality_analyzer`.
- The target may be a single `.py` file. Hidden dirs, `__pycache__`, `venv`,
  `node_modules` and `site-packages` are always skipped; file order is deterministic.
- JSON mode writes no files (no `code_analysis.log`) and only logs warnings.
- Severities are always `low`/`medium`/`high` (several smells had none, structural ones were capitalized).
- A config only needs the thresholds it changes; the rest keep the bundled defaults
  (a missing key used to fail every file with `KeyError`).
- End-to-end test (`tests/test_e2e.py`) runs the CLI on `tests/fixtures/sample_project`.

### Detection fixes
- Architectural: every import target used to be treated as a project module, so `os`,
  `sys` etc. were graph nodes and skewed every metric; any import starting with a
  stdlib name (`requests` -> `re`) counted as stdlib; `from . import x` was ignored and
  analyzing a package dir lost all its absolute imports. Imports are now resolved
  against the project's modules (relative imports, `src/` layouts, `TYPE_CHECKING` skipped).
- Cyclic Dependency: one finding per strongly connected component (linear time) instead of
  enumerating simple cycles (exponential); exclusions match module parts, so `database`
  is no longer skipped as `base`.
- Unstable Dependency now follows the Stable Dependencies Principle (depending on a less
  stable module) instead of flagging every entry point; Hub-like Dependency requires
  balanced fan-in and fan-out instead of flagging pure libraries.
- Structural: DIT followed the real inheritance chain only by accident (always 2); bases are
  now resolved across modules. WMPC, SIZE2, WAC, MPC and CBO were implemented but never run;
  CBO counted local variables. Complexity, branches and nesting now cover module-level
  functions, async code, `match`, comprehensions and conditional expressions; nesting is
  reported as its own smell (Deep Nesting) using `MAX_NESTING_DEPTH`. A one-line docstring
  no longer hides the rest of the file from LOC and Long File. Fan-in/out use resolved imports.
- Code: Data Class, Lazy Class and Dead Code were implemented but never run (and crashed on
  some decorators). Dead Code is now project-wide over private functions and methods.
  Long Parameter List and Data Clumps count keyword-only and positional-only parameters;
  Switch Statements covers `match`; Feature Envy applies to instance methods only;
  Inappropriate Intimacy counts private fields only; Temporary Field ignores fields read
  through another object anywhere in the project; Shotgun Surgery ignores raised
  exceptions; Message Chains ignores module paths and no longer skips any chain that
  merely contains `.name`; Speculative Generality ignores `cls`, `_`-prefixed and
  overriding signatures; Divergent Change understands camelCase; Long Method skips docstrings.
- Default `DUPLICATE_CODE_THRESHOLD` is 2 (15 identical functions never happened).
- Output is deterministic: descriptions no longer depend on set order (`PYTHONHASHSEED`).
- Exclusions (utils, core, base, ...) ignore the analyzed package's own name; `src/pkg`
  answers to `import pkg`; relative imports above the analyzed root are ignored; relative
  imports of siblings named like stdlib modules count for CBO; private hooks overridden in
  subclasses and dunder protocol parameters are not reported; a recursion overflow on
  generated code no longer disables nesting/branch checks silently.

### Performance
- Structural analysis walks each file once and caches cyclomatic complexity; WAC/SIZE2 no
  longer re-walk every method per field. Cycle detection is linear. django (2,933 files):
  code 76 s, structural 45 s, architectural 4 s.

### Dependencies and CI
- Dependency floors verified with `--resolution lowest-direct`: astroid>=3.0, networkx>=3.0,
  pyyaml>=6.0.1, tqdm>=4.60 (the old >=2.0 floors could not even be installed). Lockfile
  upgraded (astroid 4.3.4, networkx 3.7, tqdm 4.70.1, ruff 0.17.1, pytest 9.1.1).
- Python 3.14 added to CI and classifiers. Actions: checkout v7, setup-uv v10.3.0 (pinned:
  setup-uv publishes no moving v10 tag), upload-artifact v7, download-artifact v8,
  codeql-action v4. The release workflow no longer uses the uv cache.

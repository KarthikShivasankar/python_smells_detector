"""
End-to-end check of the installed CLI, as an agent or CI job would run it:
``python -m code_quality_analyzer <path> --format json`` on the deliberately
smelly project in tests/fixtures/sample_project.
"""
import json
import os
import subprocess
import sys

import pytest

SAMPLE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_project")
SRC = os.path.join(os.path.dirname(__file__), "..", "src")

# (type, name, file, line) every run on the sample project must report
EXPECTED = {
    ("Architectural", "Cyclic Dependency", "billing.py", None),
    ("Code", "Data Class", "billing.py", 19),
    ("Code", "Lazy Class", "billing.py", 33),
    ("Code", "Duplicate Code", "billing.py, orders.py", None),
    ("Code", "Long Parameter List", "orders.py", 4),
    ("Code", "Switch Statements", "orders.py", 9),
    ("Code", "Dead Code", "orders.py", 42),
    ("Code", "Message Chains", "orders.py", 51),
    ("Code", "Feature Envy", "orders.py", 53),
    ("Structural", "Deep Nesting", "orders.py", 22),
}


def run_cli(*args, cwd):
    env = {**os.environ, "PYTHONPATH": os.path.abspath(SRC)}
    return subprocess.run([sys.executable, "-m", "code_quality_analyzer", *args],
                          capture_output=True, text=True, cwd=cwd, env=env, timeout=120)


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    cwd = tmp_path_factory.mktemp("cwd")
    result = run_cli(SAMPLE, "--format", "json", cwd=cwd)
    assert result.returncode == 0, result.stderr
    assert list(cwd.iterdir()) == [], "JSON mode must not write files"
    return json.loads(result.stdout)


def test_report_schema(report):
    assert report["schema_version"] == 1
    assert report["tool"]["name"] == "code-quality-analyzer"
    assert report["summary"]["total"] == len(report["findings"])
    assert sum(report["summary"]["by_severity"].values()) == len(report["findings"])
    for finding in report["findings"]:
        assert set(finding) == {"type", "name", "description", "file_path",
                                "module_class", "line_number", "severity"}
        assert finding["severity"] in ("low", "medium", "high")


def test_expected_findings(report):
    def short(path):
        return ", ".join(os.path.basename(p) for p in path.split(", "))
    found = {(f["type"], f["name"], short(f["file_path"]), f["line_number"])
             for f in report["findings"]}
    assert EXPECTED <= found, f"missing: {sorted(EXPECTED - found, key=str)}"


def test_unparsable_file_listed_in_errors(report):
    assert {os.path.basename(e["file"]) for e in report["errors"]} == {"broken.py"}
    assert all("SyntaxError" in e["error"] for e in report["errors"])


def test_fail_on_exit_code(tmp_path):
    assert run_cli(SAMPLE, "--format", "json", "--fail-on", "high", cwd=tmp_path).returncode == 1
    clean = tmp_path / "clean.py"
    clean.write_text("def add(a, b):\n    return a + b\n")
    assert run_cli(str(clean), "--format", "json", "--fail-on", "low", cwd=tmp_path).returncode == 0


def test_bad_path_exit_code(tmp_path):
    result = run_cli(str(tmp_path / "missing"), "--format", "json", cwd=tmp_path)
    assert result.returncode == 2
    assert result.stdout == ""

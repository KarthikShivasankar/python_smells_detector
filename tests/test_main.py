"""
Tests for main.py orchestration: analyze_code_smells, analyze_architectural_smells,
analyze_structural_smells, generate_report, generate_csv_report, and create_parser.
"""
import csv
import json
import os
import sys

import pytest

from code_quality_analyzer.architectural_smell_detector import (
    ArchitecturalSmell,
    ArchitecturalSmellDetector,
)
from code_quality_analyzer.code_smell_detector import CodeSmell, CodeSmellDetector
from code_quality_analyzer.main import (
    DEFAULT_CONFIG_NAME,
    analyze,
    analyze_architectural_smells,
    analyze_code_smells,
    analyze_project,
    analyze_structural_smells,
    create_parser,
    generate_csv_report,
    generate_report,
    resolve_config_path,
)
from code_quality_analyzer.structural_smell_detector import StructuralSmell, StructuralSmellDetector
from conftest import ARCHITECTURAL_THRESHOLDS, CODE_SMELL_THRESHOLDS, STRUCTURAL_THRESHOLDS

# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------

class TestCreateParser:
    def test_parses_directory_argument(self):
        parser = create_parser()
        args = parser.parse_args(['/some/path'])
        assert args.directory == '/some/path'

    def test_default_config(self):
        parser = create_parser()
        args = parser.parse_args(['/some/path'])
        assert args.config == 'code_quality_config.yaml'

    def test_type_choices(self):
        parser = create_parser()
        for t in ('code', 'architectural', 'structural'):
            args = parser.parse_args(['/p', '--type', t])
            assert args.type == t

    def test_invalid_type_raises(self):
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(['/p', '--type', 'invalid'])

    def test_ignore_flag(self):
        parser = create_parser()
        args = parser.parse_args(['/p', '--ignore', 'tests', 'docs'])
        assert 'tests' in args.ignore
        assert 'docs' in args.ignore

    def test_debug_flag(self):
        parser = create_parser()
        args = parser.parse_args(['/p', '--debug'])
        assert args.debug is True

    def test_output_flag(self):
        parser = create_parser()
        args = parser.parse_args(['/p', '--output', 'my_report'])
        assert args.output == 'my_report'


# ---------------------------------------------------------------------------
# resolve_config_path
# ---------------------------------------------------------------------------

class TestResolveConfigPath:
    def test_existing_explicit_path_is_used(self, tmp_path):
        cfg = tmp_path / "custom.yaml"
        cfg.write_text("code_smells: {}\n")
        assert resolve_config_path(str(cfg)) == str(cfg)

    def test_default_in_cwd_is_used(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / DEFAULT_CONFIG_NAME).write_text("code_smells: {}\n")
        assert resolve_config_path(DEFAULT_CONFIG_NAME) == DEFAULT_CONFIG_NAME

    def test_default_missing_falls_back_to_packaged(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        resolved = resolve_config_path(DEFAULT_CONFIG_NAME)
        assert resolved != DEFAULT_CONFIG_NAME
        assert resolved.endswith(DEFAULT_CONFIG_NAME)
        assert os.path.isfile(resolved)

    def test_missing_explicit_path_returned_unchanged(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_config_path("nonexistent_custom.yaml") == "nonexistent_custom.yaml"


# ---------------------------------------------------------------------------
# analyze_code_smells
# ---------------------------------------------------------------------------

class TestAnalyzeCodeSmells:
    def test_detects_smells_in_bad_code(self, tmp_path):
        methods = "\n".join(
            f"    def method{i}(self):\n        self.x = {i}\n        return self.x"
            for i in range(16)
        )
        f = tmp_path / "large.py"
        f.write_text(f"class Big:\n{methods}\n")
        detector = CodeSmellDetector(CODE_SMELL_THRESHOLDS)
        result = analyze_code_smells(str(tmp_path), detector)
        assert any("Large Class" in s.name for s in result)

    def test_empty_directory_returns_empty(self, tmp_path):
        detector = CodeSmellDetector(CODE_SMELL_THRESHOLDS)
        result = analyze_code_smells(str(tmp_path), detector)
        assert result == []

    def test_ignore_dirs_respected(self, tmp_path):
        ignored = tmp_path / "skip_me"
        ignored.mkdir()
        bad = ignored / "bad_code.py"
        methods = "\n".join(
            f"    def method{i}(self):\n        self.x = {i}\n        return self.x"
            for i in range(16)
        )
        bad.write_text(f"class Big:\n{methods}\n")
        detector = CodeSmellDetector(CODE_SMELL_THRESHOLDS)
        result = analyze_code_smells(str(tmp_path), detector, ignore_dirs=['skip_me'])
        assert result == [], "Ignored directory should not be analyzed"

    def test_syntax_error_file_skipped_gracefully(self, tmp_path):
        f = tmp_path / "broken.py"
        f.write_text("def func(:\n    pass\n")
        good = tmp_path / "good.py"
        good.write_text("x = 1\n")
        detector = CodeSmellDetector(CODE_SMELL_THRESHOLDS)
        # Should not raise — error is caught and the good file is still processed
        result = analyze_code_smells(str(tmp_path), detector)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# analyze_architectural_smells
# ---------------------------------------------------------------------------

class TestAnalyzeArchitecturalSmells:
    def test_detects_god_object(self, tmp_path):
        funcs = "\n".join(f"def func_{i}(): return {i}" for i in range(26))
        (tmp_path / "god.py").write_text(funcs)
        detector = ArchitecturalSmellDetector(ARCHITECTURAL_THRESHOLDS)
        result = analyze_architectural_smells(str(tmp_path), detector)
        assert any("God Object" in s.name for s in result)

    def test_ignore_dirs_respected(self, tmp_path):
        skip = tmp_path / "skip"
        skip.mkdir()
        funcs = "\n".join(f"def func_{i}(): return {i}" for i in range(26))
        (skip / "god.py").write_text(funcs)
        detector = ArchitecturalSmellDetector(ARCHITECTURAL_THRESHOLDS)
        result = analyze_architectural_smells(str(tmp_path), detector, ignore_dirs=['skip'])
        assert not any("God Object" in s.name for s in result)


# ---------------------------------------------------------------------------
# analyze_structural_smells
# ---------------------------------------------------------------------------

class TestAnalyzeStructuralSmells:
    def test_detects_loc_smell(self, tmp_path):
        lines = "\n".join(f"x{i} = {i}" for i in range(200))
        (tmp_path / "big.py").write_text(lines)
        detector = StructuralSmellDetector(STRUCTURAL_THRESHOLDS)
        result = analyze_structural_smells(str(tmp_path), detector)
        assert any("Lines of Code" in s.name for s in result)

    def test_ignore_dirs_respected(self, tmp_path):
        skip = tmp_path / "skip"
        skip.mkdir()
        lines = "\n".join(f"x{i} = {i}" for i in range(200))
        (skip / "big.py").write_text(lines)
        detector = StructuralSmellDetector(STRUCTURAL_THRESHOLDS)
        result = analyze_structural_smells(str(tmp_path), detector, ignore_dirs=['skip'])
        assert not any("Lines of Code" in s.name for s in result)


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------

class TestGenerateReport:
    def _make_smells(self):
        code = [CodeSmell("Long Method", "desc", "f.py", "MyClass", 10)]
        structural = [StructuralSmell("High LOC", "desc", "f.py", "mod")]
        architectural = [ArchitecturalSmell("God Object", "desc", "f.py", "mod")]
        return code, structural, architectural

    def test_prints_to_stdout_when_no_output(self, capsys):
        code, structural, architectural = self._make_smells()
        generate_report(code, architectural, structural)
        captured = capsys.readouterr()
        assert "Long Method" in captured.out
        assert "High LOC" in captured.out
        assert "God Object" in captured.out

    def test_writes_txt_file(self, tmp_path):
        code, structural, architectural = self._make_smells()
        out = str(tmp_path / "report.txt")
        generate_report(code, architectural, structural, output_txt=out)
        assert os.path.exists(out)
        content = open(out).read()
        assert "Long Method" in content

    def test_writes_csv_when_both_paths_given(self, tmp_path):
        code, structural, architectural = self._make_smells()
        txt = str(tmp_path / "report.txt")
        csv_path = str(tmp_path / "report.csv")
        generate_report(code, architectural, structural, output_txt=txt, output_csv=csv_path)
        assert os.path.exists(csv_path)

    def test_no_smells_still_produces_report(self, tmp_path):
        out = str(tmp_path / "empty.txt")
        generate_report([], [], [], output_txt=out)
        assert os.path.exists(out)
        content = open(out).read()
        assert "No code smells" in content or "No structural smells" in content

    def test_summary_counts_correct(self, tmp_path):
        code, structural, architectural = self._make_smells()
        out = str(tmp_path / "r.txt")
        generate_report(code, architectural, structural, output_txt=out)
        content = open(out).read()
        assert "Total Code Smells: 1" in content
        assert "Total Structural Smells: 1" in content
        assert "Total Architectural Smells: 1" in content


# ---------------------------------------------------------------------------
# generate_csv_report
# ---------------------------------------------------------------------------

class TestGenerateCSVReport:
    def _make_smells(self):
        code = [CodeSmell("Long Method", "a method is too long", "src/a.py", "MyClass", 42, "high")]
        structural = [StructuralSmell("High LOC", "module too long", "src/b.py", "my_mod", 1, "medium")]
        architectural = [ArchitecturalSmell("God Object", "too many funcs", "src/c.py", "big_mod", None, "low")]
        return code, structural, architectural

    def test_csv_has_header_row(self, tmp_path):
        code, structural, architectural = self._make_smells()
        csv_path = str(tmp_path / "report.csv")
        generate_csv_report(code, architectural, structural, csv_path)
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        assert 'Type' in headers
        assert 'Name' in headers
        assert 'Severity' in headers

    def test_csv_contains_all_smell_types(self, tmp_path):
        code, structural, architectural = self._make_smells()
        csv_path = str(tmp_path / "report.csv")
        generate_csv_report(code, architectural, structural, csv_path)
        with open(csv_path, newline='') as f:
            rows = list(csv.DictReader(f))
        types = {r['Type'] for r in rows}
        assert 'Code' in types
        assert 'Structural' in types
        assert 'Architectural' in types

    def test_csv_smell_details_correct(self, tmp_path):
        code, structural, architectural = self._make_smells()
        csv_path = str(tmp_path / "report.csv")
        generate_csv_report(code, architectural, structural, csv_path)
        with open(csv_path, newline='') as f:
            rows = {r['Type']: r for r in csv.DictReader(f)}
        assert rows['Code']['Name'] == 'Long Method'
        assert rows['Code']['Severity'] == 'high'
        assert rows['Code']['Line Number'] == '42'

    def test_empty_lists_produce_header_only(self, tmp_path):
        csv_path = str(tmp_path / "empty.csv")
        generate_csv_report([], [], [], csv_path)
        with open(csv_path, newline='') as f:
            rows = list(csv.DictReader(f))
        assert rows == []


# ---------------------------------------------------------------------------
# Machine-readable interfaces (library API and --format json)
# ---------------------------------------------------------------------------

BAD_CODE = "def f(a, b, c, d, e, f, g):\n    return a\n"
FINDING_KEYS = {'type', 'name', 'description', 'file_path', 'module_class',
                'line_number', 'severity'}


class TestMachineReadable:
    def test_format_flag(self):
        parser = create_parser()
        assert parser.parse_args(["/tmp"]).format == "text"
        assert parser.parse_args(["/tmp", "--format", "json"]).format == "json"

    def test_analyze_returns_report(self, tmp_path, capsys):
        (tmp_path / "bad.py").write_text(BAD_CODE)
        report = analyze(str(tmp_path), types=["code"])
        assert capsys.readouterr().out == "", "library call must not print to stdout"
        assert set(report) == {"schema_version", "tool", "target", "summary", "findings", "errors"}
        findings = report["findings"]
        assert any(f["name"] == "Long Parameter List" for f in findings)
        assert all(set(f) == FINDING_KEYS and f["type"] == "Code" for f in findings)
        assert all(f["severity"] in ("low", "medium", "high") for f in findings)
        assert report["summary"]["total"] == len(findings) == report["summary"]["Code"]
        assert report["errors"] == []
        json.dumps(report)

    def test_analyze_rejects_unknown_type(self, tmp_path):
        with pytest.raises(ValueError):
            analyze(str(tmp_path), types=["codes"])

    def test_cli_json_stdout_is_pure_json(self, tmp_path, monkeypatch, capsys):
        src = tmp_path / "src"
        src.mkdir()
        (src / "bad.py").write_text(BAD_CODE)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["analyze_code_quality", str(src), "--format", "json"])
        analyze_project()
        report = json.loads(capsys.readouterr().out)
        assert report["summary"]["Code"] == sum(f["type"] == "Code" for f in report["findings"])
        assert any(f["name"] == "Long Parameter List" for f in report["findings"])


class TestAgentContract:
    """The CLI contract that agents and CI harnesses rely on."""

    def _run(self, argv, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        return analyze_project(argv)

    def test_fail_on_sets_exit_code(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "bad.py").write_text(BAD_CODE)
        target = str(tmp_path / "bad.py")
        assert self._run([target, "--format", "json"], monkeypatch, tmp_path) == 0
        assert self._run([target, "--format", "json", "--fail-on", "low"],
                         monkeypatch, tmp_path) == 1
        capsys.readouterr()

    def test_clean_code_passes_fail_on(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "ok.py").write_text("def add(a, b):\n    return a + b\n")
        assert self._run([str(tmp_path / "ok.py"), "--format", "json", "--fail-on", "low"],
                         monkeypatch, tmp_path) == 0
        assert json.loads(capsys.readouterr().out)["findings"] == []

    def test_min_severity_filters(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "bad.py").write_text(BAD_CODE)
        self._run([str(tmp_path), "--format", "json", "--min-severity", "high"], monkeypatch, tmp_path)
        report = json.loads(capsys.readouterr().out)
        assert all(f["severity"] == "high" for f in report["findings"])

    def test_missing_path_is_usage_error(self, tmp_path, monkeypatch, capsys):
        with pytest.raises(SystemExit) as exc:
            self._run([str(tmp_path / "nope"), "--format", "json"], monkeypatch, tmp_path)
        assert exc.value.code == 2
        assert "no such file or directory" in capsys.readouterr().err

    def test_missing_config_is_usage_error(self, tmp_path, monkeypatch, capsys):
        with pytest.raises(SystemExit) as exc:
            self._run([str(tmp_path), "--format", "json", "--config", "missing.yaml"],
                      monkeypatch, tmp_path)
        assert exc.value.code == 2

    def test_json_mode_writes_no_files(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "bad.py").write_text(BAD_CODE)
        self._run([str(tmp_path), "--format", "json"], monkeypatch, tmp_path)
        assert sorted(p.name for p in tmp_path.iterdir()) == ["bad.py"]
        capsys.readouterr()

    def test_unparsable_file_reported_in_errors(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "broken.py").write_text("def broken(:\n")
        (tmp_path / "bad.py").write_text(BAD_CODE)
        self._run([str(tmp_path), "--format", "json"], monkeypatch, tmp_path)
        report = json.loads(capsys.readouterr().out)
        broken = str(tmp_path / "broken.py")
        assert {e["detector"] for e in report["errors"] if e["file"] == broken} == {
            "CodeSmellDetector", "ArchitecturalSmellDetector", "StructuralSmellDetector"}
        assert report["findings"], "other files are still analyzed"

    def test_findings_are_sorted(self, tmp_path):
        for name in ("b.py", "a.py"):
            (tmp_path / name).write_text(BAD_CODE)
        findings = analyze(str(tmp_path))["findings"]
        keys = [(f["file_path"], f["line_number"] or 0, f["type"], f["name"]) for f in findings]
        assert keys == sorted(keys)

    def test_partial_config_keeps_defaults(self, tmp_path):
        # Regression: a config missing any threshold made every file fail with KeyError
        cfg = tmp_path / "partial.yaml"
        cfg.write_text("code_smells:\n  LONG_PARAMETER_LIST:\n    value: 1\n")
        (tmp_path / "f.py").write_text("def f(a, b):\n    return a + b\n")
        report = analyze(str(tmp_path / "f.py"), types=["code"], config=str(cfg))
        assert report["errors"] == []
        assert [f["name"] for f in report["findings"]] == ["Long Parameter List"]


class TestDeterminism:
    def test_reports_identical_across_hash_seeds(self, tmp_path):
        # Regression: descriptions joined sets, so output changed with PYTHONHASHSEED
        import subprocess
        sample = os.path.join(os.path.dirname(__file__), "fixtures", "sample_project")
        src = os.path.join(os.path.dirname(__file__), "..", "src")
        outputs = set()
        for seed in ("1", "2", "3"):
            env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": os.path.abspath(src)}
            result = subprocess.run([sys.executable, "-m", "code_quality_analyzer", sample,
                                     "--format", "json"], capture_output=True, text=True,
                                    env=env, cwd=tmp_path, check=True)
            outputs.add(result.stdout)
        assert len(outputs) == 1

    def test_non_python_file_rejected(self, tmp_path):
        target = tmp_path / "notes.txt"
        target.write_text("hello")
        with pytest.raises(ValueError):
            analyze(str(target))

"""
Tests for main.py orchestration: analyze_code_smells, analyze_architectural_smells,
analyze_structural_smells, generate_report, generate_csv_report, and create_parser.
"""
import os
import csv
import pytest
from code_quality_analyzer.main import (
    create_parser,
    analyze_code_smells,
    analyze_architectural_smells,
    analyze_structural_smells,
    generate_report,
    generate_csv_report,
)
from code_quality_analyzer.code_smell_detector import CodeSmellDetector, CodeSmell
from code_quality_analyzer.structural_smell_detector import StructuralSmellDetector, StructuralSmell
from code_quality_analyzer.architectural_smell_detector import ArchitecturalSmellDetector, ArchitecturalSmell
from conftest import CODE_SMELL_THRESHOLDS, STRUCTURAL_THRESHOLDS, ARCHITECTURAL_THRESHOLDS


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

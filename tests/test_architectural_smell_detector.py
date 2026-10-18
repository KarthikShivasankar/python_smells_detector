"""
Comprehensive tests for ArchitecturalSmellDetector.

Each test class targets one of the eight architectural smell detectors.
Tests write real Python files into tmp_path directories so the detector
exercises its actual file-parsing and graph-building logic.
"""
from code_quality_analyzer.architectural_smell_detector import ArchitecturalSmellDetector

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def smells_named(detector, name):
    return [s for s in detector.architectural_smells if name in s.name]


# ---------------------------------------------------------------------------
# God Object
# ---------------------------------------------------------------------------

class TestGodObject:
    def test_detects_module_with_many_functions(self, architectural_smell_detector, tmp_path):
        # 26 public functions > GOD_OBJECT_FUNCTIONS threshold 20
        funcs = "\n".join(f"def public_func_{i}():\n    return {i}" for i in range(26))
        f = tmp_path / "god_module.py"
        f.write_text(funcs)
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "God Object"), \
            "Expected God Object for module with 26 public functions"

    def test_small_module_not_flagged(self, architectural_smell_detector, tmp_path):
        funcs = "\n".join(f"def func_{i}():\n    return {i}" for i in range(5))
        f = tmp_path / "small.py"
        f.write_text(funcs)
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "God Object")

    def test_private_functions_not_counted(self, architectural_smell_detector, tmp_path):
        # 26 private functions — should NOT count toward god-object threshold
        funcs = "\n".join(f"def _private_{i}():\n    return {i}" for i in range(26))
        f = tmp_path / "private_funcs.py"
        f.write_text(funcs)
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "God Object"), \
            "Private functions should not count toward God Object"

    def test_methods_and_imported_names_not_counted(self, architectural_smell_detector, tmp_path):
        # Regression for #32: class methods counted as module functions, and names
        # imported from a package outside the project produced a God Object for it
        classes = "\n".join(
            f"class C{c}:\n" + "\n".join(f"    def m{c}_{i}(self):\n        return {i}" for i in range(8))
            for c in range(3)
        )
        (tmp_path / "classes.py").write_text(classes + "\n")
        names = ", ".join(f"Name{i}" for i in range(21))
        (tmp_path / "importer.py").write_text(f"from extlib import {names}\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "God Object")


# ---------------------------------------------------------------------------
# Scattered Functionality
# ---------------------------------------------------------------------------

class TestScatteredFunctionality:
    def test_detects_same_function_in_many_modules(self, architectural_smell_detector, tmp_path):
        # Same function name in 3 modules → triggers Scattered Functionality
        for i in range(3):
            m = tmp_path / f"module_{i}.py"
            m.write_text(
                f"def duplicated_logic():\n    return {i}\n"
                f"def unique_func_{i}():\n    return {i}\n"
            )
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Scattered Functionality"), \
            "Expected Scattered Functionality for same function in 3 modules"

    def test_unique_functions_not_flagged(self, architectural_smell_detector, tmp_path):
        for i in range(3):
            m = tmp_path / f"module_{i}.py"
            m.write_text(f"def unique_{i}():\n    return {i}\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Scattered Functionality")

    def test_common_names_excluded(self, architectural_smell_detector, tmp_path):
        # 'main' and 'setup' are in the exclusion list
        for i in range(3):
            m = tmp_path / f"module_{i}.py"
            m.write_text(f"def main():\n    return {i}\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Scattered Functionality"), \
            "'main' is a common name and should be excluded"

    def test_same_method_in_classes_not_flagged(self, architectural_smell_detector, tmp_path):
        # Regression for #32: polymorphic methods are not scattered module functions
        for name in ("users", "orders", "invoices"):
            (tmp_path / f"{name}.py").write_text(
                f"class {name.title()}Record:\n"
                "    def to_dict(self):\n        return {}\n"
                "    def validate(self):\n        return True\n"
            )
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Scattered Functionality")


# ---------------------------------------------------------------------------
# Redundant Abstraction
# ---------------------------------------------------------------------------

class TestRedundantAbstraction:
    def test_detects_near_identical_modules(self, architectural_smell_detector, tmp_path):
        # Two modules with identical function sets > 80% similarity and >= 3 functions
        content = "\n".join(f"def method_{i}():\n    return {i}" for i in range(5))
        (tmp_path / "module_a.py").write_text(content)
        (tmp_path / "module_b.py").write_text(content)
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Redundant Abstraction"), \
            "Expected Redundant Abstraction for two modules with identical function sets"

    def test_different_modules_not_flagged(self, architectural_smell_detector, tmp_path):
        (tmp_path / "module_a.py").write_text(
            "def alpha(): pass\ndef beta(): pass\ndef gamma(): pass\n"
        )
        (tmp_path / "module_b.py").write_text(
            "def delta(): pass\ndef epsilon(): pass\ndef zeta(): pass\n"
        )
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Redundant Abstraction")


# ---------------------------------------------------------------------------
# Improper API Usage
# ---------------------------------------------------------------------------

class TestImproperAPIUsage:
    def test_detects_repetitive_api_calls(self, architectural_smell_detector, tmp_path):
        # 12 calls to api.method1 — repetition ratio will exceed threshold
        calls = "\n".join("    api.method1()" for _ in range(12))
        f = tmp_path / "api_abuse.py"
        f.write_text(f"def do_stuff(api):\n{calls}\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Improper API Usage"), \
            "Expected Improper API Usage for 12 identical api.method1() calls"

    def test_varied_api_calls_not_flagged(self, architectural_smell_detector, tmp_path):
        calls = "\n".join(f"    api.method_{i}()" for i in range(12))
        f = tmp_path / "varied_api.py"
        f.write_text(f"def do_stuff(api):\n{calls}\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Improper API Usage"), \
            "Varied API calls should not trigger Improper API Usage"

    def test_configured_ratio_is_used(self, architectural_smell_detector, tmp_path):
        # Regression for #33: IMPROPER_API_USAGE_RATIO (0.7) was ignored in favour of a
        # hard-coded 0.4; 5 of 10 calls repeated (50%) is below the configured ratio
        calls = ["    out.append(1)"] * 5 + [f"    a.m{i}()" for i in range(5)]
        f = tmp_path / "builder.py"
        f.write_text("def build(a):\n    out = []\n" + "\n".join(calls) + "\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Improper API Usage")


# ---------------------------------------------------------------------------
# Orphan Module
# ---------------------------------------------------------------------------

class TestOrphanModule:
    def test_detects_isolated_module(self, architectural_smell_detector, tmp_path):
        # One module completely unconnected to others
        (tmp_path / "isolated.py").write_text(
            "def standalone_function():\n    return 42\n"
        )
        (tmp_path / "connected_a.py").write_text(
            "import connected_b\ndef work():\n    connected_b.task()\n"
        )
        (tmp_path / "connected_b.py").write_text(
            "def task():\n    return 1\n"
        )
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Orphan Module"), \
            "Expected Orphan Module for isolated.py with no connections"

    def test_connected_modules_not_flagged(self, architectural_smell_detector, tmp_path):
        (tmp_path / "a.py").write_text("import b\ndef fa():\n    b.fb()\n")
        (tmp_path / "b.py").write_text("def fb():\n    return 1\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        # connected modules should not be flagged as orphans
        orphan_names = [
            s.module_class for s in architectural_smell_detector.architectural_smells
            if "Orphan" in s.name
        ]
        assert "a" not in orphan_names and "b" not in orphan_names, \
            "Connected modules should not be flagged as orphans"


# ---------------------------------------------------------------------------
# Cyclic Dependency
# ---------------------------------------------------------------------------

class TestCyclicDependency:
    def test_detects_mutual_import_cycle(self, architectural_smell_detector, tmp_path):
        # a imports b, b imports a → cycle of length 2
        (tmp_path / "cycle_a.py").write_text(
            "import cycle_b\ndef fa():\n    cycle_b.fb()\n"
        )
        (tmp_path / "cycle_b.py").write_text(
            "import cycle_a\ndef fb():\n    cycle_a.fa()\n"
        )
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Cyclic Dependency"), \
            "Expected Cyclic Dependency for mutual import between two modules"

    def test_acyclic_imports_not_flagged(self, architectural_smell_detector, tmp_path):
        (tmp_path / "top.py").write_text(
            "import middle\ndef main():\n    middle.run()\n"
        )
        (tmp_path / "middle.py").write_text(
            "import bottom\ndef run():\n    bottom.work()\n"
        )
        (tmp_path / "bottom.py").write_text(
            "def work():\n    return 1\n"
        )
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Cyclic Dependency"), \
            "Linear import chain should not have cyclic dependencies"

    def test_three_module_cycle(self, architectural_smell_detector, tmp_path):
        (tmp_path / "p.py").write_text("import q\ndef fp(): q.fq()\n")
        (tmp_path / "q.py").write_text("import r\ndef fq(): r.fr()\n")
        (tmp_path / "r.py").write_text("import p\ndef fr(): p.fp()\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Cyclic Dependency"), \
            "Expected Cyclic Dependency for 3-module cycle"


# ---------------------------------------------------------------------------
# Unstable Dependency
# ---------------------------------------------------------------------------

class TestUnstableDependency:
    def test_detects_dependency_on_less_stable_module(self, architectural_smell_detector, tmp_path):
        # core is imported by 3 modules (instability 0.25) yet imports volatile,
        # which imports 5 modules and is imported only by core (instability 5/6 > 0.8)
        for i in range(3):
            (tmp_path / f"user_{i}.py").write_text("import core\n")
        (tmp_path / "core.py").write_text("import volatile\n")
        leaves = "\n".join(f"import leaf_{i}" for i in range(5))
        (tmp_path / "volatile.py").write_text(leaves + "\n")
        for i in range(5):
            (tmp_path / f"leaf_{i}.py").write_text("X = 1\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert [s.module_class for s in smells_named(
            architectural_smell_detector, "Unstable Dependency")] == ["core"]

    def test_entry_point_with_many_imports_not_flagged(self, architectural_smell_detector, tmp_path):
        # Regression: a top-level module that only imports others has instability 1.0,
        # which is expected for an entry point and is not an unstable dependency
        imports = "\n".join(f"import external_dep_{i}" for i in range(10))
        (tmp_path / "unstable_mod.py").write_text(f"{imports}\ndef func():\n    pass\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Unstable Dependency")

    def test_stable_module_not_flagged(self, architectural_smell_detector, tmp_path):
        # Module depended upon by many others → low instability
        (tmp_path / "stable.py").write_text("def utility(): return 1\n")
        for i in range(5):
            m = tmp_path / f"consumer_{i}.py"
            m.write_text(f"import stable\ndef func_{i}(): stable.utility()\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Unstable Dependency")


# ---------------------------------------------------------------------------
# Hub-like Dependency
# ---------------------------------------------------------------------------

class TestHubLikeDependency:
    def test_detects_hub_module(self, architectural_smell_detector, tmp_path):
        # hub is imported by 4 modules and imports 4 others: 8 connections in a
        # 9-module project, balanced in and out
        (tmp_path / "hub.py").write_text("".join(f"import dep_{i}\n" for i in range(4)))
        for i in range(4):
            (tmp_path / f"dep_{i}.py").write_text("X = 1\n")
            (tmp_path / f"client_{i}.py").write_text("import hub\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert [s.module_class for s in smells_named(
            architectural_smell_detector, "Hub-like Dependency")] == ["hub"]

    def test_widely_imported_library_not_hub(self, architectural_smell_detector, tmp_path):
        # Regression: a module that is only imported (fan-in, no fan-out) is a
        # stable library, not a hub
        (tmp_path / "hub_lib.py").write_text("def utility():\n    return 42\n")
        for i in range(12):
            (tmp_path / f"consumer_{i}.py").write_text(
                f"import hub_lib\n\ndef work_{i}():\n    return hub_lib.utility()\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Hub-like Dependency")


# ---------------------------------------------------------------------------
# Import resolution
# ---------------------------------------------------------------------------

class TestImportResolution:
    def test_external_imports_are_not_project_modules(self, architectural_smell_detector, tmp_path):
        # Regression: every import target used to stay in the module graph, and any
        # name starting with a stdlib module name (requests -> re) counted as stdlib
        (tmp_path / "app.py").write_text("import os\nimport requests\nimport helper\n")
        (tmp_path / "helper.py").write_text("X = 1\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        graph = architectural_smell_detector.module_dependencies
        assert sorted(graph.nodes()) == ["app", "helper"]
        assert list(graph.edges()) == [("app", "helper")]
        assert architectural_smell_detector.external_dependencies["app"] == {
            ("stdlib", "os"), ("third_party", "requests")}

    def test_relative_and_package_imports_resolve(self, architectural_smell_detector, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("from . import a\n")
        (pkg / "a.py").write_text("from .b import thing\n")
        (pkg / "b.py").write_text("from pkg import c\nthing = 1\n")
        (pkg / "c.py").write_text("X = 1\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert set(architectural_smell_detector.module_dependencies.edges()) == {
            ("pkg.__init__", "pkg.a"), ("pkg.a", "pkg.b"), ("pkg.b", "pkg.c")}

    def test_analyzing_a_package_dir_resolves_its_absolute_imports(
            self, architectural_smell_detector, tmp_path):
        # Regression: pointing the tool at a package dir made `from pkg import mod`
        # look like a third-party import, leaving the module graph without edges
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "a.py").write_text("from pkg import b\n")
        (pkg / "b.py").write_text("import pkg.a\n")
        architectural_smell_detector.detect_smells(str(pkg))
        assert set(architectural_smell_detector.module_dependencies.edges()) == {
            ("pkg.a", "pkg.b"), ("pkg.b", "pkg.a")}
        assert smells_named(architectural_smell_detector, "Cyclic Dependency")

    def test_type_checking_imports_ignored(self, architectural_smell_detector, tmp_path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text(
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import a\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(architectural_smell_detector, "Cyclic Dependency")

    def test_name_containing_excluded_word_still_checked(self, architectural_smell_detector, tmp_path):
        # Regression: 'base' in 'database' excluded the module from cycle detection
        (tmp_path / "database.py").write_text("import models\n")
        (tmp_path / "models.py").write_text("import database\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Cyclic Dependency")

    def test_unparsable_file_recorded_as_error(self, architectural_smell_detector, tmp_path):
        (tmp_path / "broken.py").write_text("def broken(:\n")
        (tmp_path / "ok.py").write_text("X = 1\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert [e["file"] for e in architectural_smell_detector.errors] == [
            str(tmp_path / "broken.py")]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_directory_no_crash(self, architectural_smell_detector, tmp_path):
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert architectural_smell_detector.architectural_smells == []


class TestReviewRegressions:
    def test_root_package_name_does_not_exclude_everything(self, architectural_smell_detector, tmp_path):
        # Regression: analyzing a package named utils/core made every module look like
        # an excluded utility module (its own name is the first dotted part)
        for root_name in ("mylib", "utils"):
            pkg = tmp_path / root_name
            pkg.mkdir()
            (pkg / "__init__.py").write_text("")
            (pkg / "a.py").write_text("X = 1\n")
            (pkg / "b.py").write_text("Y = 1\n")
            (pkg / "c.py").write_text(f"from {root_name} import a\n")
        found = {}
        for root_name in ("mylib", "utils"):
            detector = ArchitecturalSmellDetector(architectural_smell_detector.thresholds)
            detector.detect_smells(str(tmp_path / root_name))
            found[root_name] = sorted(s.module_class.split(".", 1)[1]
                                      for s in smells_named(detector, "Orphan Module"))
        assert found["mylib"] == found["utils"] == ["b"]

    def test_src_layout_package_import_resolves(self, architectural_smell_detector, tmp_path):
        pkg = tmp_path / "src" / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("api = 1\n")
        (pkg / "core.py").write_text("x = 1\n")
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_a.py").write_text("from pkg import api\nfrom pkg.core import x\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert set(architectural_smell_detector.module_dependencies.successors("tests.test_a")) == {
            "src.pkg.__init__", "src.pkg.core"}
        assert not architectural_smell_detector.external_dependencies["tests.test_a"]

    def test_relative_import_above_root_ignored(self, architectural_smell_detector, tmp_path):
        (tmp_path / "way.py").write_text("X = 1\n")
        (tmp_path / "a.py").write_text("from ...way import x\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert not architectural_smell_detector.module_dependencies.edges()

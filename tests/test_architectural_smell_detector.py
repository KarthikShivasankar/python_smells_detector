"""
Comprehensive tests for ArchitecturalSmellDetector.

Each test class targets one of the eight architectural smell detectors.
Tests write real Python files into tmp_path directories so the detector
exercises its actual file-parsing and graph-building logic.
"""


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
    def test_detects_unstable_module(self, architectural_smell_detector, tmp_path):
        # Module with many outgoing imports and no incoming → instability = 1.0 > 0.8
        imports = "\n".join(f"import external_dep_{i}" for i in range(10))
        f = tmp_path / "unstable_mod.py"
        f.write_text(f"{imports}\ndef func():\n    pass\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Unstable Dependency"), \
            "Expected Unstable Dependency for leaf module with no in-degree"

    def test_stable_module_not_flagged(self, architectural_smell_detector, tmp_path):
        # Module depended upon by many others → low instability
        (tmp_path / "stable.py").write_text("def utility(): return 1\n")
        for i in range(5):
            m = tmp_path / f"consumer_{i}.py"
            m.write_text(f"import stable\ndef func_{i}(): stable.utility()\n")
        architectural_smell_detector.detect_smells(str(tmp_path))
        stable_unstable = [
            s for s in architectural_smell_detector.architectural_smells
            if "Unstable" in s.name and "stable" in (s.module_class or "")
        ]
        assert not stable_unstable, \
            "A module that others depend on should not be flagged as unstable"


# ---------------------------------------------------------------------------
# Hub-like Dependency
# ---------------------------------------------------------------------------

class TestHubLikeDependency:
    def test_detects_hub_module(self, architectural_smell_detector, tmp_path):
        # Hub module with high fan-in (12 modules import it) and no fan-out.
        # fan_in_ratio >> fan_out_ratio → unbalanced → triggers Hub-like Dependency.
        (tmp_path / "hub_lib.py").write_text(
            "def utility():\n    return 42\n"
        )
        for i in range(12):
            m = tmp_path / f"consumer_{i}.py"
            m.write_text(
                f"import hub_lib\n\ndef work_{i}():\n    return hub_lib.utility()\n"
            )
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(architectural_smell_detector, "Hub-like Dependency"), \
            "Expected Hub-like Dependency for module imported by 12 others with no out-deps"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_directory_no_crash(self, architectural_smell_detector, tmp_path):
        architectural_smell_detector.detect_smells(str(tmp_path))
        assert architectural_smell_detector.architectural_smells == []

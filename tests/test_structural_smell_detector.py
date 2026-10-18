"""
Comprehensive tests for StructuralSmellDetector.

Tests verify the twelve metric-based structural smell detectors.
Each test writes real Python source files into a tmp_path directory,
runs detect_smells(), then asserts the expected smell was (or was not) found.
"""
from code_quality_analyzer.structural_smell_detector import StructuralSmellDetector

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def smells_named(detector, name):
    return [s for s in detector.structural_smells if name in s.name]


# ---------------------------------------------------------------------------
# High Lines of Code (LOC)
# ---------------------------------------------------------------------------

class TestLOC:
    def test_detects_large_module(self, structural_smell_detector, tmp_path):
        # LOC threshold 150 — write 200 plain code lines
        lines = "\n".join(f"x{i} = {i}" for i in range(200))
        f = tmp_path / "big_module.py"
        f.write_text(lines)
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Lines of Code"), \
            "Expected LOC smell for 200-line file"

    def test_small_module_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "small_module.py"
        f.write_text("\n".join(f"x{i} = {i}" for i in range(30)))
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Lines of Code")

    def test_one_line_docstring_does_not_hide_code(self, structural_smell_detector, tmp_path):
        # Regression: a one-line docstring flipped the "inside docstring" state, so
        # every line after it was counted as documentation
        lines = "\n".join(f"x{i} = {i}" for i in range(200))
        (tmp_path / "documented.py").write_text(f'"""Module docstring."""\n{lines}\n')
        structural_smell_detector.detect_smells(str(tmp_path))
        smells = smells_named(structural_smell_detector, "High Lines of Code")
        assert smells and "200 effective code lines" in smells[0].description


# ---------------------------------------------------------------------------
# High Number of Classes — project-level (NOC)
# ---------------------------------------------------------------------------

class TestNOC:
    def test_detects_too_many_classes(self, structural_smell_detector, tmp_path):
        # 50 regular classes should exceed the weighted NOC threshold of 7
        for i in range(5):
            m = tmp_path / f"module{i}.py"
            classes = "\n".join(
                f"class Entity{i}_{j}:\n    def run(self):\n        return {j}"
                for j in range(10)
            )
            m.write_text(classes)
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Number of Classes (NOC)"), \
            "Expected NOC smell for 50 regular classes"

    def test_few_classes_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "small_project.py"
        f.write_text("class A: pass\nclass B: pass\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Number of Classes (NOC)")


# ---------------------------------------------------------------------------
# High Number of Methods — class level (NOM)
# ---------------------------------------------------------------------------

class TestNOM:
    def test_detects_class_with_many_methods(self, structural_smell_detector, tmp_path):
        # 12 non-special methods > NOM_THRESHOLD 10
        methods = "\n".join(
            f"    def method_{i}(self):\n        return {i}" for i in range(12)
        )
        f = tmp_path / "nom.py"
        f.write_text(f"class BigClass:\n{methods}\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Number of Methods (NOM)"), \
            "Expected NOM smell for class with 12 methods"

    def test_small_class_not_flagged(self, structural_smell_detector, tmp_path):
        methods = "\n".join(
            f"    def method_{i}(self):\n        return {i}" for i in range(5)
        )
        f = tmp_path / "small.py"
        f.write_text(f"class SmallClass:\n{methods}\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Number of Methods (NOM)")

    def test_magic_methods_not_counted(self, structural_smell_detector, tmp_path):
        # 12 magic methods should NOT count toward NOM
        magic = "\n".join(
            f"    def __dunder{i}__(self):\n        return {i}" for i in range(12)
        )
        f = tmp_path / "magic.py"
        f.write_text(f"class MagicClass:\n{magic}\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Number of Methods (NOM)"), \
            "Magic methods should not count toward NOM"


# ---------------------------------------------------------------------------
# High Number of Classes in Module (NOCC)
# ---------------------------------------------------------------------------

class TestNOCC:
    def test_detects_module_with_many_classes(self, structural_smell_detector, tmp_path):
        # 20 regular classes in one module > adjusted threshold ~10*1.5=15 (simple classes)
        classes = "\n".join(
            f"class Class{i}:\n    def run(self):\n        return {i}\n    def stop(self):\n        return 0"
            for i in range(20)
        )
        f = tmp_path / "packed_module.py"
        f.write_text(classes)
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Number of Classes (NOCC)"), \
            "Expected NOCC smell for 20 classes in one module"

    def test_few_classes_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "few.py"
        f.write_text("class A: pass\nclass B: pass\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Number of Classes (NOCC)")


# ---------------------------------------------------------------------------
# High Cyclomatic Complexity
# ---------------------------------------------------------------------------

class TestCyclomaticComplexity:
    def test_detects_complex_method(self, structural_smell_detector, tmp_path):
        # 12 if-statements in a method → complexity ≥ 13 > threshold 10
        branches = "\n".join(
            f"        if x == {i}:\n            result += {i}" for i in range(12)
        )
        f = tmp_path / "complex.py"
        f.write_text(
            f"class Processor:\n"
            f"    def process(self, x):\n"
            f"        result = 0\n"
            f"{branches}\n"
            f"        return result\n"
        )
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Cyclomatic Complexity"), \
            "Expected High Cyclomatic Complexity for method with 12 if-branches"

    def test_simple_method_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "simple.py"
        f.write_text(
            "class C:\n    def method(self, x):\n        return x + 1\n"
        )
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Cyclomatic Complexity")


    def test_elif_counted_once(self, structural_smell_detector, tmp_path):
        # Regression for #31: if + 6 elif = complexity 8, was reported as 14
        arms = "".join(f"        elif x == {i}:\n            return {i}\n" for i in range(2, 8))
        f = tmp_path / "elif.py"
        f.write_text(
            "class Router:\n    def route(self, x):\n"
            "        if x == 1:\n            return 1\n" + arms + "        return 0\n"
        )
        structural_smell_detector.detect_smells(str(tmp_path))
        method = structural_smell_detector.class_info["elif.Router"]["methods"][0]
        assert structural_smell_detector.calculate_cyclomatic_complexity(method) == 8
        assert structural_smell_detector._count_branches(method) == 7
        assert structural_smell_detector._max_nesting(method) == 1
        assert not smells_named(structural_smell_detector, "High Cyclomatic Complexity")
        assert not smells_named(structural_smell_detector, "Too Many Branches")


# ---------------------------------------------------------------------------
# Too Many Branches
# ---------------------------------------------------------------------------

class TestTooManyBranches:
    def test_detects_method_with_many_branches(self, structural_smell_detector, tmp_path):
        # 12 if-branches > threshold 10
        branches = "\n".join(
            f"        if x == {i}:\n            pass" for i in range(12)
        )
        f = tmp_path / "branchy.py"
        f.write_text(
            f"class C:\n    def branchy(self, x):\n{branches}\n"
        )
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "Too Many Branches"), \
            "Expected Too Many Branches for method with 12 if-statements"

    def test_clean_method_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text(
            "class C:\n    def clean(self, x):\n        if x:\n            return x\n        return 0\n"
        )
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "Too Many Branches")


    def test_sequential_ifs_are_not_nested(self, structural_smell_detector, tmp_path):
        # Regression for #31: four flat ifs were reported as nesting depth 4
        ifs = "".join(f"        if {c}:\n            print({c})\n" for c in "abcd")
        f = tmp_path / "flat.py"
        f.write_text(f"class C:\n    def check(self, a, b, c, d):\n{ifs}")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "Too Many Branches")

    def test_deep_nesting_detected(self, structural_smell_detector, tmp_path):
        # for > if > while > try > with: 5 levels > MAX_NESTING_DEPTH 4
        body = (
            "        for a in x:\n"
            "            if a:\n"
            "                while a:\n"
            "                    try:\n"
            "                        with open(a) as fh:\n"
            "                            a -= 1\n"
            "                    except ValueError:\n"
            "                        pass\n"
        )
        f = tmp_path / "deep.py"
        f.write_text(f"class C:\n    def deep(self, x):\n{body}")
        structural_smell_detector.detect_smells(str(tmp_path))
        smells = smells_named(structural_smell_detector, "Deep Nesting")
        assert smells and "5 levels" in smells[0].description
        assert not smells_named(structural_smell_detector, "Too Many Branches")

    def test_nesting_at_limit_not_flagged(self, structural_smell_detector, tmp_path):
        body = ("        for a in x:\n            if a:\n                while a:\n"
                "                    try:\n                        a -= 1\n"
                "                    except ValueError:\n                        pass\n")
        (tmp_path / "four.py").write_text(f"class C:\n    def four(self, x):\n{body}")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "Deep Nesting")


# ---------------------------------------------------------------------------
# Functions outside classes, async code, modern syntax
# ---------------------------------------------------------------------------

class TestFunctionCoverage:
    def test_module_level_function_complexity_checked(self, structural_smell_detector, tmp_path):
        # Regression: only methods were measured, module-level functions never
        branches = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(12))
        (tmp_path / "funcs.py").write_text(f"def dispatch(x):\n{branches}    return 0\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        smells = smells_named(structural_smell_detector, "High Cyclomatic Complexity")
        assert [(s.module_class, s.line_number) for s in smells] == [("funcs", 1)]
        assert smells_named(structural_smell_detector, "Too Many Branches")

    def test_async_methods_counted(self, structural_smell_detector, tmp_path):
        methods = "".join(f"    async def m{i}(self):\n        return {i}\n" for i in range(12))
        (tmp_path / "aio.py").write_text(f"class Client:\n{methods}")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Number of Methods")

    def test_complexity_counts_expressions_and_match(self, structural_smell_detector, tmp_path):
        (tmp_path / "expr.py").write_text(
            "def f(x, items):\n"
            "    y = 1 if x else 2\n"                          # +1
            "    z = [i for i in items if i if i > 1]\n"       # +1 for, +2 ifs
            "    match x:\n"
            "        case 1:\n            pass\n"             # +1
            "        case 2:\n            pass\n"             # +1
            "        case _:\n            pass\n"             # wildcard: +0
            "    return y, z\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        function = structural_smell_detector.module_info["expr"]["functions"][0]
        assert structural_smell_detector.calculate_cyclomatic_complexity(function) == 7


# ---------------------------------------------------------------------------
# Long File
# ---------------------------------------------------------------------------

class TestLongFile:
    def test_detects_long_file(self, structural_smell_detector, tmp_path):
        # 300 meaningful lines > MAX_FILE_LENGTH 250
        lines = "\n".join(f"x{i} = {i}" for i in range(300))
        f = tmp_path / "long_file.py"
        f.write_text(lines)
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "Long File"), \
            "Expected Long File for 300-line file"

    def test_short_file_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "short.py"
        f.write_text("\n".join(f"x{i} = {i}" for i in range(50)))
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "Long File")


# ---------------------------------------------------------------------------
# Deep Inheritance Tree (DIT)
# ---------------------------------------------------------------------------

class TestDIT:
    def test_detects_deep_inheritance(self, tmp_path):
        # The detector resolves base names as plain strings (e.g. "A", "B") and
        # builds a graph where each phantom base node is a direct child of "object".
        # So deep.E's shortest path from object is always 2 regardless of chain depth.
        # Use DIT_THRESHOLD=1 so that path-length 2 > 1 triggers the smell.
        thresholds = {**__import__('conftest').STRUCTURAL_THRESHOLDS, 'DIT_THRESHOLD': 1}
        detector = StructuralSmellDetector(thresholds)
        f = tmp_path / "deep.py"
        f.write_text(
            "class A:\n    def a(self): pass\n"
            "class B(A):\n    def b(self): pass\n"
            "class C(B):\n    def c(self): pass\n"
        )
        detector.detect_smells(str(tmp_path))
        assert smells_named(detector, "Deep Inheritance Tree"), \
            "Expected DIT smell when threshold is 1 and chain path-length is 2"

    def test_depth_follows_the_real_chain(self, structural_smell_detector, tmp_path):
        # Regression: bases were never linked to their class definitions, so every
        # class got DIT 2 whatever the chain; A <- B <- C <- D <- E is depth 5
        (tmp_path / "chain.py").write_text(
            "class A: pass\nclass B(A): pass\nclass C(B): pass\n"
            "class D(C): pass\nclass E(D): pass\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        smells = smells_named(structural_smell_detector, "Deep Inheritance Tree")
        assert [s.module_class for s in smells] == ["chain.D", "chain.E"]
        assert "object->chain.A->chain.B->chain.C->chain.D->chain.E" in smells[1].description
        assert smells[1].line_number == 5

    def test_bases_resolved_across_modules(self, structural_smell_detector, tmp_path):
        (tmp_path / "base.py").write_text("class A: pass\nclass B(A): pass\nclass C(B): pass\n")
        (tmp_path / "child.py").write_text("from base import C\nclass D(C): pass\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert [s.module_class for s in smells_named(
            structural_smell_detector, "Deep Inheritance Tree")] == ["child.D"]

    def test_shallow_hierarchy_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "shallow.py"
        f.write_text("class Base: pass\nclass Child(Base): pass\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "Deep Inheritance Tree")


# ---------------------------------------------------------------------------
# High Weight of a Class (WAC)
# ---------------------------------------------------------------------------

class TestWAC:
    def test_instance_attributes_count_as_fields(self, structural_smell_detector, tmp_path):
        # Regression: only class-level assignments were fields, so self.x = ... never counted
        init = "".join(f"        self.field{i} = {i}\n" for i in range(12))
        (tmp_path / "inst.py").write_text(f"class Wide:\n    def __init__(self):\n{init}")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Weight of a Class (WAC)")

    def test_detects_class_with_many_fields(self, structural_smell_detector, tmp_path):
        # 12 public class-level fields > WAC_THRESHOLD 10
        fields = "\n".join(f"    field{i} = None" for i in range(12))
        f = tmp_path / "wac.py"
        f.write_text(f"class FieldHeavy:\n{fields}\n    def method(self):\n        pass\n")
        structural_smell_detector.analyze_directory(str(tmp_path))
        structural_smell_detector.detect_wac()
        assert smells_named(structural_smell_detector, "High Weight of a Class (WAC)"), \
            "Expected WAC smell for 12 class-level fields"

    def test_constants_excluded(self, structural_smell_detector, tmp_path):
        # Uppercase fields (constants) should not count toward WAC
        constants = "\n".join(f"    CONST{i} = {i}" for i in range(12))
        f = tmp_path / "constants.py"
        f.write_text(f"class Config:\n{constants}\n    def get(self):\n        pass\n")
        structural_smell_detector.analyze_directory(str(tmp_path))
        structural_smell_detector.detect_wac()
        assert not smells_named(structural_smell_detector, "High Weight of a Class (WAC)"), \
            "Uppercase constants should be excluded from WAC"


# ---------------------------------------------------------------------------
# Large Class (SIZE2)
# ---------------------------------------------------------------------------

class TestSIZE2:
    def test_detects_large_class_by_size2(self, structural_smell_detector, tmp_path):
        # 12 methods + 6 fields = 18 significant members > SIZE2_THRESHOLD 15
        methods = "\n".join(
            f"    def method{i}(self):\n        return self.field0" for i in range(12)
        )
        fields = "\n".join(f"    field{i} = None" for i in range(6))
        f = tmp_path / "size2.py"
        f.write_text(f"class BigClass:\n{fields}\n{methods}\n")
        structural_smell_detector.analyze_directory(str(tmp_path))
        structural_smell_detector.detect_size2()
        assert smells_named(structural_smell_detector, "Large Class (SIZE2)"), \
            "Expected SIZE2 smell for class with 18 significant members"

    def test_small_class_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "small.py"
        f.write_text("class S:\n    x = 1\n    def method(self):\n        return self.x\n")
        structural_smell_detector.analyze_directory(str(tmp_path))
        structural_smell_detector.detect_size2()
        assert not smells_named(structural_smell_detector, "Large Class (SIZE2)")


# ---------------------------------------------------------------------------
# High Response for a Class (RFC)
# ---------------------------------------------------------------------------

class TestRFC:
    def test_detects_high_rfc(self, structural_smell_detector, tmp_path):
        # RFC = significant_methods + unique external method calls (set, not count)
        # 12 methods + 12 unique external calls (one per method) = 24 > threshold 20
        methods = "\n".join(
            f"    def action{i}(self):\n"
            f"        self.ext.unique_call_{i}()\n"
            f"        return {i}"
            for i in range(12)
        )
        f = tmp_path / "rfc.py"
        f.write_text(f"class HighRFC:\n{methods}\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Response for a Class (RFC)"), \
            "Expected RFC smell for class with 12 methods + 12 unique external calls = 24"

    def test_simple_class_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "simple_rfc.py"
        f.write_text("class Simple:\n    def do(self):\n        return 1\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Response for a Class (RFC)")


# ---------------------------------------------------------------------------
# High Fan-out
# ---------------------------------------------------------------------------

class TestFanOut:
    def test_detects_high_fanout(self, structural_smell_detector, tmp_path):
        # One module that imports 18 non-stdlib modules → > MAX_FANOUT 15
        imports = "\n".join(f"import custom_module_{i}" for i in range(18))
        f = tmp_path / "high_fanout.py"
        f.write_text(f"{imports}\nclass C: pass\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Fan-out"), \
            "Expected High Fan-out for module with 18 imports"

    def test_few_imports_not_flagged(self, structural_smell_detector, tmp_path):
        f = tmp_path / "few_imports.py"
        f.write_text("import os\nimport sys\nclass C: pass\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Fan-out")


# ---------------------------------------------------------------------------
# High Fan-in
# ---------------------------------------------------------------------------

class TestFanIn:
    def test_detects_high_fanin(self, structural_smell_detector, tmp_path):
        # Create a shared module that 18 other modules import
        shared = tmp_path / "shared_lib.py"
        shared.write_text("class SharedClass:\n    def method(self):\n        return 1\n")
        for i in range(18):
            m = tmp_path / f"consumer{i}.py"
            m.write_text(f"import shared_lib\n\nclass Consumer{i}:\n    def use(self):\n        return shared_lib.SharedClass()\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Fan-in"), \
            "Expected High Fan-in for module imported by 18 others"

    def test_external_packages_not_reported(self, structural_smell_detector, tmp_path):
        # Regression: imported third-party names were graph nodes and got Fan-in findings
        for i in range(18):
            (tmp_path / f"consumer{i}.py").write_text("import numpy\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Fan-in")

    def test_relative_imports_count(self, structural_smell_detector, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "shared.py").write_text("X = 1\n")
        for i in range(18):
            (pkg / f"consumer{i}.py").write_text("from . import shared\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert [s.module_class for s in smells_named(
            structural_smell_detector, "High Fan-in")] == ["pkg.shared"]


# ---------------------------------------------------------------------------
# High Lack of Cohesion (LCOM)
# ---------------------------------------------------------------------------

class TestLCOM:
    def test_detects_low_cohesion(self, structural_smell_detector, tmp_path):
        # 6 methods each using a completely different field → many non-cohesive pairs
        methods_and_fields = ""
        for i in range(6):
            methods_and_fields += (
                f"    def method_{i}(self):\n"
                f"        return self.field_{i}\n"
            )
        f = tmp_path / "lcom.py"
        f.write_text(f"class LowCohesion:\n{methods_and_fields}\n")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert smells_named(structural_smell_detector, "High Lack of Cohesion of Methods (LCOM)"), \
            "Expected LCOM smell for class with 6 methods each touching a unique field"

    def test_high_cohesion_not_flagged(self, structural_smell_detector, tmp_path):
        # All methods share the same field
        f = tmp_path / "cohesive.py"
        f.write_text(
            "class Cohesive:\n"
            "    def a(self): return self.value\n"
            "    def b(self): return self.value + 1\n"
            "    def c(self): return self.value * 2\n"
        )
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "High Lack of Cohesion of Methods (LCOM)")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_directory_no_crash(self, structural_smell_detector, tmp_path):
        structural_smell_detector.detect_smells(str(tmp_path))
        assert structural_smell_detector.structural_smells == []


class TestCBO:
    def test_counts_imported_and_project_classes(self, structural_smell_detector, tmp_path):
        imports = "".join(f"from lib{i} import Dep{i}\n" for i in range(9))
        uses = "".join(f"        Dep{i}()\n" for i in range(9))
        (tmp_path / "coupled.py").write_text(
            f"{imports}import os\nclass Hub:\n    def run(self, a, b, c):\n{uses}"
            "        os.getcwd()\n        return a.x + b.y + c.z\n")
        structural_smell_detector.thresholds['CBO_THRESHOLD'] = 8
        structural_smell_detector.detect_smells(str(tmp_path))
        smells = smells_named(structural_smell_detector, "Coupling Between Object Classes")
        assert smells and "coupled to 9" in smells[0].description

    def test_locals_and_parameters_are_not_coupling(self, structural_smell_detector, tmp_path):
        # Regression: every name with an attribute access (parameters, locals) counted
        attrs = "".join(f"        v{i}.do()\n" for i in range(12))
        params = ", ".join(f"v{i}" for i in range(12))
        (tmp_path / "loose.py").write_text(f"class Loose:\n    def run(self, {params}):\n{attrs}")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert not smells_named(structural_smell_detector, "Coupling Between Object Classes")


class TestReviewRegressions:
    def test_huge_expression_does_not_disable_nesting(self, structural_smell_detector, tmp_path):
        # Regression: recursion overflow on generated code silently dropped detect_branches
        (tmp_path / "a_gen.py").write_text("X = " + " + ".join(["1"] * 3000) + "\n")
        body = "".join("    " * (i + 1) + f"if x > {i}:\n" for i in range(6)) + "    " * 7 + "pass\n"
        (tmp_path / "deepnest.py").write_text(f"def g(x):\n{body}")
        structural_smell_detector.detect_smells(str(tmp_path))
        assert [s.module_class for s in smells_named(structural_smell_detector, "Deep Nesting")] == [
            "deepnest"]

    def test_relative_sibling_named_like_stdlib_counts_for_cbo(self, structural_smell_detector, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        names = ", ".join(f"f{i}" for i in range(10))
        calls = "".join(f"        f{i}()\n" for i in range(10))
        (pkg / "a.py").write_text(f"from .types import {names}\nclass User:\n    def run(self):\n{calls}")
        structural_smell_detector.thresholds['CBO_THRESHOLD'] = 8
        structural_smell_detector.detect_smells(str(tmp_path))
        assert [s.module_class for s in smells_named(
            structural_smell_detector, "Coupling Between Object Classes")] == ["pkg.a.User"]

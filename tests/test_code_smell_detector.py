"""
Comprehensive tests for CodeSmellDetector.

Each test class covers one detection method. Positive tests verify that the
smell IS detected when the code clearly violates the threshold; negative tests
verify that clean code does NOT trigger a false positive.
"""
import pytest

from code_quality_analyzer.code_smell_detector import CodeSmellDetector

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def smells_named(detector, name):
    """Return all smells whose name contains *name*."""
    return [s for s in detector.code_smells if name in s.name]


# ---------------------------------------------------------------------------
# Long Method
# ---------------------------------------------------------------------------

class TestLongMethod:
    def test_detects_method_over_threshold(self, code_smell_detector, tmp_path):
        # 48 non-empty, non-comment lines inside the function body (> 45 threshold)
        body = "\n".join(f"    x{i} = {i}" for i in range(48))
        code = f"def big_func():\n{body}\n"
        f = tmp_path / "long_method.py"
        f.write_text(code)
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Long Method"), \
            "Expected 'Long Method' smell for a 48-line function"

    def test_clean_method_not_flagged(self, code_smell_detector, tmp_path):
        body = "\n".join(f"    x{i} = {i}" for i in range(10))
        f = tmp_path / "short_method.py"
        f.write_text(f"def short_func():\n{body}\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Long Method"), \
            "Short function should not be flagged as Long Method"

    def test_property_not_flagged(self, code_smell_detector, tmp_path):
        # Body lines must be double-indented (inside class + inside method)
        body = "\n".join(f"        x{i} = {i}" for i in range(48))
        code = f"class C:\n    @property\n    def val(self):\n{body}\n        return 1\n"
        f = tmp_path / "prop.py"
        f.write_text(code)
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Long Method"), \
            "Property methods should not be flagged"

    def test_comments_not_counted(self, code_smell_detector, tmp_path):
        # 48 lines but 40 of them are comments → should NOT trigger
        comments = "\n".join(f"    # comment {i}" for i in range(40))
        code_lines = "\n".join(f"    x{i} = {i}" for i in range(8))
        f = tmp_path / "commented.py"
        f.write_text(f"def func():\n{comments}\n{code_lines}\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Long Method"), \
            "Comment lines should not count toward long-method threshold"


# ---------------------------------------------------------------------------
# Large Class
# ---------------------------------------------------------------------------

class TestLargeClass:
    def test_detects_class_with_many_methods(self, code_smell_detector, tmp_path):
        # 16 non-trivial methods (> 15 threshold)
        methods = "\n".join(
            f"    def method{i}(self):\n        self.x = {i}\n        return self.x"
            for i in range(16)
        )
        f = tmp_path / "large_class.py"
        f.write_text(f"class BigClass:\n{methods}\n")
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Large Class"), \
            "Expected 'Large Class' smell for a class with 16 non-trivial methods"

    def test_small_class_not_flagged(self, code_smell_detector, tmp_path):
        methods = "\n".join(
            f"    def method{i}(self):\n        return {i}"
            for i in range(5)
        )
        f = tmp_path / "small_class.py"
        f.write_text(f"class SmallClass:\n{methods}\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Large Class")

    def test_dataclass_not_flagged(self, code_smell_detector, tmp_path):
        methods = "\n".join(
            f"    def method{i}(self):\n        self.x = {i}\n        return self.x"
            for i in range(16)
        )
        f = tmp_path / "dataclass.py"
        f.write_text(f"from dataclasses import dataclass\n\n@dataclass\nclass BigDataClass:\n{methods}\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Large Class"), \
            "Dataclasses should not be flagged"

    def test_exception_class_not_flagged(self, code_smell_detector, tmp_path):
        methods = "\n".join(
            f"    def method{i}(self):\n        self.x = {i}\n        return self.x"
            for i in range(16)
        )
        f = tmp_path / "exc_class.py"
        f.write_text(f"class MyException(Exception):\n{methods}\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Large Class"), \
            "Exception classes should not be flagged"


# ---------------------------------------------------------------------------
# Primitive Obsession
# ---------------------------------------------------------------------------

class TestPrimitiveObsession:
    def test_detects_many_typed_primitives(self, code_smell_detector, tmp_path):
        # 5 typed primitive args > threshold of 4 and > 70 % of total
        f = tmp_path / "prim.py"
        f.write_text(
            "def func(a: int, b: str, c: float, d: bool, e: int): pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Primitive Obsession"), \
            "Expected Primitive Obsession for 5 typed primitive params"

    def test_object_params_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "obj_params.py"
        f.write_text(
            "def func(a: MyClass, b: AnotherClass, c: ThirdClass, d: FourthClass, e: FifthClass): pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Primitive Obsession"), \
            "Object-type params should not trigger Primitive Obsession"

    def test_few_params_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "few_params.py"
        f.write_text("def func(a: int, b: str, c: float): pass\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Primitive Obsession"), \
            "<=3 params skipped per detector logic"


# ---------------------------------------------------------------------------
# Long Parameter List
# ---------------------------------------------------------------------------

class TestLongParameterList:
    def test_detects_too_many_params(self, code_smell_detector, tmp_path):
        # 7 params excluding self (> threshold 5, not __init__)
        f = tmp_path / "long_params.py"
        f.write_text(
            "def my_func(a, b, c, d, e, f, g): pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Long Parameter List"), \
            "Expected Long Parameter List for 7 params"

    def test_init_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "init_params.py"
        f.write_text(
            "class C:\n    def __init__(self, a, b, c, d, e, f, g): pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Long Parameter List"), \
            "__init__ is excluded from long-parameter-list check"

    def test_varargs_raises_threshold(self, code_smell_detector, tmp_path):
        # With *args threshold becomes 5+2=7; exactly 7 non-self params should NOT trigger
        f = tmp_path / "varargs.py"
        f.write_text(
            "def my_func(a, b, c, d, e, f, g, *args): pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        # 7 params with *args → threshold is 7, so len(args)=7 is NOT > 7
        assert not smells_named(code_smell_detector, "Long Parameter List"), \
            "varargs should raise the threshold by 2"

    def test_clean_function_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text("def func(a, b, c): pass\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Long Parameter List")


# ---------------------------------------------------------------------------
# Switch Statements (complex conditionals)
# ---------------------------------------------------------------------------

class TestSwitchStatements:
    def test_detects_complex_nested_conditions(self, tmp_path):
        # detect_switch_statements counts If nodes directly inside node.orelse.
        # Threshold COMPLEX_CONDITIONAL=3 → need count > 3 (i.e. >=4 If siblings).
        # Also must NOT be a guard clause (body > 2 lines OR non-Compare test).
        detector = CodeSmellDetector({**__import__('conftest').CODE_SMELL_THRESHOLDS,
                                      'COMPLEX_CONDITIONAL': 1})
        # Outer if: body has 3 statements (not guard clause), orelse has 3 If nodes → count=4 > 1
        f = tmp_path / "switch.py"
        f.write_text(
            "def func(flag, a, b, c, d):\n"
            "    if flag:\n"
            "        x = 1\n"
            "        y = 2\n"
            "        z = 3\n"
            "    else:\n"
            "        if a:\n            x = 10\n"
            "        if b:\n            x = 20\n"
            "        if c:\n            x = 30\n"
            "        if d:\n            x = 40\n"
        )
        detector.detect_smells(str(f))
        assert smells_named(detector, "Switch Statements"), \
            "Expected Switch Statements for if with 4 If nodes in orelse"

    def test_simple_if_else_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "simple_if.py"
        f.write_text(
            "def func(x):\n"
            "    if x > 0:\n        return 'pos'\n"
            "    else:\n        return 'neg'\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Switch Statements")


# ---------------------------------------------------------------------------
# Temporary Field
# ---------------------------------------------------------------------------

class TestTemporaryField:
    def test_detects_unused_init_fields(self, code_smell_detector, tmp_path):
        # 3 self.xxx fields set in __init__ and never read by another method (>= threshold 3)
        f = tmp_path / "temp_field.py"
        f.write_text(
            "class C:\n"
            "    def __init__(self):\n"
            "        self.title = 'r'\n"
            "        self.alpha = None\n"
            "        self.beta = None\n"
            "        self.gamma = None\n"
            "    def method(self):\n"
            "        return self.title\n"
        )
        code_smell_detector.detect_smells(str(f))
        smells = smells_named(code_smell_detector, "Temporary Field")
        assert len(smells) == 1
        assert "title" not in smells[0].description

    def test_all_fields_used_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "all_used.py"
        f.write_text(
            "class C:\n"
            "    def __init__(self):\n"
            "        self.value = setup()\n"
            "    def method(self):\n"
            "        return self.value\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Temporary Field")

    def test_params_and_locals_are_not_fields(self, code_smell_detector, tmp_path):
        # Regression for #19: parameters passed to super() and local variables used
        # to be reported as fields (including 'self').
        f = tmp_path / "params.py"
        f.write_text(
            "class Binner(Base):\n"
            "    def __init__(self, bins, precision, verbose):\n"
            "        super().__init__(precision, verbose)\n"
            "        scale = setup()\n"
            "        self.bins = bins * scale\n"
            "    def fit(self, data):\n"
            "        return data[: self.bins]\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Temporary Field")


# ---------------------------------------------------------------------------
# Divergent Change
# ---------------------------------------------------------------------------

class TestDivergentChange:
    def test_detects_many_method_prefixes(self, code_smell_detector, tmp_path):
        # 6 distinct non-CRUD prefixes and > 5 methods total
        methods = (
            "    def send_email(self):\n        x = 1\n        return x\n"
            "    def render_template(self):\n        x = 1\n        return x\n"
            "    def parse_input(self):\n        x = 1\n        return x\n"
            "    def compute_result(self):\n        x = 1\n        return x\n"
            "    def log_event(self):\n        x = 1\n        return x\n"
            "    def format_output(self):\n        x = 1\n        return x\n"
        )
        f = tmp_path / "divergent.py"
        f.write_text(f"class Multi:\n{methods}")
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Divergent Change"), \
            "Expected Divergent Change for class with 6 different method prefixes"

    def test_single_responsibility_not_flagged(self, code_smell_detector, tmp_path):
        methods = "\n".join(
            f"    def process_step{i}(self):\n        return {i}" for i in range(6)
        )
        f = tmp_path / "single_resp.py"
        f.write_text(f"class Processor:\n{methods}\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Divergent Change")


# ---------------------------------------------------------------------------
# Shotgun Surgery
# ---------------------------------------------------------------------------

class TestShotgunSurgery:
    def test_detects_method_called_in_many_contexts(self, code_smell_detector, tmp_path):
        # common_op called from 7 different top-level functions (>5 calls, >3 contexts)
        funcs = "\n".join(
            f"def func{i}():\n    common_op()" for i in range(7)
        )
        f = tmp_path / "shotgun.py"
        f.write_text(funcs)
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Shotgun Surgery"), \
            "Expected Shotgun Surgery for method called across 7 contexts"

    def test_infrequent_call_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text(
            "def a():\n    helper()\n"
            "def b():\n    helper()\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Shotgun Surgery")


# ---------------------------------------------------------------------------
# Feature Envy
# ---------------------------------------------------------------------------

class TestFeatureEnvy:
    def test_detects_excessive_external_calls(self, code_smell_detector, tmp_path):
        # method makes 5 calls to 'other' and 0 local calls → external > 3 AND > 2x local
        f = tmp_path / "feature_envy.py"
        f.write_text(
            "class MyClass:\n"
            "    def my_method(self):\n"
            "        x = other.do_a()\n"
            "        y = other.do_b()\n"
            "        z = other.do_c()\n"
            "        w = other.do_d()\n"
            "        return other.do_e()\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Feature Envy"), \
            "Expected Feature Envy for method making 5 calls to external object"

    def test_module_access_not_flagged(self, code_smell_detector, tmp_path):
        # Regression for #20: calls on imported modules are not envy of another object
        f = tmp_path / "modules.py"
        f.write_text(
            "import math\n"
            "import os.path\n"
            "import numpy as np\n"
            "from os import path as p\n"
            "class Stats:\n"
            "    def summary(self):\n"
            "        a = math.fsum(self.values)\n"
            "        b = math.sqrt(a) + math.floor(a) + math.ceil(a)\n"
            "        c = np.mean(a) + np.std(a) + np.min(a) + np.max(a)\n"
            "        d = os.sep + os.sep + os.sep + os.sep\n"
            "        return p.join(p.sep, p.sep, p.sep, p.sep), b, c, d\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Feature Envy")

    def test_balanced_calls_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "balanced.py"
        f.write_text(
            "class MyClass:\n"
            "    def my_method(self):\n"
            "        self.a()\n"
            "        self.b()\n"
            "        self.c()\n"
            "        other.do()\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Feature Envy")


# ---------------------------------------------------------------------------
# Message Chains
# ---------------------------------------------------------------------------

class TestMessageChains:
    def test_detects_long_chain(self, code_smell_detector, tmp_path):
        # chain of 5 attributes > threshold 3
        f = tmp_path / "chain.py"
        f.write_text(
            "def func():\n"
            "    result = obj.level1.level2.level3.level4.value\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Message Chains"), \
            "Expected Message Chains for 5-level attribute chain"

    def test_short_chain_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "short_chain.py"
        f.write_text("def func():\n    x = obj.attr.value\n")
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Message Chains")


# ---------------------------------------------------------------------------
# Middle Man
# ---------------------------------------------------------------------------

class TestMiddleMan:
    def test_detects_pure_delegation(self, code_smell_detector, tmp_path):
        # 4 out of 5 methods just delegate → ratio 0.8 > threshold 0.5
        f = tmp_path / "middleman.py"
        f.write_text(
            "class MiddleMan:\n"
            "    def __init__(self):\n"
            "        self._real = RealClass()\n"
            "    def alpha(self): return self._real.alpha()\n"
            "    def beta(self):  return self._real.beta()\n"
            "    def gamma(self): return self._real.gamma()\n"
            "    def delta(self): return self._real.delta()\n"
            "    def epsilon(self): return self._real.epsilon()\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Middle Man"), \
            "Expected Middle Man for class delegating 5/5 methods"

    def test_function_calls_and_self_calls_not_delegation(self, code_smell_detector, tmp_path):
        # Regression for #23: 'return len(...)' crashed the analysis (max() of an empty
        # dict) and 'return self._helper()' counted as delegation to self
        f = tmp_path / "not_middleman.py"
        f.write_text(
            "class Basket:\n"
            "    def __init__(self, items):\n"
            "        self.items = items\n"
            "    def count(self): return len(self.items)\n"
            "    def total(self): return sum(self.items)\n"
            "    def biggest(self): return max(self.items)\n"
            "    def smallest(self): return min(self.items)\n"
            "class Pricing:\n"
            "    def __init__(self, rate):\n"
            "        self.rate = rate\n"
            "    def net(self, x): return self._apply(x, 1)\n"
            "    def gross(self, x): return self._apply(x, 2)\n"
            "    def half(self, x): return self._apply(x, 0.5)\n"
            "    def _apply(self, x, f):\n"
            "        value = x * f\n"
            "        return round(value, 2)\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Middle Man")

    def test_proxy_class_not_flagged(self, code_smell_detector, tmp_path):
        # Classes ending in Proxy are explicitly excluded
        f = tmp_path / "proxy.py"
        f.write_text(
            "class ServiceProxy:\n"
            "    def a(self): return self._s.a()\n"
            "    def b(self): return self._s.b()\n"
            "    def c(self): return self._s.c()\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Middle Man"), \
            "Proxy classes are excluded from Middle Man detection"


# ---------------------------------------------------------------------------
# Speculative Generality
# ---------------------------------------------------------------------------

class TestSpeculativeGenerality:
    def test_detects_many_pass_methods(self, code_smell_detector, tmp_path):
        # 4 pass methods >= SPECULATIVE_GENERALITY_THRESHOLD (4)
        methods = "\n".join(
            f"    def hook{i}(self):\n        pass" for i in range(4)
        )
        f = tmp_path / "speculative.py"
        f.write_text(f"class Framework:\n{methods}\n")
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Speculative Generality"), \
            "Expected Speculative Generality for 4 pass methods"

    def test_abc_class_not_flagged(self, code_smell_detector, tmp_path):
        # Classes inheriting ABC are legitimately abstract
        methods = "\n".join(
            f"    def hook{i}(self):\n        pass" for i in range(4)
        )
        f = tmp_path / "abc_class.py"
        f.write_text(
            f"from abc import ABC\n\nclass MyABC(ABC):\n{methods}\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Speculative Generality"), \
            "ABC subclasses should not be flagged"


# ---------------------------------------------------------------------------
# Data Clumps
# ---------------------------------------------------------------------------

class TestDataClumps:
    def test_detects_repeated_parameter_group(self, code_smell_detector, tmp_path):
        # Same 6 params appear in two functions
        f = tmp_path / "data_clumps.py"
        f.write_text(
            "def create(host, port, username, password, database, timeout): pass\n"
            "def connect(host, port, username, password, database, timeout): pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Data Clumps"), \
            "Expected Data Clumps for same 6 params in two functions"

    def test_short_params_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "no_clump.py"
        f.write_text(
            "def a(x, y): pass\n"
            "def b(x, y): pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Data Clumps")

    def test_reports_only_maximal_group(self, code_smell_detector, tmp_path):
        # 10 shared params used to yield C(10,6)+...+C(10,10) = 386 subset findings
        params = ", ".join(f"p{i}" for i in range(10))
        f = tmp_path / "wide.py"
        f.write_text(f"def f1({params}): pass\ndef f2({params}): pass\n")
        code_smell_detector.detect_smells(str(f))
        assert len(smells_named(code_smell_detector, "Data Clumps")) == 1

    def test_distinct_maximal_groups_reported_separately(self, code_smell_detector, tmp_path):
        # f1/f2 share 8 params; f3 shares only 6 of them with both
        f = tmp_path / "nested.py"
        f.write_text(
            "def f1(a, b, c, d, e, g, h, i): pass\n"
            "def f2(a, b, c, d, e, g, h, i): pass\n"
            "def f3(a, b, c, d, e, g, x, y): pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        found = sorted(s.module_class for s in smells_named(code_smell_detector, "Data Clumps"))
        assert found == ["f1, f2", "f1, f2, f3"]

    def test_cross_file_clump_replaces_file_finding(self, code_smell_detector, tmp_path):
        params = ", ".join(f"p{i}" for i in range(6))
        a = tmp_path / "a.py"
        a.write_text(f"def f1({params}): pass\ndef f2({params}): pass\n")
        b = tmp_path / "b.py"
        b.write_text(f"def g({params}): pass\n")
        code_smell_detector.detect_smells(str(a))
        code_smell_detector.detect_smells(str(b))
        code_smell_detector.detect_cross_file_smells()
        clumps = smells_named(code_smell_detector, "Data Clumps")
        assert len(clumps) == 1
        assert clumps[0].module_class == "f1, f2, g"


# ---------------------------------------------------------------------------
# Excessive Comments
# ---------------------------------------------------------------------------

class TestExcessiveComments:
    def test_detects_high_comment_ratio(self, code_smell_detector, tmp_path):
        # Many comment blocks interleaved with minimal code
        comment_blocks = ""
        for i in range(7):   # 7 large blocks of 6 lines each
            comment_block = "\n".join(f"# comment line {j}" for j in range(6))
            comment_blocks += comment_block + "\n"
            comment_blocks += f"x{i} = {i}\n"
        f = tmp_path / "over_commented.py"
        f.write_text(comment_blocks)
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Excessive Comments"), \
            "Expected Excessive Comments for file with >30% comment ratio and >5 large blocks"

    def test_normal_comments_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "clean_comments.py"
        code = "\n".join(
            [f"x{i} = {i}" for i in range(30)] +
            ["# just one small comment"]
        )
        f.write_text(code)
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Excessive Comments")


# ---------------------------------------------------------------------------
# Duplicate Code
# ---------------------------------------------------------------------------

class TestDuplicateCode:
    def test_detects_identical_function_bodies(self, code_smell_detector, tmp_path):
        # threshold lowered to 3 in conftest; create 3 functions with identical bodies
        body = "\n".join(
            [f"    x{i} = {i}" for i in range(6)] +
            ["    return x0 + x1 + x2 + x3 + x4 + x5"]
        )
        funcs = "\n".join(f"def func{i}():\n{body}" for i in range(3))
        f = tmp_path / "dupes.py"
        f.write_text(funcs)
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Duplicate Code"), \
            "Expected Duplicate Code for 3 functions with identical bodies"

    def test_unique_bodies_not_flagged(self, code_smell_detector, tmp_path):
        f = tmp_path / "unique.py"
        f.write_text(
            "def func1():\n    return 1\ndef func2():\n    return 2\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Duplicate Code")


# ---------------------------------------------------------------------------
# Alternative Classes
# ---------------------------------------------------------------------------

class TestAlternativeClasses:
    def test_detects_same_interface_classes(self, code_smell_detector, tmp_path):
        # 3 classes all exposing the same public methods → threshold 3
        classes = "\n".join(
            f"class Impl{i}:\n"
            f"    def process(self):\n        return {i}\n"
            f"    def validate(self):\n        return True\n"
            f"    def execute(self):\n        return {i}\n"
            for i in range(3)
        )
        f = tmp_path / "alt_classes.py"
        f.write_text(classes)
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Alternative Classes"), \
            "Expected Alternative Classes for 3 classes with identical method sets"

    def test_classes_with_shared_base_not_flagged(self, code_smell_detector, tmp_path):
        # Sharing a base class is a valid design pattern, not a smell
        f = tmp_path / "hierarchy.py"
        f.write_text(
            "class Base:\n    pass\n"
            "class A(Base):\n    def process(self):\n        pass\n    def validate(self):\n        pass\n"
            "class B(Base):\n    def process(self):\n        pass\n    def validate(self):\n        pass\n"
            "class C(Base):\n    def process(self):\n        pass\n    def validate(self):\n        pass\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Alternative Classes"), \
            "Classes sharing a base should not trigger Alternative Classes"


    def test_unrelated_bases_do_not_count_as_shared(self, code_smell_detector, tmp_path):
        classes = "\n".join(
            f"class Impl{i}(Base{i}):\n"
            f"    def process(self):\n        return {i}\n"
            f"    def validate(self):\n        return True\n"
            for i in range(3)
        )
        f = tmp_path / "unrelated_bases.py"
        f.write_text(classes)
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Alternative Classes")


# ---------------------------------------------------------------------------
# Parallel Inheritance Hierarchies
# ---------------------------------------------------------------------------

class TestParallelInheritance:
    def test_detects_parallel_hierarchies(self, code_smell_detector, tmp_path):
        f = tmp_path / "parallel.py"
        f.write_text(
            "class Animal:\n"
            "    def speak(self): pass\n"
            "    def move(self): pass\n"
            "class Dog(Animal):\n"
            "    def speak(self): return 'woof'\n"
            "    def move(self): return 'walk'\n"
            "class Cat(Animal):\n"
            "    def speak(self): return 'meow'\n"
            "    def move(self): return 'slink'\n"
            "class AnimalOwner:\n"
            "    def speak(self): pass\n"
            "    def move(self): pass\n"
            "class DogOwner(AnimalOwner):\n"
            "    def speak(self): return 'hello'\n"
            "    def move(self): return 'drive'\n"
            "class CatOwner(AnimalOwner):\n"
            "    def speak(self): return 'hi'\n"
            "    def move(self): return 'cycle'\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert smells_named(code_smell_detector, "Parallel Inheritance"), \
            "Expected Parallel Inheritance Hierarchies"

    def test_unrelated_names_not_flagged(self, code_smell_detector, tmp_path):
        # Regression for #22: the naming check compared children with the first child,
        # so any two hierarchies sharing a method name were reported
        f = tmp_path / "unrelated.py"
        f.write_text(
            "class Animal:\n    pass\n"
            "class Dog(Animal):\n"
            "    def move(self): return 'walk'\n"
            "    def eat(self): return 'bone'\n"
            "class Cat(Animal):\n    def move(self): return 'slink'\n"
            "class Vehicle:\n    pass\n"
            "class Car(Vehicle):\n"
            "    def move(self): return 'drive'\n"
            "    def park(self): return 'garage'\n"
            "class Truck(Vehicle):\n    def move(self): return 'haul'\n"
        )
        code_smell_detector.detect_smells(str(f))
        assert not smells_named(code_smell_detector, "Parallel Inheritance")


# ---------------------------------------------------------------------------
# Cross-file smells
# ---------------------------------------------------------------------------

class TestCrossFileSmells:
    def test_cross_file_alternative_classes(self, code_smell_detector, tmp_path):
        for i in range(3):
            f = tmp_path / f"impl{i}.py"
            f.write_text(
                f"class Service{i}:\n"
                f"    def send(self):\n        return {i}\n"
                f"    def receive(self):\n        return {i}\n"
                f"    def process(self):\n        return {i}\n"
            )
            code_smell_detector.detect_smells(str(f))
        code_smell_detector.detect_cross_file_smells()
        assert smells_named(code_smell_detector, "Alternative Classes"), \
            "Expected cross-file Alternative Classes for 3 services with same interface"

    def test_cross_file_subclasses_of_shared_base_not_flagged(self, code_smell_detector, tmp_path):
        # Regression for #21: one subclass per file implementing a shared base is polymorphism
        for name in ("Circle", "Square", "Triangle"):
            f = tmp_path / f"{name.lower()}.py"
            f.write_text(
                f"class {name}(Shape):\n"
                f"    def area(self):\n        return 1\n"
                f"    def perimeter(self):\n        return 2\n"
            )
            code_smell_detector.detect_smells(str(f))
        code_smell_detector.detect_cross_file_smells()
        assert not smells_named(code_smell_detector, "Alternative Classes")

    def test_cross_file_duplicate_code(self, code_smell_detector, tmp_path):
        body = "\n".join(
            [f"    x{i} = {i}" for i in range(6)] +
            ["    return x0 + x1 + x2"]
        )
        for i in range(3):
            f = tmp_path / f"module{i}.py"
            f.write_text(f"def compute():\n{body}\n")
            code_smell_detector.detect_smells(str(f))
        code_smell_detector.detect_cross_file_smells()
        assert smells_named(code_smell_detector, "Duplicate Code"), \
            "Expected cross-file Duplicate Code"

    def test_cross_file_duplicate_code_not_double_counted(self, code_smell_detector, tmp_path):
        body = "\n".join(
            [f"    x{i} = {i}" for i in range(6)] +
            ["    return x0 + x1 + x2"]
        )
        a = tmp_path / "a.py"
        a.write_text("\n".join(f"def f{i}():\n{body}" for i in range(3)) + "\n")
        b = tmp_path / "b.py"
        b.write_text(f"def g():\n{body}\n")
        code_smell_detector.detect_smells(str(a))
        code_smell_detector.detect_smells(str(b))
        code_smell_detector.detect_cross_file_smells()
        dupes = smells_named(code_smell_detector, "Duplicate Code")
        assert len(dupes) == 1
        assert dupes[0].module_class == "f0, f1, f2, g"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_detect_smells_raises_on_syntax_error(self, code_smell_detector, tmp_path):
        from code_quality_analyzer.exceptions import CodeAnalysisError
        f = tmp_path / "broken.py"
        f.write_text("def func(:\n    pass\n")
        with pytest.raises(CodeAnalysisError):
            code_smell_detector.detect_smells(str(f))

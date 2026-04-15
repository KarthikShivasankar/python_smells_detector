import pytest
from code_quality_analyzer.code_smell_detector import CodeSmellDetector
from code_quality_analyzer.config_handler import ConfigHandler

@pytest.fixture
def config_handler():
    return ConfigHandler('code_quality_config.yaml')

@pytest.fixture
def code_smell_detector(config_handler):
    thresholds = config_handler.get_thresholds('code_smells')
    return CodeSmellDetector(thresholds)

def test_detect_long_method(code_smell_detector, tmp_path):
    test_file = tmp_path / "long_method.py"
    test_file.write_text("\n".join([f"print('Line {i}')" for i in range(21)]))

    code_smell_detector.detect_smells(str(test_file))
    assert any("Long Method" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_large_class(code_smell_detector, tmp_path):
    test_file = tmp_path / "large_class.py"
    test_file.write_text("class LargeClass:\n" + "\n".join([f"    def method{i}(self): pass" for i in range(16)]))

    code_smell_detector.detect_smells(str(test_file))
    assert any("Large Class" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_long_parameter_list(code_smell_detector, tmp_path):
    test_file = tmp_path / "long_parameter_list.py"
    test_file.write_text("def function_with_many_params(param1, param2, param3, param4, param5, param6, param7): pass")

    code_smell_detector.detect_smells(str(test_file))
    assert any("Long Parameter List" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_complex_conditional(code_smell_detector, tmp_path):
    test_file = tmp_path / "complex_conditional.py"
    test_file.write_text("""
def complex_function(a, b, c, d):
    if a > b:
        print("a > b")
    elif b > c:
        print("b > c")
    elif c > d:
        print("c > d")
    else:
        print("d is largest")
    """)

    code_smell_detector.detect_smells(str(test_file))
    assert any("Complex Conditional" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_primitive_obsession(code_smell_detector, tmp_path):
    test_file = tmp_path / "primitive_obsession.py"
    test_file.write_text("def function_with_primitives(a: int, b: str, c: float, d: bool, e: int): pass")

    code_smell_detector.detect_smells(str(test_file))
    assert any("Primitive Obsession" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_divergent_change(code_smell_detector, tmp_path):
    test_file = tmp_path / "divergent_change.py"
    test_file.write_text("""
class DivergentClass:
    def database_method1(self): pass
    def database_method2(self): pass
    def ui_method1(self): pass
    def ui_method2(self): pass
    def network_method1(self): pass
    def network_method2(self): pass
    """)

    code_smell_detector.detect_smells(str(test_file))
    assert any("Divergent Change" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_shotgun_surgery(code_smell_detector, tmp_path):
    test_file = tmp_path / "shotgun_surgery.py"
    test_file.write_text("\n".join([f"def function{i}():\n    common_operation()" for i in range(7)]))

    code_smell_detector.detect_smells(str(test_file))
    assert any("Shotgun Surgery" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_excessive_comments(code_smell_detector, tmp_path):
    test_file = tmp_path / "excessive_comments.py"
    test_file.write_text("\n".join([f"# Comment {i}" if i % 2 == 0 else f"print({i})" for i in range(20)]))

    code_smell_detector.detect_smells(str(test_file))
    assert any("Excessive Comments" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_lazy_class(code_smell_detector, tmp_path):
    test_file = tmp_path / "lazy_class.py"
    test_file.write_text("""
class LazyClass:
    def method1(self): pass
    def method2(self): pass
    """)

    code_smell_detector.detect_smells(str(test_file))
    assert any("Lazy Class" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_feature_envy(code_smell_detector, tmp_path):
    test_file = tmp_path / "feature_envy.py"
    test_file.write_text("""
class OtherClass:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass

class EnviousClass:
    def envious_method(self, other):
        other.method1()
        other.method2()
        other.method3()
        other.method4()
        other.method1()
    """)

    code_smell_detector.detect_smells(str(test_file))
    assert any("Feature Envy" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_inappropriate_intimacy(code_smell_detector, tmp_path):
    test_file = tmp_path / "inappropriate_intimacy.py"
    test_file.write_text("""
class ClassA:
    def __init__(self):
        self.shared1 = 1
        self.shared2 = 2
        self.shared3 = 3
        self.shared4 = 4

class ClassB:
    def method1(self, a):
        return a.shared1
    def method2(self, a):
        return a.shared2
    def method3(self, a):
        return a.shared3
    def method4(self, a):
        return a.shared4
    """)

    code_smell_detector.detect_smells(str(test_file))
    assert any("Inappropriate Intimacy" in smell.name for smell in code_smell_detector.code_smells)

def test_detect_message_chains(code_smell_detector, tmp_path):
    test_file = tmp_path / "message_chains.py"
    test_file.write_text("""
def long_chain():
    return obj.method1().method2().method3().method4().method5()
    """)

    code_smell_detector.detect_smells(str(test_file))
    assert any("Message Chains" in smell.name for smell in code_smell_detector.code_smells)

# Add more tests for other code smells...

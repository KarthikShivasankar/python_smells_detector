import pytest
from code_quality_analyzer.structural_smell_detector import StructuralSmellDetector
from code_quality_analyzer.config_handler import ConfigHandler

@pytest.fixture
def config_handler():
    return ConfigHandler('code_quality_config.yaml')

@pytest.fixture
def structural_smell_detector(config_handler):
    thresholds = config_handler.get_thresholds('structural_smells')
    return StructuralSmellDetector(thresholds)

def test_detect_nom(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("\n".join([f"def method{i}(): pass" for i in range(21)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Number of Methods (NOM)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_wmpc(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("\n".join([f"def method{i}(a, b, c): return a + b + c" for i in range(51)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Weighted Methods per Class (WMPC)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_size2(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("class TestClass:\n    " + "\n    ".join([f"attr{i} = {i}" for i in range(25)] + [f"def method{i}(): pass" for i in range(26)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("Large Class (SIZE2)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_wac(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("class TestClass:\n    " + "\n    ".join([f"attr{i} = {i}" for i in range(16)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Weight of a Class (WAC)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_lcom(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("""
class TestClass:
    def __init__(self):
        self.a = 1
        self.b = 2
    def method1(self):
        return self.a
    def method2(self):
        return self.b
    def method3(self):
        pass
    """)

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Lack of Cohesion in Methods (LCOM)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_rfc(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("class TestClass:\n    " + "\n    ".join([f"def method{i}(): other_method()" for i in range(51)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Response for Class (RFC)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_nocc(structural_smell_detector, tmp_path):
    for i in range(11):
        (tmp_path / f"class{i}.py").write_text(f"class Class{i}: pass")

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Number of Classes (NOCC)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_dit(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_inheritance.py"
    test_file.write_text("""
class A: pass
class B(A): pass
class C(B): pass
class D(C): pass
class E(D): pass
class F(E): pass
    """)

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Depth of Inheritance Tree (DIT)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_loc(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_module.py"
    test_file.write_text("\n".join([f"print({i})" for i in range(1001)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Lines of Code (LOC)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_mpc(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("class TestClass:\n    " + "\n    ".join([f"def method{i}(): other_object.method()" for i in range(51)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Method Propagation Coupling (MPC)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_cbo(structural_smell_detector, tmp_path):
    for i in range(11):
        module = tmp_path / f"module{i}.py"
        imports = "\n".join([f"import module{j}" for j in range(11) if j != i])
        module.write_text(imports)

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Coupling Between Object Classes (CBO)" in smell.name for smell in structural_smell_detector.structural_smells)

def test_detect_noc(structural_smell_detector, tmp_path):
    for i in range(101):
        module = tmp_path / f"module{i}.py"
        module.write_text(f"class Class{i}: pass")

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Number of Classes (NOC)" in smell.name for smell in structural_smell_detector.structural_smells)

# Add more tests for other structural smells...
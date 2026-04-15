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
    assert any("High Number of Methods (NOM)" in smell for smell in structural_smell_detector.structural_smells)

def test_detect_wmpc(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("\n".join([f"def method{i}(a, b, c): return a + b + c" for i in range(51)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Weighted Methods per Class (WMPC)" in smell for smell in structural_smell_detector.structural_smells)

def test_detect_size2(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    attributes = "\n".join([f"attr{i} = {i}" for i in range(25)])
    methods = "\n".join([f"def method{i}(): pass" for i in range(26)])
    test_file.write_text(f"class TestClass:\n{attributes}\n{methods}")

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("Large Class (SIZE2)" in smell for smell in structural_smell_detector.structural_smells)

def test_detect_wac(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_class.py"
    test_file.write_text("\n".join([f"attr{i} = {i}" for i in range(16)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Weight of a Class (WAC)" in smell for smell in structural_smell_detector.structural_smells)

def test_detect_loc(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_module.py"
    test_file.write_text("\n".join([f"print({i})" for i in range(1001)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Lines of Code (LOC)" in smell for smell in structural_smell_detector.structural_smells)

def test_detect_cbo(structural_smell_detector, tmp_path):
    for i in range(11):
        module = tmp_path / f"module{i}.py"
        imports = "\n".join([f"import module{j}" for j in range(11) if j != i])
        module.write_text(imports)

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Coupling Between Object Classes (CBO)" in smell for smell in structural_smell_detector.structural_smells)

def test_detect_noc(structural_smell_detector, tmp_path):
    for i in range(101):
        module = tmp_path / f"module{i}.py"
        module.write_text(f"class Class{i}: pass")

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Number of Classes (NOC)" in smell for smell in structural_smell_detector.structural_smells)

# Add more tests for other structural smells...



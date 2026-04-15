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
    assert any("Long Method" in smell for smell in code_smell_detector.code_smells)

def test_detect_large_class(code_smell_detector, tmp_path):
    test_file = tmp_path / "large_class.py"
    test_file.write_text("class LargeClass:\n" + "\n".join([f"    def method{i}(self): pass" for i in range(16)]))

    code_smell_detector.detect_smells(str(test_file))
    assert any("Large Class" in smell for smell in code_smell_detector.code_smells)

def test_detect_long_parameter_list(code_smell_detector, tmp_path):
    test_file = tmp_path / "long_parameter_list.py"
    test_file.write_text("def function_with_many_params(param1, param2, param3, param4, param5, param6, param7): pass")

    code_smell_detector.detect_smells(str(test_file))
    assert any("Long Parameter List" in smell for smell in code_smell_detector.code_smells)

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
    assert any("Complex Conditional" in smell for smell in code_smell_detector.code_smells)

def test_detect_primitive_obsession(code_smell_detector, tmp_path):
    test_file = tmp_path / "primitive_obsession.py"
    test_file.write_text("def function_with_primitives(a: int, b: str, c: float, d: bool, e: int): pass")

    code_smell_detector.detect_smells(str(test_file))
    assert any("Primitive Obsession" in smell for smell in code_smell_detector.code_smells)

# Add more tests for other code smells...

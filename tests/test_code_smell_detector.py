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


def test_detect_primitive_obsession(code_smell_detector, tmp_path):
    test_file = tmp_path / "primitive_obsession.py"
    test_file.write_text("def function_with_primitives(a: int, b: str, c: float, d: bool, e: int): pass")

    code_smell_detector.detect_smells(str(test_file))
    assert any("Primitive Obsession" in smell.name for smell in code_smell_detector.code_smells)



def test_detect_shotgun_surgery(code_smell_detector, tmp_path):
    test_file = tmp_path / "shotgun_surgery.py"
    test_file.write_text("\n".join([f"def function{i}():\n    common_operation()" for i in range(7)]))

    code_smell_detector.detect_smells(str(test_file))
    assert any("Shotgun Surgery" in smell.name for smell in code_smell_detector.code_smells)


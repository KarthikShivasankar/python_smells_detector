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



def test_detect_loc(structural_smell_detector, tmp_path):
    test_file = tmp_path / "test_module.py"
    test_file.write_text("\n".join([f"print({i})" for i in range(1001)]))

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Lines of Code (LOC)" in smell.name for smell in structural_smell_detector.structural_smells)



def test_detect_noc(structural_smell_detector, tmp_path):
    for i in range(101):
        module = tmp_path / f"module{i}.py"
        module.write_text(f"class Class{i}: pass")

    structural_smell_detector.detect_smells(str(tmp_path))
    assert any("High Number of Classes (NOC)" in smell.name for smell in structural_smell_detector.structural_smells)


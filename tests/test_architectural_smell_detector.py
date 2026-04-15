import pytest
from code_quality_analyzer.architectural_smell_detector import ArchitecturalSmellDetector
from code_quality_analyzer.config_handler import ConfigHandler

@pytest.fixture
def config_handler():
    return ConfigHandler('code_quality_config.yaml')

@pytest.fixture
def architectural_smell_detector(config_handler):
    thresholds = config_handler.get_thresholds('architectural_smells')
    return ArchitecturalSmellDetector(thresholds)

def test_detect_god_object(architectural_smell_detector, tmp_path):
    test_file = tmp_path / "god_object.py"
    test_file.write_text("\n".join([f"def func{i}(): pass" for i in range(26)]))

    architectural_smell_detector.detect_smells(str(tmp_path))
    assert any("God Object" in smell.name for smell in architectural_smell_detector.architectural_smells)


def test_detect_scattered_functionality(architectural_smell_detector, tmp_path):
    for i in range(3):
        module = tmp_path / f"module{i}.py"
        module.write_text("def scattered_function(): pass")

    architectural_smell_detector.detect_smells(str(tmp_path))
    assert any("Scattered Functionality" in smell.name for smell in architectural_smell_detector.architectural_smells)

def test_detect_redundant_abstraction(architectural_smell_detector, tmp_path):
    module1 = tmp_path / "module1.py"
    module2 = tmp_path / "module2.py"
    content = "\n".join([f"def func{i}(): pass" for i in range(5)])
    module1.write_text(content)
    module2.write_text(content)

    architectural_smell_detector.detect_smells(str(tmp_path))
    assert any("Redundant Abstraction" in smell.name for smell in architectural_smell_detector.architectural_smells)

def test_detect_improper_api_usage(architectural_smell_detector, tmp_path):
    test_file = tmp_path / "improper_api_usage.py"
    test_file.write_text("\n".join([f"api.method1()" for _ in range(10)]))

    architectural_smell_detector.detect_smells(str(tmp_path))
    assert any("Improper API Usage" in smell.name for smell in architectural_smell_detector.architectural_smells)




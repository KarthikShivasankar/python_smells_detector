"""
Tests for ConfigHandler — config loading, validation, and threshold access.
"""
import os

import pytest
import yaml

from code_quality_analyzer.config_handler import ConfigHandler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REAL_CONFIG = os.path.join(PROJECT_ROOT, 'code_quality_config.yaml')


def write_config(path, data):
    with open(path, 'w') as f:
        yaml.safe_dump(data, f)


# ---------------------------------------------------------------------------
# Loading the real project config
# ---------------------------------------------------------------------------

class TestRealConfig:
    def test_loads_without_error(self):
        handler = ConfigHandler(REAL_CONFIG)
        assert handler.thresholds

    def test_all_three_smell_categories_present(self):
        handler = ConfigHandler(REAL_CONFIG)
        assert 'code_smells' in handler.thresholds
        assert 'structural_smells' in handler.thresholds
        assert 'architectural_smells' in handler.thresholds

    def test_code_smell_thresholds_are_positive_numbers(self):
        handler = ConfigHandler(REAL_CONFIG)
        for key, value in handler.thresholds['code_smells'].items():
            assert isinstance(value, (int, float)), f"{key} should be numeric"
            assert value > 0, f"{key} should be positive"

    def test_structural_thresholds_include_required_keys(self):
        handler = ConfigHandler(REAL_CONFIG)
        required = [
            'NOM_THRESHOLD', 'WMPC1_THRESHOLD', 'WMPC2_THRESHOLD',
            'SIZE2_THRESHOLD', 'WAC_THRESHOLD', 'LCOM_THRESHOLD',
            'RFC_THRESHOLD', 'NOCC_THRESHOLD', 'DIT_THRESHOLD',
            'LOC_THRESHOLD', 'CBO_THRESHOLD'
        ]
        structural = handler.thresholds['structural_smells']
        for key in required:
            assert key in structural, f"Required threshold {key} missing from config"

    def test_get_thresholds_unknown_key_returns_empty(self):
        handler = ConfigHandler(REAL_CONFIG)
        result = handler.get_thresholds('nonexistent_category')
        assert result == {}


# ---------------------------------------------------------------------------
# Custom minimal config
# ---------------------------------------------------------------------------

class TestCustomConfig:
    def test_loads_custom_yaml(self, tmp_path):
        cfg = {
            'code_smells': {
                'LONG_METHOD_LINES': {'value': 30},
                'LARGE_CLASS_METHODS': {'value': 10},
            },
            'structural_smells': {
                'NOM_THRESHOLD': {'value': 5},
                'WMPC1_THRESHOLD': {'value': 10},
                'WMPC2_THRESHOLD': {'value': 10},
                'SIZE2_THRESHOLD': {'value': 8},
                'WAC_THRESHOLD': {'value': 4},
                'LCOM_THRESHOLD': {'value': 5},
                'RFC_THRESHOLD': {'value': 10},
                'NOCC_THRESHOLD': {'value': 5},
                'DIT_THRESHOLD': {'value': 2},
                'LOC_THRESHOLD': {'value': 100},
                'CBO_THRESHOLD': {'value': 3},
            },
            'architectural_smells': {
                'GOD_OBJECT_FUNCTIONS': {'value': 10},
            }
        }
        config_path = str(tmp_path / 'test_config.yaml')
        write_config(config_path, cfg)
        handler = ConfigHandler(config_path)
        assert handler.get_thresholds('code_smells')['LONG_METHOD_LINES'] == 30
        assert handler.get_thresholds('structural_smells')['NOM_THRESHOLD'] == 5
        assert handler.get_thresholds('architectural_smells')['GOD_OBJECT_FUNCTIONS'] == 10

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ConfigHandler(str(tmp_path / 'nonexistent.yaml'))

    def test_invalid_yaml_raises(self, tmp_path):
        bad = tmp_path / 'bad.yaml'
        bad.write_text(": invalid: yaml: {{")
        with pytest.raises(Exception):
            ConfigHandler(str(bad))

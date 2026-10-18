import logging
from importlib import resources

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_NAME = "code_quality_config.yaml"
SECTIONS = ('code_smells', 'architectural_smells', 'structural_smells')


class ConfigHandler:
    """
    A class to handle configuration loading and management for code quality analysis.
    """

    def __init__(self, config_path):
        """
        Initialize the ConfigHandler with a given configuration file path.

        Args:
            config_path (str): The path to the YAML configuration file.
        """
        self.config_path = config_path
        self.thresholds = self.load_thresholds()
        self._validate_thresholds()

    def load_thresholds(self):
        """
        Load threshold values from the YAML configuration file. Thresholds it does not
        set keep the defaults from the configuration bundled with the package, so a
        partial config only needs the values it changes.
        """
        try:
            config = self._read(self.config_path)
            defaults = self._read(resources.files(__package__).joinpath(DEFAULT_CONFIG_NAME))

            logger.info(f"Loading configuration from: {self.config_path}")

            thresholds = {}
            for section in SECTIONS:
                user = config.get(section) or {}
                unknown = set(user) - set(defaults.get(section, {}))
                if unknown:
                    logger.warning(f"Unknown {section} thresholds in {self.config_path}: {sorted(unknown)}")
                merged = {**defaults.get(section, {}), **user}
                thresholds[section] = {k: v['value'] if isinstance(v, dict) else v
                                       for k, v in merged.items()}

            logger.info(f"Loaded thresholds: {thresholds}")
            return thresholds

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {str(e)}")
            raise

    @staticmethod
    def _read(path):
        with open(path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}

    def _validate_thresholds(self):
        """
        Warn about threshold values that are not positive numbers. Missing thresholds
        cannot occur: they fall back to the bundled defaults.
        """
        for section in SECTIONS:
            for threshold, value in self.thresholds[section].items():
                if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                    logger.warning(f"Invalid threshold value for {threshold}: {value}")

    def get_thresholds(self, smell_type):
        """
        Get threshold values for a specific type of code smell.
        """
        thresholds = self.thresholds.get(smell_type, {})
        logger.debug(f"Retrieved {smell_type} thresholds: {thresholds}")
        return thresholds

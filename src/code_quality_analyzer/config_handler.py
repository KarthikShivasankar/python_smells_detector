import yaml

class ConfigHandler:
    """
    A class to handle configuration loading and management for code quality analysis.

    This class is responsible for loading threshold values from a YAML configuration file
    and providing access to these thresholds for different types of code smells.

    Attributes:
        config_path (str): The path to the YAML configuration file.
        thresholds (dict): A dictionary containing threshold values for different types of code smells.
    """

    def __init__(self, config_path):
        """
        Initialize the ConfigHandler with a given configuration file path.

        Args:
            config_path (str): The path to the YAML configuration file.
        """
        self.config_path = config_path
        self.thresholds = self.load_thresholds()

    def load_thresholds(self):
        """
        Load threshold values from the YAML configuration file.

        This method reads the configuration file and extracts threshold values
        for different types of code smells.

        Returns:
            dict: A dictionary containing threshold values for different types of code smells.
        """
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file)
        return {
            'code_smells': {k: v['value'] for k, v in config['code_smells'].items()},
            'architectural_smells': {k: v['value'] for k, v in config['architectural_smells'].items()},
            'structural_smells': {k: v['value'] for k, v in config['structural_smells'].items()}
        }

    def get_thresholds(self, smell_type):
        """
        Get threshold values for a specific type of code smell.

        Args:
            smell_type (str): The type of code smell ('code_smells', 'architectural_smells', or 'structural_smells').

        Returns:
            dict: A dictionary of threshold values for the specified smell type.
                  Returns an empty dictionary if the smell type is not found.
        """
        return self.thresholds.get(smell_type, {})
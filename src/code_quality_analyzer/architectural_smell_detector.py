import os
import ast
import networkx as nx
from collections import defaultdict
import yaml
from dataclasses import dataclass

@dataclass
class ArchitecturalSmell:
    name: str
    description: str
    file_path: str
    module_class: str
    line_number: int = None
    severity: str = ''

class ArchitecturalSmellDetector:
    """
    A class to detect architectural smells in Python projects.

    This class analyzes Python source code files within a directory to identify
    various architectural smells based on predefined thresholds.

    Attributes:
        architectural_smells (list): A list to store detected architectural smells.
        module_dependencies (nx.DiGraph): A directed graph to represent module dependencies.
        module_functions (defaultdict): A dictionary to store functions for each module.
        api_usage (defaultdict): A dictionary to store API usage for each module.
        thresholds (dict): A dictionary of threshold values for various smell detections.
        file_paths (dict): A dictionary to store file paths for each module.
    """

    def __init__(self, thresholds):
        """
        Initialize the ArchitecturalSmellDetector with given thresholds.

        Args:
            thresholds (dict): A dictionary of threshold values for various smell detections.
        """
        self.architectural_smells = []
        self.module_dependencies = nx.DiGraph()
        self.module_functions = defaultdict(set)
        self.api_usage = defaultdict(list)
        self.thresholds = thresholds
        self.file_paths = {}  # New attribute to store file paths

    def load_thresholds(self, config_path):
        """
        Load threshold values from a YAML configuration file.

        Args:
            config_path (str): Path to the YAML configuration file.

        Returns:
            dict: A dictionary of threshold values for architectural smells.
        """
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return {k: v['value'] for k, v in config['architectural_smells'].items()}

    def detect_smells(self, directory_path):
        """
        Detect architectural smells in the given directory.

        This method analyzes all Python files in the given directory and its subdirectories,
        and runs various smell detection methods. If a parse error occurs, it prints the error
        message and continues with the analysis.

        Args:
            directory_path (str): The path to the directory to be analyzed.
        """
        try:
            self.analyze_directory(directory_path)
            self.detect_hub_like_dependency()
            self.detect_scattered_functionality()
            self.detect_redundant_abstractions()
            self.detect_god_objects()
            self.detect_improper_api_usage()
            self.detect_orphan_modules()
            self.detect_cyclic_dependencies()
            self.detect_unstable_dependencies()
        except Exception as e:
            print(f"Error analyzing directory {directory_path}: {str(e)}")

    def analyze_directory(self, directory_path):
        """
        Analyze all Python files in the given directory and its subdirectories.

        Args:
            directory_path (str): The path to the directory to be analyzed.
        """
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)
        
        # After analyzing all files, resolve external dependencies
        self.resolve_external_dependencies()

    def analyze_file(self, file_path):
        """
        Analyze a single Python file for architectural information.

        This method parses the file and extracts information about imports,
        functions, and API usage.

        Args:
            file_path (str): The path to the Python file to be analyzed.
        """
        try:
            with open(file_path, 'r') as file:
                tree = ast.parse(file.read())

            module_name = os.path.relpath(file_path, os.path.dirname(os.path.dirname(file_path)))
            module_name = module_name.replace(os.path.sep, '.')[:-3]  # Remove .py extension
            self.module_dependencies.add_node(module_name)
            self.file_paths[module_name] = file_path

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.module_dependencies.add_edge(module_name, alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.module_dependencies.add_edge(module_name, node.module)
                elif isinstance(node, ast.FunctionDef):
                    self.module_functions[module_name].add(node.name)
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        self.api_usage[module_name].append(node.func.attr)
        except SyntaxError as e:
            print(f"Parse error in file {file_path}: {str(e)}")
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")

    def resolve_external_dependencies(self):
        """
        Resolve external dependencies by checking if imported modules exist in the project.
        """
        all_modules = set(self.module_dependencies.nodes())
        for module in list(self.module_dependencies.nodes()):
            for dependency in list(self.module_dependencies.successors(module)):
                if dependency not in all_modules:
                    self.module_dependencies.remove_edge(module, dependency)
                    if not self.module_dependencies.in_edges(dependency) and not self.module_dependencies.out_edges(dependency):
                        self.module_dependencies.remove_node(dependency)

    def add_smell(self, name, description, file_path, module_class, line_number=None):
        """
        Add a detected architectural smell to the list of smells.

        Args:
            name (str): The name of the architectural smell.
            description (str): A description of the detected smell.
            file_path (str): The path to the file where the smell was detected.
            module_class (str): The module or class where the smell was detected.
            line_number (int, optional): The line number where the smell was detected. Defaults to None.
        """
        self.architectural_smells.append(ArchitecturalSmell(
            name=name,
            description=description,
            file_path=file_path,
            module_class=module_class,
            line_number=line_number
        ))

    def detect_hub_like_dependency(self):
        """
        Detect hub-like dependencies in the project.

        A hub-like dependency is a module that has high connectivity
        (sum of in-degree and out-degree) relative to the total number of modules.
        """
        total_modules = len(self.module_dependencies.nodes())
        threshold = self.thresholds.get('HUB_LIKE_DEPENDENCY_THRESHOLD', 0.5)
        for node in self.module_dependencies.nodes():
            in_degree = self.module_dependencies.in_degree(node)
            out_degree = self.module_dependencies.out_degree(node)
            if (in_degree + out_degree) / total_modules > threshold:
                self.add_smell(
                    "Hub-like Dependency",
                    f"Module '{node}' has high connectivity ({in_degree + out_degree} connections)",
                    self.file_paths.get(node, "Unknown"),
                    node
                )

    def detect_scattered_functionality(self):
        """
        Detect scattered functionality in the project.

        Scattered functionality occurs when a function appears in multiple modules.
        """
        function_modules = defaultdict(list)
        for module, functions in self.module_functions.items():
            for func in functions:
                function_modules[func].append(module)
        
        for func, modules in function_modules.items():
            if len(modules) > 1:
                self.add_smell(
                    "Scattered Functionality",
                    f"Function '{func}' appears in modules {', '.join(modules)}",
                    self.file_paths.get(modules[0], "Unknown"),
                    modules[0]
                )

    def detect_redundant_abstractions(self):
        """
        Detect potential redundant abstractions in the project.

        This is a simplified check that looks for modules with similar functionalities.
        """
        similar_modules = defaultdict(list)
        for module, functions in self.module_functions.items():
            signature = frozenset(functions)
            similar_modules[signature].append(module)
        
        for signature, modules in similar_modules.items():
            if len(modules) > 1:
                self.add_smell(
                    "Potential Redundant Abstractions",
                    f"Modules {', '.join(modules)} have similar functionalities",
                    self.file_paths.get(modules[0], "Unknown"),
                    modules[0]
                )

    def detect_god_objects(self):
        """
        Detect god objects in the project.

        A god object is a module that has too many functions.
        """
        for module, functions in self.module_functions.items():
            if len(functions) > self.thresholds['GOD_OBJECT_FUNCTIONS']:
                self.add_smell(
                    "God Object",
                    f"Module '{module}' has too many functions ({len(functions)})", 
                    self.file_paths.get(module, "Unknown"),
                    module
                )

    def detect_improper_api_usage(self):
        """
        Detect potential improper API usage in the project.

        This is a simplified check that looks for repetitive API calls within a module.
        """
        for module, api_calls in self.api_usage.items():
            if len(set(api_calls)) < len(api_calls) / 2:
                self.add_smell(
                    "Potential Improper API Usage",
                    f"Module '{module}' has repetitive API calls",
                    self.file_paths.get(module, "Unknown"),
                    module
                )

    def detect_orphan_modules(self):
        """
        Detect orphan modules in the project.

        An orphan module is a module that has no incoming or outgoing dependencies.
        """
        for node in self.module_dependencies.nodes():
            if self.module_dependencies.in_degree(node) + self.module_dependencies.out_degree(node) == 0:
                self.add_smell(
                    "Orphan Module",
                    f"'{node}' is not connected to other modules",
                    self.file_paths.get(node, "Unknown"),
                    node
                )

    def detect_cyclic_dependencies(self):
        """
        Detect cyclic dependencies in the project.

        A cyclic dependency occurs when two or more modules depend on each other in a circular manner.
        """
        cycles = list(nx.simple_cycles(self.module_dependencies))
        for cycle in cycles:
            if len(cycle) > 1:  # Ignore self-loops
                cycle_str = ' -> '.join(cycle + [cycle[0]])  # Add the first node at the end to complete the cycle
                self.add_smell(
                    "Cyclic Dependency",
                    f"Modules form a dependency cycle: {cycle_str}",
                    self.file_paths.get(cycle[0], "Unknown"),
                    cycle[0]
                )

    def detect_unstable_dependencies(self):
        """
        Detect unstable dependencies in the project.

        An unstable dependency is a module with high instability, calculated as the ratio of
        outgoing dependencies to total dependencies.
        """
        for node in self.module_dependencies.nodes():
            in_degree = self.module_dependencies.in_degree(node)
            out_degree = self.module_dependencies.out_degree(node)
            total_dependencies = in_degree + out_degree
            if total_dependencies > 0:
                instability = out_degree / total_dependencies
                if instability > self.thresholds['UNSTABLE_DEPENDENCY_THRESHOLD']:
                    self.add_smell(
                        "Unstable Dependency",
                        f"Module '{node}' has high instability ({instability:.2f})",
                        self.file_paths.get(node, "Unknown"),
                        node
                    )

    def print_report(self):
        """
        Print a report of all detected architectural smells.

        If no smells are detected, it prints a message indicating so.
        """
        if not self.architectural_smells:
            print("No architectural smells detected.")
        else:
            print("Detected Architectural Smells:")
            for smell in self.architectural_smells:
                print(f"- {smell}")

def analyze_architecture(directory_path, config_path):
    """
    Analyze the architecture of a Python project and detect architectural smells.

    Args:
        directory_path (str): The path to the directory containing the Python project to analyze.
        config_path (str): The path to the configuration file containing smell detection thresholds.
    """
    detector = ArchitecturalSmellDetector(config_path)
    detector.detect_smells(directory_path)
    detector.print_report()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Detect architectural smells in Python code.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default="code_quality_config.yaml", help="Path to the configuration file")
    args = parser.parse_args()

    analyze_architecture(args.directory, args.config)
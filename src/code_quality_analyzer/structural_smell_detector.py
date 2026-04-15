import os
import ast
import networkx as nx
from collections import defaultdict

class StructuralSmellDetector:
    """
    A class to detect structural code smells in Python projects.

    This class analyzes Python source code files within a directory to identify
    various structural code smells based on predefined thresholds.

    Attributes:
        structural_smells (list): A list to store detected structural smells.
        class_info (defaultdict): A dictionary to store information about classes.
        module_info (defaultdict): A dictionary to store information about modules.
        dependency_graph (nx.DiGraph): A directed graph to represent module dependencies.
        thresholds (dict): A dictionary of threshold values for various smell detections.
        project_root (str): The root directory of the project being analyzed.
    """

    def __init__(self, thresholds):
        """
        Initialize the StructuralSmellDetector with given thresholds.

        Args:
            thresholds (dict): A dictionary of threshold values for various smell detections.
        """
        self.structural_smells = []
        self.class_info = defaultdict(dict)
        self.module_info = defaultdict(dict)
        self.dependency_graph = nx.DiGraph()
        self.thresholds = thresholds
        self.project_root = None

    def detect_smells(self, directory_path):
        """
        Detect structural smells in the given directory.

        This method analyzes all Python files in the given directory and its subdirectories,
        and runs various smell detection methods.

        Args:
            directory_path (str): The path to the directory to be analyzed.
        """
        self.project_root = directory_path
        self.analyze_directory(directory_path)
        self.detect_nom()
        self.detect_wmpc()
        self.detect_size2()
        self.detect_wac()
        self.detect_lcom()
        self.detect_rfc()
        self.detect_nocc()
        self.detect_dit()
        self.detect_loc()
        self.detect_mpc()
        self.detect_cbo()
        self.detect_noc()

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

    def analyze_file(self, file_path):
        """
        Analyze a single Python file for structural information.

        This method parses the file and extracts information about classes, methods,
        attributes, and module dependencies.

        Args:
            file_path (str): The path to the Python file to be analyzed.
        """
        with open(file_path, 'r') as file:
            tree = ast.parse(file.read())

        module_name = os.path.relpath(file_path, self.project_root).replace(os.path.sep, '.')[:-3]
        self.module_info[module_name]['loc'] = len(tree.body)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = f"{module_name}.{node.name}"
                self.class_info[class_name]['methods'] = []
                self.class_info[class_name]['attributes'] = []
                self.class_info[class_name]['loc'] = node.end_lineno - node.lineno + 1

                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        self.class_info[class_name]['methods'].append(child.name)
                    elif isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                self.class_info[class_name]['attributes'].append(target.id)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.dependency_graph.add_edge(module_name, alias.name)
                else:
                    if node.module:
                        self.dependency_graph.add_edge(module_name, node.module)

    def detect_nom(self):
        """
        Detect classes with a high Number of Methods (NOM).

        This method identifies classes that exceed the NOM threshold and adds them to the structural smells list.
        """
        for class_name, info in self.class_info.items():
            nom = len(info['methods'])
            if nom > self.thresholds['NOM_THRESHOLD']:
                self.structural_smells.append(f"High Number of Methods (NOM): Class '{class_name}' has {nom} methods")

    def detect_wmpc(self):
        """
        Detect classes with high Weighted Methods per Class (WMPC).

        This method calculates a simplified WMPC for each class and identifies those exceeding the threshold.
        """
        for class_name, info in self.class_info.items():
            wmpc = sum(1 for method in info['methods'])  # Simplified, should consider complexity
            if wmpc > self.thresholds['WMPC1_THRESHOLD']:
                self.structural_smells.append(f"High Weighted Methods per Class (WMPC): Class '{class_name}' has WMPC of {wmpc}")

    def detect_size2(self):
        """
        Detect large classes based on the SIZE2 metric.

        This method calculates the SIZE2 metric (sum of methods and attributes) for each class
        and identifies those exceeding the threshold.
        """
        for class_name, info in self.class_info.items():
            size2 = len(info['methods']) + len(info['attributes'])
            if size2 > self.thresholds['SIZE2_THRESHOLD']:
                self.structural_smells.append(f"Large Class (SIZE2): Class '{class_name}' has {size2} members")

    def detect_wac(self):
        """
        Detect classes with high Weight of a Class (WAC).

        This method counts the number of attributes in each class and identifies those exceeding the WAC threshold.
        """
        for class_name, info in self.class_info.items():
            wac = len(info['attributes'])
            if wac > self.thresholds['WAC_THRESHOLD']:
                self.structural_smells.append(f"High Weight of a Class (WAC): Class '{class_name}' has {wac} attributes")

    def detect_lcom(self):
        """
        Detect classes with high Lack of Cohesion of Methods (LCOM).

        This method calculates a simplified LCOM metric for each class and identifies those exceeding the threshold.
        """
        for class_name, info in self.class_info.items():
            method_count = len(info['methods'])
            attribute_count = len(info['attributes'])
            if method_count > 1 and attribute_count > 0:
                lcom = 1 - (attribute_count / method_count)
                if lcom > self.thresholds['LCOM_THRESHOLD']:
                    self.structural_smells.append(f"High Lack of Cohesion of Methods (LCOM): Class '{class_name}' has LCOM of {lcom:.2f}")

    def detect_rfc(self):
        """
        Detect classes with high Response for a Class (RFC).

        This method calculates a simplified RFC metric for each class and identifies those exceeding the threshold.
        """
        for class_name, info in self.class_info.items():
            rfc = len(info['methods'])  # Should also include called methods
            if rfc > self.thresholds['RFC_THRESHOLD']:
                self.structural_smells.append(f"High Response for a Class (RFC): Class '{class_name}' has RFC of {rfc}")

    def detect_nocc(self):
        """
        Detect modules with a high Number of Classes (NOCC).

        This method counts the number of classes in each module and identifies those exceeding the NOCC threshold.
        """
        module_class_count = defaultdict(int)
        for class_name in self.class_info:
            module_name = class_name.rsplit('.', 1)[0]
            module_class_count[module_name] += 1

        for module_name, count in module_class_count.items():
            if count > self.thresholds['NOCC_THRESHOLD']:
                self.structural_smells.append(f"High Number of Classes (NOCC): Module '{module_name}' has {count} classes")

    def detect_dit(self):
        """
        Detect modules with a Deep Inheritance Tree (DIT).

        This method identifies modules with a high number of classes, which may indicate a deep inheritance tree.
        """
        # Simplified DIT detection
        class_hierarchy = defaultdict(list)
        for class_name in self.class_info:
            module_name, class_name = class_name.rsplit('.', 1)
            class_hierarchy[module_name].append(class_name)

        for module_name, classes in class_hierarchy.items():
            if len(classes) > self.thresholds['DIT_THRESHOLD']:
                self.structural_smells.append(f"Deep Inheritance Tree (DIT): Module '{module_name}' has a deep inheritance tree")

    def detect_loc(self):
        for module_name, info in self.module_info.items():
            if info['loc'] > self.thresholds['LOC_THRESHOLD']:
                self.structural_smells.append(f"High Lines of Code (LOC): Module '{module_name}' has {info['loc']} lines")

    def detect_mpc(self):
        # Simplified MPC detection
        for class_name, info in self.class_info.items():
            mpc = len(info['methods'])  # Should count method calls to other classes
            if mpc > self.thresholds['MPC_THRESHOLD']:
                self.structural_smells.append(f"High Message Passing Coupling (MPC): Class '{class_name}' has MPC of {mpc}")

    def detect_cbo(self):
        for node in self.dependency_graph.nodes():
            cbo = self.dependency_graph.degree(node)
            if cbo > self.thresholds['CBO_THRESHOLD']:
                self.structural_smells.append(f"High Coupling Between Object Classes (CBO): Module '{node}' has CBO of {cbo}")

    def detect_noc(self):
        noc = len(self.class_info)
        if noc > self.thresholds['NOC_THRESHOLD']:
            self.structural_smells.append(f"High Number of Classes (NOC): Project has {noc} classes")

    def print_report(self):
        if not self.structural_smells:
            print("No structural smells detected.")
        else:
            print("Detected Structural Smells:")
            for smell in self.structural_smells:
                print(f"- {smell}")

def analyze_structure(directory_path, thresholds):
    detector = StructuralSmellDetector(thresholds)
    detector.detect_smells(directory_path)
    detector.print_report()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Detect structural smells in Python code.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default="code_quality_config.yaml", help="Path to the configuration file")
    args = parser.parse_args()

    from config_handler import ConfigHandler
    config_handler = ConfigHandler(args.config)
    thresholds = config_handler.get_thresholds('structural_smells')

    analyze_structure(args.directory, thresholds)
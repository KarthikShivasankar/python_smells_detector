import os
import ast
import networkx as nx
from collections import defaultdict
from dataclasses import dataclass
import yaml

@dataclass
class StructuralSmell:
    """
    Represents a detected structural smell in the code.

    Attributes:
        name (str): The name of the structural smell.
        description (str): A description of the detected smell.
        file_path (str): The path to the file where the smell was detected.
        module_class (str): The module or class where the smell was detected.
        line_number (int, optional): The line number where the smell was detected.
        severity (str, optional): The severity level of the smell.
    """
    name: str
    description: str
    file_path: str
    module_class: str
    line_number: int = None
    severity: str = ''

class StructuralSmellDetector:
    """
    A class to detect structural smells in Python code.

    This class analyzes Python source code files to identify various structural
    code smells based on predefined thresholds.

    Attributes:
        structural_smells (list): A list to store detected structural smells.
        class_info (defaultdict): A dictionary to store information about classes.
        module_info (defaultdict): A dictionary to store information about modules.
        dependency_graph (nx.DiGraph): A directed graph to represent module dependencies.
        thresholds (dict): A dictionary of threshold values for various smell detections.
        project_root (str): The root directory of the project being analyzed.
        file_paths (dict): A dictionary to store file paths of modules and classes.
    """

    def __init__(self, config):
        """
        Initialize the StructuralSmellDetector with given configuration.

        Args:
            config (dict or str): Either a dictionary of thresholds or a path to a YAML config file.
        """
        self.structural_smells = []
        self.class_info = defaultdict(dict)
        self.module_info = defaultdict(dict)
        self.dependency_graph = nx.DiGraph()
        self.thresholds = self.load_thresholds(config)
        self.project_root = None
        self.file_paths = {}

    def load_thresholds(self, config):
        """
        Load threshold values from the given configuration.

        Args:
            config (dict or str): Either a dictionary of thresholds or a path to a YAML config file.

        Returns:
            dict: A dictionary of threshold values.

        Raises:
            ValueError: If the config is neither a dictionary nor a valid file path.
        """
        if isinstance(config, dict):
            return config
        elif isinstance(config, str):
            with open(config, 'r') as file:
                config_data = yaml.safe_load(file)
            return {k: v['value'] for k, v in config_data['structural_smells'].items()}
        else:
            raise ValueError("Config must be either a dictionary or a file path string")

    def detect_smells(self, directory_path):
        """
        Detect structural smells in the given directory.

        This method analyzes all Python files in the given directory and its subdirectories,
        and runs various smell detection methods.

        Args:
            directory_path (str): The path to the directory to be analyzed.
        """
        try:
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
            self.detect_cyclomatic_complexity()
            self.detect_fanout()
            self.detect_fanin()
            self.detect_file_length()
            self.detect_method_length()
            self.detect_parameters()
            self.detect_returns()
            self.detect_branches()
            self.detect_nesting_depth()
            self.detect_identifier_length()
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

    def analyze_file(self, file_path):
        """
        Analyze a single Python file for structural information.

        Args:
            file_path (str): The path to the Python file to be analyzed.
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            
            tree = ast.parse(content)
            module_name = os.path.relpath(file_path, self.project_root).replace(os.path.sep, '.')[:-3]
            self.module_info[module_name]['loc'] = len(content.split('\n'))
            self.file_paths[module_name] = file_path

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self.analyze_class(node, module_name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        self.dependency_graph.add_edge(module_name, alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.dependency_graph.add_edge(module_name, node.module)
        except SyntaxError as e:
            print(f"Parse error in file {file_path}: {str(e)}")
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")

    def analyze_class(self, node, module_name):
        """
        Analyze a class definition node and extract relevant information.

        Args:
            node (ast.ClassDef): The class definition node to analyze.
            module_name (str): The name of the module containing the class.
        """
        class_name = f"{module_name}.{node.name}"
        self.class_info[class_name]['methods'] = []
        self.class_info[class_name]['fields'] = set()
        self.class_info[class_name]['method_calls'] = defaultdict(set)
        self.class_info[class_name]['base_classes'] = [self.resolve_base_class(base, module_name) for base in node.bases]
        self.class_info[class_name]['loc'] = node.end_lineno - node.lineno + 1

        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                self.class_info[class_name]['methods'].append(child)
                self.analyze_method(child, class_name)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        self.class_info[class_name]['fields'].add(target.id)

    def analyze_method(self, node, class_name):
        """
        Analyze a method definition node and extract relevant information.

        Args:
            node (ast.FunctionDef): The method definition node to analyze.
            class_name (str): The name of the class containing the method.
        """
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    self.class_info[class_name]['method_calls'][node.name].add(child.func.attr)

    def add_smell(self, name, description, file_path, module_class, line_number=None):
        """
        Add a detected smell to the list of structural smells.

        Args:
            name (str): The name of the structural smell.
            description (str): A description of the detected smell.
            file_path (str): The path to the file where the smell was detected.
            module_class (str): The module or class where the smell was detected.
            line_number (int, optional): The line number where the smell was detected.
        """
        self.structural_smells.append(StructuralSmell(
            name=name,
            description=description,
            file_path=file_path,
            module_class=module_class,
            line_number=line_number
        ))

    def detect_nom(self):
        """
        Detect classes with a high Number of Methods (NOM).

        This method identifies classes that exceed the NOM threshold and adds them to the structural smells list.
        """
        for class_name, info in self.class_info.items():
            nom = len(info['methods'])
            if nom > self.thresholds['NOM_THRESHOLD']:
                self.add_smell(
                    "High Number of Methods (NOM)",
                    f"Class '{class_name}' has {nom} methods",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name
                )

    def detect_wmpc(self):
        """
        Detect classes with high Weighted Methods per Class (WMPC).

        This method calculates both WMPC1 (based on cyclomatic complexity) and WMPC2 (based on number of parameters)
        for each class and identifies those exceeding the respective thresholds.
        """
        for class_name, info in self.class_info.items():
            wmpc1 = sum(self.calculate_cyclomatic_complexity(method) for method in info['methods'])
            wmpc2 = sum(len(method.args.args) for method in info['methods'])
            if wmpc1 > self.thresholds['WMPC1_THRESHOLD'] or wmpc2 > self.thresholds['WMPC2_THRESHOLD']:
                self.add_smell(
                    "High Weighted Methods per Class (WMPC)",
                    f"Class '{class_name}' (WMPC1: {wmpc1}, WMPC2: {wmpc2})",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name
                )

    def detect_size2(self):
        """
        Detect large classes based on the SIZE2 metric.

        This method calculates the SIZE2 metric (sum of methods and fields) for each class
        and identifies those exceeding the threshold.
        """
        for class_name, info in self.class_info.items():
            size2 = len(info['methods']) + len(info['fields'])
            if size2 > self.thresholds['SIZE2_THRESHOLD']:
                self.add_smell(
                    "Large Class (SIZE2)",
                    f"Class '{class_name}' has {size2} members",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name
                )

    def detect_wac(self):
        """
        Detect classes with high Weight of a Class (WAC).

        This method counts the number of fields in each class and identifies those exceeding the WAC threshold.
        """
        for class_name, info in self.class_info.items():
            wac = len(info['fields'])
            if wac > self.thresholds['WAC_THRESHOLD']:
                self.add_smell(
                    "High Weight of a Class (WAC)",
                    f"Class '{class_name}' has {wac} attributes",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name
                )

    def detect_lcom(self):
        """
        Detect classes with high Lack of Cohesion of Methods (LCOM).

        This method calculates the LCOM metric for each class and identifies those exceeding the threshold.
        LCOM is calculated as the difference between the number of method pairs not sharing instance variables
        and the number of method pairs sharing instance variables.
        """
        for class_name, info in self.class_info.items():
            methods = info['methods']
            fields = info['fields']
            method_field_usage = {method.name: set() for method in methods}
            
            for method in methods:
                for node in ast.walk(method):
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
                        method_field_usage[method.name].add(node.attr)
            
            non_cohesive_pairs = 0
            cohesive_pairs = 0
            
            for i, method1 in enumerate(methods):
                for method2 in methods[i+1:]:
                    if not method_field_usage[method1.name].intersection(method_field_usage[method2.name]):
                        non_cohesive_pairs += 1
                    else:
                        cohesive_pairs += 1
            
            lcom = max(0, non_cohesive_pairs - cohesive_pairs)
            if lcom > self.thresholds['LCOM_THRESHOLD']:
                self.add_smell(
                    "High Lack of Cohesion of Methods (LCOM)",
                    f"Class '{class_name}' has LCOM of {lcom}",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name
                )

    def detect_rfc(self):
        """
        Detect classes with high Response for a Class (RFC).

        This method calculates the RFC metric (number of methods + number of distinct method calls)
        for each class and identifies those exceeding the threshold.
        """
        for class_name, info in self.class_info.items():
            rfc = len(info['methods']) + sum(len(calls) for calls in info['method_calls'].values())
            if rfc > self.thresholds['RFC_THRESHOLD']:
                self.add_smell(
                    "High Response for a Class (RFC)",
                    f"Class '{class_name}' has RFC of {rfc}",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name
                )

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
                self.add_smell(
                    "High Number of Classes (NOCC)",
                    f"Module '{module_name}' has {count} classes",
                    self.file_paths.get(module_name, "Unknown"),
                    module_name
                )

    def detect_dit(self):
        """
        Detect classes with a Deep Inheritance Tree (DIT).

        This method calculates the depth of inheritance tree for each class and identifies those exceeding the threshold.
        """
        inheritance_graph = nx.DiGraph()
        
        for class_name, info in self.class_info.items():
            inheritance_graph.add_node(class_name)
            for base in info['base_classes']:
                inheritance_graph.add_edge(base, class_name)
        
        if 'object' not in inheritance_graph:
            inheritance_graph.add_node('object')
            for node in inheritance_graph.nodes():
                if inheritance_graph.in_degree(node) == 0 and node != 'object':
                    inheritance_graph.add_edge('object', node)
        
        for class_name in inheritance_graph.nodes():
            if class_name != 'object':
                try:
                    dit = nx.shortest_path_length(inheritance_graph, 'object', class_name)
                    if dit > self.thresholds['DIT_THRESHOLD']:
                        self.add_smell(
                            "Deep Inheritance Tree (DIT)",
                            f"Class '{class_name}' has DIT of {dit}",
                            self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                            class_name
                        )
                except nx.NetworkXNoPath:
                    self.add_smell(
                        "Isolated Class in Inheritance Tree",
                        f"Class '{class_name}' is isolated",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name
                    )

    def detect_loc(self):
        """
        Detect modules with high Lines of Code (LOC).

        This method counts the number of lines in each module and identifies those exceeding the LOC threshold.
        """
        for module_name, info in self.module_info.items():
            if info['loc'] > self.thresholds['LOC_THRESHOLD']:
                self.add_smell(
                    "High Lines of Code (LOC)",
                    f"Module '{module_name}' has {info['loc']} lines",
                    self.file_paths.get(module_name, "Unknown"),
                    module_name
                )

    def detect_mpc(self):
        """
        Detect classes with high Message Passing Coupling (MPC).

        This method calculates the MPC metric (number of method calls to other classes)
        for each class and identifies those exceeding the threshold.
        """
        for class_name, info in self.class_info.items():
            mpc = sum(len(calls) for calls in info['method_calls'].values())
            if mpc > self.thresholds['MPC_THRESHOLD']:
                self.add_smell(
                    "High Message Passing Coupling (MPC)",
                    f"Class '{class_name}' has MPC of {mpc}",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name
                )

    def detect_cbo(self):
        """
        Detect modules with high Coupling Between Object Classes (CBO).

        This method calculates the CBO metric (number of other classes a class is coupled to)
        for each module and identifies those exceeding the threshold.
        """
        for node in self.dependency_graph.nodes():
            cbo = self.dependency_graph.degree(node)
            if cbo > self.thresholds['CBO_THRESHOLD']:
                self.add_smell(
                    "High Coupling Between Object Classes (CBO)",
                    f"Module '{node}' has CBO of {cbo}",
                    self.file_paths.get(node, "Unknown"),
                    node
                )

    def detect_noc(self):
        """
        Detect projects with a high Number of Classes (NOC).

        This method counts the total number of classes in the project and identifies if it exceeds the NOC threshold.
        """
        noc = len(self.class_info)
        if noc > self.thresholds['NOC_THRESHOLD']:
            self.add_smell(
                "High Number of Classes (NOC)",
                f"Project has {noc} classes",
                self.project_root,
                "Project"
            )

    def calculate_cyclomatic_complexity(self, method_node):
        """
        Calculate the cyclomatic complexity of a method.

        Args:
            method_node (ast.FunctionDef): The AST node of the method.

        Returns:
            int: The cyclomatic complexity of the method.
        """
        complexity = 1
        for node in ast.walk(method_node):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                if isinstance(node.op, ast.And) or isinstance(node.op, ast.Or):
                    complexity += len(node.values) - 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers) + len(node.finalbody)
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.Assert):
                complexity += 1
            elif isinstance(node, ast.Return) and isinstance(node.value, ast.Compare):
                complexity += len(node.value.ops)
        return complexity

    def resolve_base_class(self, base_node, current_module):
        """
        Resolve the full name of a base class.

        Args:
            base_node (ast.expr): The AST node representing the base class.
            current_module (str): The name of the current module.

        Returns:
            str: The full name of the base class.
        """
        if isinstance(base_node, ast.Name):
            return f"{current_module}.{base_node.id}"
        elif isinstance(base_node, ast.Attribute):
            return f"{base_node.value.id}.{base_node.attr}"
        else:
            return 'object'

    def print_report(self):
        """
        Print a report of all detected structural smells.
        """
        if not self.structural_smells:
            print("No structural smells detected.")
        else:
            print("Detected Structural Smells:")
            for smell in self.structural_smells:
                print(f"- {smell}")

    def detect_cyclomatic_complexity(self):
        """
        Detect methods with high cyclomatic complexity.

        This method calculates the cyclomatic complexity of each method and identifies those exceeding the threshold.
        """
        for class_name, info in self.class_info.items():
            for method in info['methods']:
                complexity = self.calculate_cyclomatic_complexity(method)
                if complexity > self.thresholds['CYCLOMATIC_COMPLEXITY_THRESHOLD']:
                    self.add_smell(
                        "High Cyclomatic Complexity",
                        f"Method '{method.name}' in class '{class_name}' has complexity of {complexity}",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name,
                        method.lineno
                    )

    def detect_fanout(self):
        """
        Detect modules with high fan-out.

        This method calculates the fan-out (number of outgoing dependencies) for each module
        and identifies those exceeding the threshold.
        """
        for module in self.dependency_graph.nodes():
            fanout = self.dependency_graph.out_degree(module)
            if fanout > self.thresholds['MAX_FANOUT']:
                self.add_smell(
                    "High Fan-out",
                    f"Module '{module}' has fan-out of {fanout}",
                    self.file_paths.get(module, "Unknown"),
                    module
                )

    def detect_fanin(self):
        """
        Detect modules with high fan-in.

        This method calculates the fan-in (number of incoming dependencies) for each module
        and identifies those exceeding the threshold.
        """
        for module in self.dependency_graph.nodes():
            fanin = self.dependency_graph.in_degree(module)
            if fanin > self.thresholds['MAX_FANIN']:
                self.add_smell(
                    "High Fan-in",
                    f"Module '{module}' has fan-in of {fanin}",
                    self.file_paths.get(module, "Unknown"),
                    module
                )

    def detect_file_length(self):
        """
        Detect files with excessive length.

        This method identifies files that exceed the maximum file length threshold.
        """
        for module_name, info in self.module_info.items():
            if info['loc'] > self.thresholds['MAX_FILE_LENGTH']:
                self.add_smell(
                    "Long File",
                    f"File '{module_name}' has {info['loc']} lines",
                    self.file_paths.get(module_name, "Unknown"),
                    module_name
                )

    def detect_method_length(self):
        """
        Detect methods with excessive length.

        This method identifies methods that exceed the maximum method length threshold.
        """
        for class_name, info in self.class_info.items():
            for method in info['methods']:
                method_length = method.end_lineno - method.lineno + 1
                if method_length > self.thresholds['MAX_METHOD_LENGTH']:
                    self.add_smell(
                        "Long Method",
                        f"Method '{method.name}' in class '{class_name}' has {method_length} lines",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name,
                        method.lineno
                    )

    def detect_parameters(self):
        """
        Detect methods with too many parameters.

        This method identifies methods that exceed the maximum number of parameters threshold.
        """
        for class_name, info in self.class_info.items():
            for method in info['methods']:
                param_count = len(method.args.args) - 1  # Subtract 1 for 'self'
                if param_count > self.thresholds['MAX_PARAMETERS']:
                    self.add_smell(
                        "Too Many Parameters",
                        f"Method '{method.name}' in class '{class_name}' has {param_count} parameters",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name,
                        method.lineno
                    )

    def detect_returns(self):
        """
        Detect methods with too many return statements.

        This method identifies methods that exceed the maximum number of return statements threshold.
        """
        for class_name, info in self.class_info.items():
            for method in info['methods']:
                return_count = sum(1 for node in ast.walk(method) if isinstance(node, ast.Return))
                if return_count > self.thresholds['MAX_RETURNS']:
                    self.add_smell(
                        "Too Many Return Statements",
                        f"Method '{method.name}' in class '{class_name}' has {return_count} return statements",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name,
                        method.lineno
                    )

    def detect_branches(self):
        """
        Detect methods with too many branches.

        This method identifies methods that exceed the maximum number of branches threshold.
        Branches include if statements, for loops, while loops, and try-except blocks.
        """
        for class_name, info in self.class_info.items():
            for method in info['methods']:
                branch_count = sum(1 for node in ast.walk(method) if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)))
                if branch_count > self.thresholds['MAX_BRANCHES']:
                    self.add_smell(
                        "Too Many Branches",
                        f"Method '{method.name}' in class '{class_name}' has {branch_count} branches",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name,
                        method.lineno
                    )

    def detect_nesting_depth(self):
        """
        Detect methods with excessive nesting depth.

        This method identifies methods that exceed the maximum nesting depth threshold.
        """
        for class_name, info in self.class_info.items():
            for method in info['methods']:
                max_depth = self.calculate_max_nesting_depth(method)
                if max_depth > self.thresholds['MAX_NESTING_DEPTH']:
                    self.add_smell(
                        "Deep Nesting",
                        f"Method '{method.name}' in class '{class_name}' has nesting depth of {max_depth}",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name,
                        method.lineno
                    )

    def detect_identifier_length(self):
        """
        Detect identifiers (class names, method names, field names) that are too short or too long.

        This method identifies identifiers that are shorter than the minimum or longer than the maximum
        identifier length thresholds.
        """
        for class_name, info in self.class_info.items():
            self.check_identifier_length(class_name, class_name.split('.')[-1])
            for method in info['methods']:
                self.check_identifier_length(class_name, method.name, method.lineno)
            for field in info['fields']:
                self.check_identifier_length(class_name, field)

    def check_identifier_length(self, class_name, identifier, line_number=None):
        """
        Check if an identifier's length is within the acceptable range.

        Args:
            class_name (str): The name of the class containing the identifier.
            identifier (str): The identifier to check.
            line_number (int, optional): The line number where the identifier is defined.
        """
        if len(identifier) < self.thresholds['MIN_IDENTIFIER_LENGTH']:
            self.add_smell(
                "Short Identifier",
                f"Identifier '{identifier}' in class '{class_name}' is too short",
                self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                class_name,
                line_number
            )
        elif len(identifier) > self.thresholds['MAX_IDENTIFIER_LENGTH']:
            self.add_smell(
                "Long Identifier",
                f"Identifier '{identifier}' in class '{class_name}' is too long",
                self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                class_name,
                line_number
            )

    def calculate_max_nesting_depth(self, node, current_depth=0):
        """
        Calculate the maximum nesting depth of a given AST node.

        Args:
            node (ast.AST): The AST node to analyze.
            current_depth (int): The current nesting depth.

        Returns:
            int: The maximum nesting depth found in the node and its children.
        """
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                child_depth = self.calculate_max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth

def analyze_structure(directory_path, config):
    """
    Analyze the structural smells in a given directory.

    Args:
        directory_path (str): The path to the directory to analyze.
        config (dict or str): Either a dictionary of thresholds or a path to a YAML config file.
    """
    detector = StructuralSmellDetector(config)
    detector.detect_smells(directory_path)
    detector.print_report()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Detect structural smells in Python code.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default="code_quality_config.yaml", help="Path to the configuration file")
    args = parser.parse_args()

    analyze_structure(args.directory, args.config)
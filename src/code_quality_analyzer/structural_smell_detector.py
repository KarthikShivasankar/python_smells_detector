import os
import ast
import networkx as nx
from collections import defaultdict
from dataclasses import dataclass
import yaml
import logging
from .exceptions import CodeAnalysisError

# Set up logger
logger = logging.getLogger(__name__)

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
        self.module_dependencies = nx.DiGraph()
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
        """
        detection_methods = [
            (self.detect_nom, "detect_nom"),
            (self.detect_lcom, "detect_lcom"),
            (self.detect_rfc, "detect_rfc"),
            (self.detect_nocc, "detect_nocc"),
            (self.detect_dit, "detect_dit"),
            (self.detect_loc, "detect_loc"),
            (self.detect_noc, "detect_noc"),
            (self.detect_cyclomatic_complexity, "detect_cyclomatic_complexity"),
            (self.detect_fanout, "detect_fanout"),
            (self.detect_fanin, "detect_fanin"),
            (self.detect_file_length, "detect_file_length"),
            (self.detect_branches, "detect_branches")
        ]

        try:
            # First analyze the directory structure
            logger.info(f"Analyzing directory structure: {directory_path}")
            self.analyze_directory(directory_path)
            
            if not self.module_info:
                logger.warning("No modules were successfully analyzed. Skipping smell detection.")
                return
            
            # Then run each detection method
            for detect_method, method_name in detection_methods:
                try:
                    logger.debug(f"Running {method_name}")
                    detect_method()
                    logger.debug(f"Completed {method_name}. Total smells so far: {len(self.structural_smells)}")
                except Exception as e:
                    logger.error(f"Error in {method_name}: {str(e)}", exc_info=True)
                    # Continue with next detection method instead of stopping
                    continue
                
        except Exception as e:
            logger.error(f"Error analyzing directory {directory_path}: {str(e)}", exc_info=True)
            raise CodeAnalysisError(
                message=str(e),
                file_path=directory_path
            )

        # Log final results
        logger.info(f"Analysis complete. Found {len(self.structural_smells)} structural smells.")

    def analyze_directory(self, directory_path):
        """
        Analyze all Python files in the given directory and its subdirectories.

        Args:
            directory_path (str): The path to the directory to be analyzed.
        """
        self.project_root = os.path.abspath(directory_path)
        files_analyzed = 0
        files_with_errors = 0
        
        logger.info(f"Starting analysis of directory: {directory_path}")
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        self.analyze_file(file_path)
                        files_analyzed += 1
                        logger.debug(f"Successfully analyzed: {file_path}")
                    except CodeAnalysisError as e:
                        files_with_errors += 1
                        logger.warning(f"Error analyzing {file_path}: {str(e)}")
                        # Continue with next file instead of stopping
                        continue
                    except Exception as e:
                        files_with_errors += 1
                        logger.error(f"Unexpected error analyzing {file_path}: {str(e)}")
                        continue

        # Log analysis summary
        logger.info(f"""
Analysis Summary:
----------------
Files analyzed: {files_analyzed}
Files with errors: {files_with_errors}
Success rate: {((files_analyzed - files_with_errors) / max(files_analyzed, 1) * 100):.1f}%
        """)

        if files_analyzed == 0:
            logger.warning("No Python files were successfully analyzed!")
        elif files_with_errors > 0:
            logger.warning(f"{files_with_errors} files could not be analyzed due to errors")

    def analyze_file(self, file_path):
        """
        Analyze a single Python file for structural information.

        Args:
            file_path (str): The path to the Python file to be analyzed.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                logger.error(f"Syntax error in {file_path}: {str(e)}")
                raise CodeAnalysisError(
                    message=f"Parse error: {str(e)}",
                    file_path=file_path,
                    line_number=getattr(e, 'lineno', None)
                )
            
            # Get relative module path
            rel_path = os.path.relpath(file_path, self.project_root)
            module_name = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
            
            self.module_info[module_name]['loc'] = len(content.splitlines())
            self.file_paths[module_name] = file_path
            
            # Add node to dependency graph
            self.module_dependencies.add_node(module_name)
            self.dependency_graph.add_node(module_name)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self.analyze_class(node, module_name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        self.dependency_graph.add_edge(module_name, alias.name)
                        self.module_dependencies.add_edge(module_name, alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.dependency_graph.add_edge(module_name, node.module)
                        self.module_dependencies.add_edge(module_name, node.module)
                        
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error in {file_path}: {str(e)}")
            raise CodeAnalysisError(
                message=f"File encoding error: {str(e)}",
                file_path=file_path
            )
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            raise CodeAnalysisError(
                message=f"Analysis error: {str(e)}",
                file_path=file_path
            )

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

    def add_smell(self, name, description, file_path, module_class, line_number=None, severity='medium'):
        """
        Add a detected structural smell to the list.
        
        Args:
            name (str): The name of the smell
            description (str): Description of the smell
            file_path (str): Path to the file containing the smell
            module_class (str): The module or class containing the smell
            line_number (int, optional): The line number where the smell was detected
            severity (str, optional): The severity level of the smell (default: 'medium')
        """
        self.structural_smells.append(StructuralSmell(
            name=name,
            description=description,
            file_path=file_path,
            module_class=module_class,
            line_number=line_number,
            severity=severity
        ))

    def detect_nom(self):
        """
        Detect classes with a high Number of Methods (NOM).
        """
        threshold = self.thresholds.get('NOM_THRESHOLD')
        if not threshold:
            logger.warning("NOM_THRESHOLD not found in configuration, using default value of 10")
            threshold = 10

        logger.info(f"Detecting NOM smells with threshold: {threshold}")

        for class_name, info in self.class_info.items():
            # Filter out special methods and properties
            regular_methods = [m for m in info['methods'] 
                             if not (m.name.startswith('__') and m.name.endswith('__')) 
                             and not any(isinstance(d, ast.Name) and d.id == 'property' 
                                       for d in getattr(m, 'decorator_list', []))]
            
            nom = len(regular_methods)
            if nom > threshold:
                severity = 'High' if nom > threshold * 1.5 else 'Medium'
                smell = StructuralSmell(
                    name="High Number of Methods (NOM)",
                    description=f"Class '{class_name}' has {nom} methods (excluding special methods and properties)",
                    file_path=self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    module_class=class_name,
                    severity=severity
                )
                self.structural_smells.append(smell)
                logger.info(f"Detected NOM smell in {class_name}: {nom} methods")

    def detect_wmpc(self):
        """
        Detect classes with high Weighted Methods per Class (WMPC).

        This method calculates both WMPC1 (based on cyclomatic complexity) and WMPC2 (based on number of parameters)
        for each class and identifies those exceeding the respective thresholds.
        Considers method visibility and excludes simple getter/setter methods.
        """
        for class_name, info in self.class_info.items():
            # Filter out simple getters/setters and special methods
            complex_methods = []
            for method in info['methods']:
                # Skip special methods
                if method.name.startswith('__') and method.name.endswith('__'):
                    continue
                
                # Check if it's a simple getter/setter
                is_simple = True
                for node in ast.walk(method):
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                        is_simple = False
                        break
                
                if not is_simple:
                    complex_methods.append(method)

            wmpc1 = sum(self.calculate_cyclomatic_complexity(method) for method in complex_methods)
            wmpc2 = sum(len(method.args.args) - 1 for method in complex_methods)  # Subtract 1 for 'self'
            
            if wmpc1 > self.thresholds['WMPC1_THRESHOLD'] or wmpc2 > self.thresholds['WMPC2_THRESHOLD']:
                severity = 'High' if (wmpc1 > self.thresholds['WMPC1_THRESHOLD'] * 1.5 or 
                                    wmpc2 > self.thresholds['WMPC2_THRESHOLD'] * 1.5) else 'Medium'
                self.add_smell(
                    "High Weighted Methods per Class (WMPC)",
                    f"Class '{class_name}' has complex methods (WMPC1: {wmpc1}, WMPC2: {wmpc2})",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity=severity
                )

    def detect_size2(self):
        """
        Detect large classes based on the SIZE2 metric.

        This method calculates the SIZE2 metric (sum of methods and fields) for each class
        and identifies those exceeding the threshold. Considers visibility and usage patterns.
        """
        for class_name, info in self.class_info.items():
            # Count significant members (excluding private/protected members with limited usage)
            significant_methods = [m for m in info['methods'] 
                                if not m.name.startswith('_') or 
                                any(call for calls in info['method_calls'].values() 
                                    for call in calls if call == m.name)]
            
            significant_fields = {f for f in info['fields'] 
                                if not f.startswith('_') or 
                                any(node.attr == f 
                                    for method in info['methods'] 
                                    for node in ast.walk(method) 
                                    if isinstance(node, ast.Attribute))}
            
            size2 = len(significant_methods) + len(significant_fields)
            if size2 > self.thresholds['SIZE2_THRESHOLD']:
                severity = 'High' if size2 > self.thresholds['SIZE2_THRESHOLD'] * 1.5 else 'Medium'
                self.add_smell(
                    "Large Class (SIZE2)",
                    f"Class '{class_name}' has {size2} significant members (methods: {len(significant_methods)}, fields: {len(significant_fields)})",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity=severity
                )

    def detect_wac(self):
        """
        Detect classes with high Weight of a Class (WAC).

        This method counts the number of fields in each class and identifies those exceeding the WAC threshold.
        Considers field visibility, type, and usage patterns to avoid false positives.
        """
        for class_name, info in self.class_info.items():
            # Filter fields based on visibility and usage
            significant_fields = set()
            
            for field in info['fields']:
                # Skip constants (uppercase fields)
                if field.isupper():
                    continue
                
                # Check field usage in methods
                field_usage = sum(1 for method in info['methods']
                                for node in ast.walk(method)
                                if isinstance(node, ast.Attribute) and 
                                isinstance(node.value, ast.Name) and 
                                node.value.id == 'self' and 
                                node.attr == field)
                
                # Include field if it's public or frequently used
                if not field.startswith('_') or field_usage > 1:
                    significant_fields.add(field)
            
            wac = len(significant_fields)
            if wac > self.thresholds['WAC_THRESHOLD']:
                severity = 'High' if wac > self.thresholds['WAC_THRESHOLD'] * 1.5 else 'Medium'
                self.add_smell(
                    "High Weight of a Class (WAC)",
                    f"Class '{class_name}' has {wac} significant attributes (excluding constants and unused private fields)",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity=severity
                )

    def detect_lcom(self):
        """
        Detect classes with high Lack of Cohesion of Methods (LCOM).
        Uses an improved LCOM calculation that considers:
        - Method visibility (private/protected/public)
        - Special methods and properties
        - Indirect field access through helper methods
        - Constructor field initialization
        """
        for class_name, info in self.class_info.items():
            # Filter out special methods and properties
            regular_methods = [m for m in info['methods'] 
                             if not (m.name.startswith('__') and m.name.endswith('__'))
                             and not any(isinstance(d, ast.Name) and d.id == 'property' 
                                       for d in getattr(m, 'decorator_list', []))]
            
            if len(regular_methods) < 2:  # Skip classes with too few methods
                continue
                
            # Build field usage map including indirect access
            method_field_usage = self._build_field_usage_map(regular_methods, info)
            
            # Calculate cohesion metrics
            non_cohesive_pairs = 0
            cohesive_pairs = 0
            
            for i, method1 in enumerate(regular_methods):
                for method2 in regular_methods[i+1:]:
                    # Skip pairs of private methods as they might be helper methods
                    if method1.name.startswith('_') and method2.name.startswith('_'):
                        continue
                        
                    shared_fields = method_field_usage[method1.name].intersection(
                        method_field_usage[method2.name])
                    
                    if not shared_fields:
                        non_cohesive_pairs += 1
                    else:
                        cohesive_pairs += 1
            
            if non_cohesive_pairs == 0 and cohesive_pairs == 0:
                continue  # Skip classes with no meaningful method pairs
                
            lcom = max(0, non_cohesive_pairs - cohesive_pairs)
            if lcom > self.thresholds['LCOM_THRESHOLD']:
                severity = 'High' if lcom > self.thresholds['LCOM_THRESHOLD'] * 1.5 else 'Medium'
                self.add_smell(
                    "High Lack of Cohesion of Methods (LCOM)",
                    f"Class '{class_name}' has LCOM of {lcom} (non-cohesive: {non_cohesive_pairs}, cohesive: {cohesive_pairs})",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity=severity
                )

    def _build_field_usage_map(self, methods, info):
        """Helper method to build comprehensive field usage map."""
        method_field_usage = {method.name: set() for method in methods}
        method_calls = info['method_calls']
        
        # First pass: direct field access
        for method in methods:
            for node in ast.walk(method):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    if node.value.id == 'self':
                        method_field_usage[method.name].add(node.attr)
        
        # Second pass: indirect access through method calls
        changed = True
        while changed:  # Keep propagating until no changes
            changed = False
            for method in methods:
                current_fields = method_field_usage[method.name].copy()
                # Add fields used by called methods
                for called_method in method_calls.get(method.name, set()):
                    if called_method in method_field_usage:
                        new_fields = method_field_usage[called_method]
                        if not new_fields.issubset(current_fields):
                            method_field_usage[method.name].update(new_fields)
                            changed = True
        
        return method_field_usage

    def detect_rfc(self):
        """
        Detect classes with high Response for a Class (RFC).
        Enhanced to consider:
        - Method visibility and importance
        - External vs internal calls
        - Framework-specific methods
        - Standard library calls
        """
        standard_lib_prefixes = {'os.', 'sys.', 'datetime.', 'collections.', 'json.'}
        
        for class_name, info in self.class_info.items():
            # Count significant methods (excluding simple getters/setters)
            significant_methods = []
            for method in info['methods']:
                if method.name.startswith('__') and method.name.endswith('__'):
                    continue
                    
                # Check if it's a simple accessor
                is_simple = True
                for node in ast.walk(method):
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                        is_simple = False
                        break
                
                if not is_simple or not method.name.startswith('_'):
                    significant_methods.append(method)
            
            # Count unique external method calls
            external_calls = set()
            for calls in info['method_calls'].values():
                for call in calls:
                    # Skip standard library calls
                    if any(call.startswith(prefix) for prefix in standard_lib_prefixes):
                        continue
                    # Skip self calls
                    if not any(m.name == call for m in info['methods']):
                        external_calls.add(call)
            
            rfc = len(significant_methods) + len(external_calls)
            if rfc > self.thresholds['RFC_THRESHOLD']:
                severity = 'High' if rfc > self.thresholds['RFC_THRESHOLD'] * 1.5 else 'Medium'
                self.add_smell(
                    "High Response for a Class (RFC)",
                    f"Class '{class_name}' has RFC of {rfc} (methods: {len(significant_methods)}, external calls: {len(external_calls)})",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity=severity
                )

    def detect_nocc(self):
        """
        Detect modules with a high Number of Classes (NOCC).
        Enhanced to consider:
        - Class size and complexity
        - Inner classes
        - Test classes
        - Exception classes
        """
        module_class_info = defaultdict(list)
        
        for class_name, info in self.class_info.items():
            module_name = class_name.rsplit('.', 1)[0]
            
            # Skip test classes
            if 'test' in class_name.lower():
                continue
                
            # Skip exception classes
            if any(base.endswith('Exception') for base in info['base_classes']):
                continue
            
            # Calculate class weight based on size and complexity
            class_weight = (
                len(info['methods']) +
                len(info['fields']) +
                sum(self.calculate_cyclomatic_complexity(m) for m in info['methods'])
            ) / 3  # Normalize
            
            module_class_info[module_name].append((class_name, class_weight))
        
        for module_name, classes in module_class_info.items():
            # Consider both count and weighted complexity
            count = len(classes)
            avg_weight = sum(weight for _, weight in classes) / count if count > 0 else 0
            
            # Adjust threshold based on average class complexity
            adjusted_threshold = self.thresholds['NOCC_THRESHOLD']
            if avg_weight < 5:  # Simple classes
                adjusted_threshold *= 1.5
            elif avg_weight > 15:  # Complex classes
                adjusted_threshold *= 0.7
            
            if count > adjusted_threshold:
                severity = 'High' if count > adjusted_threshold * 1.5 else 'Medium'
                self.add_smell(
                    "High Number of Classes (NOCC)",
                    f"Module '{module_name}' has {count} significant classes (avg complexity: {avg_weight:.1f})",
                    self.file_paths.get(module_name, "Unknown"),
                    module_name,
                    severity=severity
                )

    def detect_dit(self):
        """
        Detect classes with a Deep Inheritance Tree (DIT).
        Enhanced to consider:
        - Framework/library base classes
        - Mixin classes
        - Interface-like classes
        - Abstract base classes
        """
        inheritance_graph = nx.DiGraph()
        framework_bases = {'object', 'Exception', 'dict', 'list', 'set', 'tuple', 'str', 'int', 'float'}
        
        for class_name, info in self.class_info.items():
            inheritance_graph.add_node(class_name)
            significant_bases = []
            
            for base in info['base_classes']:
                # Skip framework/library base classes
                base_name = base.split('.')[-1]
                if base_name in framework_bases:
                    continue
                    
                # Skip Mixin classes
                if 'Mixin' in base_name or 'Interface' in base_name:
                    continue
                    
                # Skip abstract base classes (if they have ABC in name or are mostly abstract methods)
                if 'ABC' in base_name or 'Abstract' in base_name:
                    continue
                    
                significant_bases.append(base)
                inheritance_graph.add_edge(base, class_name)
        
        # Add 'object' as root if needed
        if 'object' not in inheritance_graph and inheritance_graph.nodes():
            inheritance_graph.add_node('object')
            for node in list(inheritance_graph.nodes()):
                if inheritance_graph.in_degree(node) == 0 and node != 'object':
                    inheritance_graph.add_edge('object', node)
        
        for class_name in inheritance_graph.nodes():
            if class_name != 'object':
                try:
                    dit = nx.shortest_path_length(inheritance_graph, 'object', class_name)
                    if dit > self.thresholds['DIT_THRESHOLD']:
                        severity = 'High' if dit > self.thresholds['DIT_THRESHOLD'] * 1.5 else 'Medium'
                        inheritance_path = '->'.join(nx.shortest_path(inheritance_graph, 'object', class_name))
                        self.add_smell(
                            "Deep Inheritance Tree (DIT)",
                            f"Class '{class_name}' has DIT of {dit}\nInheritance path: {inheritance_path}",
                            self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                            class_name,
                            severity=severity
                        )
                except nx.NetworkXNoPath:
                    # Only report if it's not a framework/library class
                    if not any(base in class_name for base in framework_bases):
                        self.add_smell(
                            "Isolated Class in Inheritance Tree",
                            f"Class '{class_name}' is isolated from the main inheritance hierarchy",
                            self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                            class_name,
                            severity='Low'
                        )

    def detect_loc(self):
        """
        Detect modules with high Lines of Code (LOC).
        """
        for module_name, info in self.module_info.items():
            try:
                file_path = self.file_paths.get(module_name, "")
                if not file_path or not os.path.exists(file_path):
                    continue

                # Try different encodings
                encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
                content = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as file:
                            content = file.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    logger.warning(f"Could not read file {file_path} with any supported encoding")
                    continue

                # Count different types of lines
                lines = content.splitlines()
                code_lines = 0
                doc_lines = 0
                import_lines = 0
                blank_lines = 0
                
                in_docstring = False
                for line in lines:
                    stripped = line.strip()
                    
                    # Skip blank lines
                    if not stripped:
                        blank_lines += 1
                        continue
                        
                    # Handle docstrings
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        in_docstring = not in_docstring
                        doc_lines += 1
                        continue
                    
                    if in_docstring:
                        doc_lines += 1
                        continue
                        
                    # Handle imports
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        import_lines += 1
                        continue
                        
                    # Handle comments
                    if stripped.startswith('#'):
                        continue
                        
                    code_lines += 1
                
                # Calculate effective LOC and complexity ratio
                effective_loc = code_lines
                complexity_ratio = effective_loc / (len(lines) - blank_lines) if len(lines) - blank_lines > 0 else 1
                
                # Adjust threshold based on module type
                adjusted_threshold = self.thresholds['LOC_THRESHOLD']
                if 'test' in module_name.lower():
                    adjusted_threshold *= 1.5  # Allow test files to be longer
                if complexity_ratio < 0.5:
                    adjusted_threshold *= 1.3  # Allow more lines if much of it is documentation
                
                if effective_loc > adjusted_threshold:
                    severity = 'High' if effective_loc > adjusted_threshold * 1.5 else 'Medium'
                    self.add_smell(
                        name="High Lines of Code (LOC)",
                        description=f"Module '{module_name}' has {effective_loc} effective code lines\n"
                        f"(Total: {len(lines)}, Code: {code_lines}, Doc: {doc_lines}, "
                        f"Import: {import_lines}, Blank: {blank_lines})",
                        file_path=file_path,
                        module_class=module_name,
                        severity=severity
                    )
            except Exception as e:
                logger.error(f"Error analyzing LOC for {module_name}: {str(e)}")
                continue

    def detect_mpc(self):
        """
        Detect classes with high Message Passing Coupling (MPC).
        Enhanced to consider:
        - Method visibility
        - Call frequency
        - Standard library calls
        - Internal vs external coupling
        - Framework-specific patterns
        """
        standard_lib_prefixes = {'os.', 'sys.', 'datetime.', 'collections.', 'json.', 'logging.'}
        framework_patterns = {'get_', 'set_', 'is_', 'has_', '__'}
        
        for class_name, info in self.class_info.items():
            # Track unique external calls and their frequencies
            method_calls = defaultdict(int)
            internal_calls = set()
            
            for method_name, calls in info['method_calls'].items():
                for call in calls:
                    # Skip standard library calls
                    if any(call.startswith(prefix) for prefix in standard_lib_prefixes):
                        continue
                        
                    # Skip framework-specific patterns
                    if any(call.startswith(pattern) for pattern in framework_patterns):
                        continue
                        
                    # Track internal vs external calls
                    if any(m.name == call for m in info['methods']):
                        internal_calls.add(call)
                    else:
                        method_calls[call] += 1
            
            # Calculate weighted MPC
            external_mpc = sum(freq for freq in method_calls.values())
            internal_mpc = len(internal_calls)
            weighted_mpc = external_mpc * 1.5 + internal_mpc  # External calls weighted more heavily
            
            if weighted_mpc > self.thresholds['MPC_THRESHOLD']:
                severity = 'High' if weighted_mpc > self.thresholds['MPC_THRESHOLD'] * 1.5 else 'Medium'
                self.add_smell(
                    "High Message Passing Coupling (MPC)",
                    f"Class '{class_name}' has weighted MPC of {weighted_mpc:.1f}\n"
                    f"(External calls: {external_mpc}, Internal calls: {internal_mpc})\n"
                    f"Most frequent external calls: {dict(sorted(method_calls.items(), key=lambda x: x[1], reverse=True)[:3])}",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity=severity
                )

    def detect_cbo(self):
        """
        Detect modules with high Coupling Between Object Classes (CBO).
        Enhanced to consider:
        - Direct vs indirect coupling
        - Framework/library dependencies
        - Test dependencies
        - Internal vs external coupling
        - Strength of coupling
        """
        standard_libs = {'os', 'sys', 'datetime', 'collections', 'json', 'logging', 're', 'math'}
        framework_patterns = {'test_', 'mock_', 'stub_', 'fake_'}
        
        for class_name, info in self.class_info.items():
            # Track different types of coupling
            direct_coupling = set()
            indirect_coupling = set()
            
            # Analyze method calls and attribute access
            for method in info['methods']:
                for node in ast.walk(method):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute):
                            # Get the base object being called
                            base_obj = self._get_base_object(node.func)
                            if base_obj and not self._is_excluded_dependency(base_obj, standard_libs, framework_patterns):
                                direct_coupling.add(base_obj)
                    
                    elif isinstance(node, ast.Attribute):
                        base_obj = self._get_base_object(node)
                        if base_obj and not self._is_excluded_dependency(base_obj, standard_libs, framework_patterns):
                            indirect_coupling.add(base_obj)
            
            # Analyze inheritance and composition
            for base in info['base_classes']:
                if not self._is_excluded_dependency(base, standard_libs, framework_patterns):
                    direct_coupling.add(base)
            
            # Calculate weighted CBO
            direct_cbo = len(direct_coupling)
            indirect_cbo = len(indirect_coupling)
            weighted_cbo = direct_cbo * 1.5 + indirect_cbo * 0.5
            
            if weighted_cbo > self.thresholds['CBO_THRESHOLD']:
                severity = self._calculate_cbo_severity(weighted_cbo, self.thresholds['CBO_THRESHOLD'])
                self.add_smell(
                    "High Coupling Between Object Classes (CBO)",
                    f"Class '{class_name}' has weighted CBO of {weighted_cbo:.1f}\n"
                    f"Direct coupling: {direct_cbo} classes\n"
                    f"Indirect coupling: {indirect_cbo} classes\n"
                    f"Most significant dependencies: {sorted(direct_coupling)[:3]}",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity=severity
                )

    def _get_base_object(self, node):
        """
        Get the base object name from an attribute node.
        
        Args:
            node (ast.AST): The AST node to analyze.
            
        Returns:
            str: The base object name, or None if it cannot be determined.
        """
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                if node.value.id != 'self':
                    return node.value.id
            elif isinstance(node.value, ast.Attribute):
                return self._get_base_object(node.value)
        return None

    def _is_excluded_dependency(self, name, standard_libs, framework_patterns):
        """
        Check if a dependency should be excluded from coupling calculations.
        
        Args:
            name (str): The name to check.
            standard_libs (set): Set of standard library names.
            framework_patterns (set): Set of framework-specific patterns.
            
        Returns:
            bool: True if the dependency should be excluded, False otherwise.
        """
        # Check standard library
        if any(name.startswith(lib) for lib in standard_libs):
            return True
            
        # Check framework patterns
        if any(pattern in name.lower() for pattern in framework_patterns):
            return True
            
        # Check utility/helper classes
        if 'utils' in name.lower() or 'helper' in name.lower():
            return True
            
        # Check common base classes
        if name in {'object', 'Exception', 'dict', 'list', 'set'}:
            return True
            
        return False

    def _calculate_cbo_severity(self, weighted_cbo, threshold):
        """
        Calculate the severity of a CBO smell based on how much it exceeds the threshold.
        
        Args:
            weighted_cbo (float): The weighted CBO value.
            threshold (float): The CBO threshold.
            
        Returns:
            str: The severity level ('Low', 'Medium', or 'High').
        """
        if weighted_cbo > threshold * 2:
            return 'High'
        elif weighted_cbo > threshold * 1.5:
            return 'Medium'
        return 'Low'

    def detect_noc(self):
        """
        Detect projects with a high Number of Classes (NOC).
        Enhanced to consider:
        - Class type and purpose
        - Project size and domain
        - Test classes
        - Inner/nested classes
        - Abstract/interface classes
        """
        # Track different types of classes
        regular_classes = []
        test_classes = []
        utility_classes = []
        abstract_classes = []
        
        for class_name, info in self.class_info.items():
            # Skip generated classes
            if 'generated' in class_name.lower():
                continue
                
            # Analyze class characteristics
            is_test = any(pattern in class_name.lower() 
                         for pattern in ['test', 'mock', 'stub', 'fake'])
            is_utility = any(pattern in class_name.lower() 
                           for pattern in ['util', 'helper', 'common', 'base'])
            is_abstract = any(pattern in class_name 
                            for pattern in ['Abstract', 'Base', 'Interface'])
            
            # Categorize the class
            if is_test:
                test_classes.append(class_name)
            elif is_utility:
                utility_classes.append(class_name)
            elif is_abstract:
                abstract_classes.append(class_name)
            else:
                regular_classes.append(class_name)
        
        # Calculate weighted NOC
        weighted_noc = (len(regular_classes) + 
                       len(abstract_classes) * 0.5 +
                       len(utility_classes) * 0.3)
        
        # Adjust threshold based on project size
        adjusted_threshold = self._adjust_noc_threshold()
        
        if weighted_noc > adjusted_threshold:
            severity = 'High' if weighted_noc > adjusted_threshold * 1.5 else 'Medium'
            self.add_smell(
                "High Number of Classes (NOC)",
                f"Project has {weighted_noc:.1f} weighted classes:\n"
                f"- Regular classes: {len(regular_classes)}\n"
                f"- Abstract/Interface classes: {len(abstract_classes)}\n"
                f"- Utility classes: {len(utility_classes)}\n"
                f"- Test classes: {len(test_classes)} (not counted in weighted total)\n"
                f"Adjusted threshold: {adjusted_threshold}",
                self.project_root,
                "Project",
                severity=severity
            )

    def _adjust_noc_threshold(self):
        """
        Adjust NOC threshold based on project characteristics.
        
        Returns:
            float: Adjusted threshold value
        """
        base_threshold = self.thresholds['NOC_THRESHOLD']
        
        # Count total lines of production code
        total_loc = sum(info['loc'] for info in self.module_info.values()
                       if not any(pattern in name.lower() 
                                for pattern in ['test', 'mock'] 
                                for name in info))
        
        # Adjust based on project size
        if total_loc > 10000:
            base_threshold *= 1.5
        elif total_loc > 5000:
            base_threshold *= 1.2
            
        return base_threshold

    
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

    def resolve_base_class(self, base_node, module_name):
        """
        Resolve the name of a base class from its AST node.
        
        Args:
            base_node: The AST node representing the base class
            module_name: The name of the module containing the class
            
        Returns:
            str: The resolved base class name
        """
        if isinstance(base_node, ast.Name):
            return base_node.id
        elif isinstance(base_node, ast.Attribute):
            # Handle module.class syntax
            return f"{self._get_base_object(base_node)}.{base_node.attr}"
        return str(base_node)

    def _get_base_object(self, node):
        """Helper method to get the base object name from an attribute node."""
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return self._get_base_object(node.value)
        return str(node.value)

    def detect_cyclomatic_complexity(self):
        """
        Detect methods with high cyclomatic complexity.
        Uses a simplified calculation based on control flow statements.
        """
        for class_name, info in self.class_info.items():
            for method in info['methods']:
                # Skip special methods
                if method.name.startswith('__') and method.name.endswith('__'):
                    continue
                    
                complexity = self.calculate_cyclomatic_complexity(method)
                threshold = self.thresholds.get('CYCLOMATIC_COMPLEXITY_THRESHOLD', 10)
                
                if complexity > threshold:
                    severity = 'High' if complexity > threshold * 1.5 else 'Medium'
                    self.add_smell(
                        "High Cyclomatic Complexity",
                        f"Method '{method.name}' has cyclomatic complexity of {complexity}",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name,
                        method.lineno,
                        severity=severity
                    )

    def calculate_cyclomatic_complexity(self, method):
        """
        Calculate cyclomatic complexity using a simplified approach.
        
        Counts:
        - if statements
        - elif branches
        - for loops
        - while loops
        - except blocks
        - boolean operations (and, or)
        
        Args:
            method (ast.FunctionDef): The method to analyze
            
        Returns:
            int: The cyclomatic complexity value
        """
        complexity = 1  # Base complexity
        
        for node in ast.walk(method):
            # Control flow statements
            if isinstance(node, ast.If):
                complexity += 1
                # Count elif branches
                complexity += len([1 for handler in node.orelse 
                                 if isinstance(handler, ast.If)])
            elif isinstance(node, (ast.For, ast.While)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            # Boolean operations
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
                
        return complexity

    def detect_fanout(self):
        """
        Detect modules with high fan-out (too many outgoing dependencies).
        Excludes standard library and test dependencies.
        """
        standard_libs = {'os', 'sys', 'datetime', 'collections', 'json', 'logging'}
        
        for module in self.dependency_graph.nodes():
            # Skip test modules
            if 'test' in module.lower():
                continue
                
            # Count only non-standard library dependencies
            significant_deps = sum(1 for successor in self.dependency_graph.successors(module)
                                 if not any(successor.startswith(lib) for lib in standard_libs))
            
            threshold = self.thresholds.get('MAX_FANOUT', 15)
            if significant_deps > threshold:
                severity = 'High' if significant_deps > threshold * 1.5 else 'Medium'
                self.add_smell(
                    "High Fan-out",
                    f"Module '{module}' has {significant_deps} significant outgoing dependencies",
                    self.file_paths.get(module, "Unknown"),
                    module,
                    severity=severity
                )

    def detect_fanin(self):
        """
        Detect modules with high fan-in (too many incoming dependencies).
        Excludes utility classes and base classes which are meant to be widely used.
        """
        for module in self.dependency_graph.nodes():
            # Skip utility and base modules which are meant to have high fan-in
            if any(pattern in module.lower() for pattern in ['util', 'base', 'common', 'interface']):
                continue
                
            fanin = self.dependency_graph.in_degree(module)
            threshold = self.thresholds.get('MAX_FANIN', 15)
            
            if fanin > threshold:
                severity = 'High' if fanin > threshold * 1.5 else 'Medium'
                self.add_smell(
                    "High Fan-in",
                    f"Module '{module}' has {fanin} incoming dependencies",
                    self.file_paths.get(module, "Unknown"),
                    module,
                    severity=severity
                )

    def detect_file_length(self):
        """
        Detect files that are too long.
        """
        for module_name, info in self.module_info.items():
            try:
                file_path = self.file_paths.get(module_name, "")
                if not file_path or not os.path.exists(file_path):
                    continue

                # Try different encodings
                encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
                content = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as file:
                            content = file.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    logger.warning(f"Could not read file {file_path} with any supported encoding")
                    continue

                # Count meaningful lines
                lines = content.splitlines()
                meaningful_lines = 0
                in_docstring = False
                
                for line in lines:
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        continue
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        in_docstring = not in_docstring
                        continue
                    if not in_docstring:
                        meaningful_lines += 1
                
                threshold = self.thresholds.get('MAX_FILE_LENGTH', 250)
                if meaningful_lines > threshold:
                    severity = 'High' if meaningful_lines > threshold * 1.5 else 'Medium'
                    self.add_smell(
                        name="Long File",
                        description=f"File '{module_name}' has {meaningful_lines} meaningful lines of code",
                        file_path=file_path,
                        module_class=module_name,
                        severity=severity
                    )
            except Exception as e:
                logger.error(f"Error analyzing file length for {module_name}: {str(e)}")
                continue

    def detect_branches(self):
        """
        Detect methods with too many branches (if/else, loops).
        Excludes certain types of methods and considers nesting level.
        """
        for class_name, info in self.class_info.items():
            for method in info['methods']:
                # Skip property methods and simple getters/setters
                if (any(isinstance(d, ast.Name) and d.id == 'property' 
                       for d in getattr(method, 'decorator_list', [])) or
                    method.name.startswith(('get_', 'set_', 'is_'))):
                    continue
                    
                branch_info = self._analyze_branches(method)
                threshold = self.thresholds.get('MAX_BRANCHES', 10)
                
                # Consider both count and nesting
                if branch_info['count'] > threshold or branch_info['max_nesting'] > 3:
                    severity = 'High' if branch_info['count'] > threshold * 1.5 else 'Medium'
                    self.add_smell(
                        "Too Many Branches",
                        f"Method '{method.name}' has {branch_info['count']} branches "
                        f"with max nesting of {branch_info['max_nesting']}",
                        self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                        class_name,
                        method.lineno,
                        severity=severity
                    )

    def _analyze_branches(self, method):
        """
        Analyze branches in a method, considering both count and nesting level.
        
        Args:
            method (ast.FunctionDef): The method to analyze
            
        Returns:
            dict: Contains branch count and maximum nesting level
        """
        branch_count = 0
        max_nesting = 0
        current_nesting = 0
        
        for node in ast.walk(method):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                branch_count += 1
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
                
                # Add elif branches for if statements
                if isinstance(node, ast.If):
                    branch_count += len([1 for handler in node.orelse 
                                       if isinstance(handler, ast.If)])
                # Add except blocks for try statements
                elif isinstance(node, ast.Try):
                    branch_count += len(node.handlers)
                    
            # Decrease nesting level when leaving a node
            elif isinstance(node, ast.FunctionDef) and node != method:
                current_nesting = max(0, current_nesting - 1)
                
        return {
            'count': branch_count,
            'max_nesting': max_nesting
        }

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
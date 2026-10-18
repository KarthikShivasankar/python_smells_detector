import ast
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass

import networkx as nx
import yaml

from .exceptions import CodeAnalysisError
from .project import (
    STDLIB_MODULES,
    ModuleIndex,
    iter_imports,
    iter_python_files,
    module_parts,
    project_root,
    root_package,
)
from .project import module_name as project_module_name

# Set up logger
logger = logging.getLogger(__name__)

TRY_NODES = (ast.Try, ast.TryStar) if hasattr(ast, 'TryStar') else (ast.Try,)
NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith,
                 ast.Match, *TRY_NODES)


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
        self.root_package = None  # name of project_root when it is itself a package
        self.file_paths = {}
        self._imports = {}  # module -> candidate-name lists, resolved once all files are known
        self.errors = []  # files that could not be read or parsed
        self._complexity = {}  # function node -> cyclomatic complexity, shared by several metrics

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

    def detect_smells(self, directory_path, ignore_dirs=None):
        """
        Detect structural smells in the given directory.

        Args:
            directory_path (str): The path to the directory to analyze.
            ignore_dirs (iterable): Directory names to skip during analysis.
        """
        detection_methods = [
            (self.detect_nom, "detect_nom"),
            (self.detect_wmpc, "detect_wmpc"),
            (self.detect_size2, "detect_size2"),
            (self.detect_wac, "detect_wac"),
            (self.detect_lcom, "detect_lcom"),
            (self.detect_rfc, "detect_rfc"),
            (self.detect_nocc, "detect_nocc"),
            (self.detect_dit, "detect_dit"),
            (self.detect_loc, "detect_loc"),
            (self.detect_mpc, "detect_mpc"),
            (self.detect_cbo, "detect_cbo"),
            (self.detect_noc, "detect_noc"),
            (self.detect_cyclomatic_complexity, "detect_cyclomatic_complexity"),
            (self.detect_fanout, "detect_fanout"),
            (self.detect_fanin, "detect_fanin"),
            (self.detect_file_length, "detect_file_length"),
            (self.detect_branches, "detect_branches"),
        ]

        try:
            # First analyze the directory structure
            logger.info(f"Analyzing directory structure: {directory_path}")
            self.analyze_directory(directory_path, ignore_dirs=ignore_dirs)

            if not self.module_info:
                logger.warning("No modules were successfully analyzed. Skipping smell detection.")
                return

            # Then run each detection method
            for detect_method, method_name in detection_methods:
                try:
                    logger.debug(f"Running {method_name}")
                    detect_method()
                    logger.debug(
                        f"Completed {method_name}. Total smells so far: {len(self.structural_smells)}")
                except Exception as e:
                    # Continue with next detection method instead of stopping
                    logger.error(f"Error in {method_name}: {str(e)}", exc_info=True)
                    self.errors.append({'file': directory_path, 'detector': 'StructuralSmellDetector',
                                        'error': f"{method_name} failed: {type(e).__name__}: {e}"})

        except Exception as e:
            logger.error(f"Error analyzing directory {directory_path}: {str(e)}", exc_info=True)
            raise CodeAnalysisError(
                message=str(e),
                file_path=directory_path
            )

        # Log final results
        logger.info(f"Analysis complete. Found {len(self.structural_smells)} structural smells.")

    def analyze_directory(self, directory_path, ignore_dirs=None):
        """
        Analyze all Python files in the given directory (or the single given file).

        Args:
            directory_path (str): The path to the directory to be analyzed.
            ignore_dirs (iterable): Directory names to skip.
        """
        self.project_root = project_root(directory_path)
        self.root_package = root_package(self.project_root)
        files_analyzed = 0

        logger.info(f"Starting analysis of directory: {directory_path}")

        for file_path in iter_python_files(directory_path, ignore_dirs):
            try:
                self.analyze_file(file_path)
                files_analyzed += 1
                logger.debug(f"Successfully analyzed: {file_path}")
            except CodeAnalysisError as e:
                # Continue with next file instead of stopping
                logger.warning(f"Error analyzing {file_path}: {str(e)}")
                self.errors.append({'file': file_path, 'detector': 'StructuralSmellDetector',
                                    'error': str(e).split('\n')[0]})

        self._build_dependency_graph()
        logger.info(f"Structural analysis read {files_analyzed} files, "
                    f"{len(self.errors)} could not be analyzed")

    def analyze_file(self, file_path):
        """
        Analyze a single Python file for structural information.

        Args:
            file_path (str): The path to the Python file to be analyzed.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            tree = ast.parse(content)
        except (SyntaxError, ValueError, UnicodeDecodeError, OSError, RecursionError) as e:
            raise CodeAnalysisError(
                message=f"{type(e).__name__}: {e}",
                file_path=file_path,
                line_number=getattr(e, 'lineno', None)
            )

        module_name = project_module_name(file_path, self.project_root)
        lines = content.splitlines()
        doc_lines = set()
        imported = {}  # names bound by imports -> module they come from, for coupling metrics
        self.module_info[module_name] = {
            'loc': len(lines),
            'lines': lines,
            'doc_lines': doc_lines,
            'imported': imported,
            'functions': [n for n in tree.body
                          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
        }
        self.file_paths[module_name] = file_path
        self.dependency_graph.add_node(module_name)
        self._imports[module_name] = [c for c, _ in iter_imports(tree, module_name)]

        # One pass over the tree for classes, imported names and docstring lines
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.analyze_class(node, module_name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    source = (alias.name if isinstance(node, ast.Import) else
                              '.' * node.level + (node.module or ''))
                    imported[alias.asname or alias.name.split('.')[0]] = source
            elif (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and
                    isinstance(node.value.value, str)):
                # String-literal statements: docstrings and the like
                doc_lines.update(range(node.lineno, node.end_lineno + 1))

    def _build_dependency_graph(self):
        """Edges to the project modules each module imports, and to external top-level packages."""
        index = ModuleIndex(self.file_paths)
        for module, imports in self._imports.items():
            for candidates in imports:
                target = index.resolve(candidates) or candidates[-1].split('.')[0]
                if target != module:
                    self.dependency_graph.add_edge(module, target)

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
        # Attribute names read anywhere in the class, and how often each is read on self
        self.class_info[class_name]['attr_names'] = set()
        self.class_info[class_name]['self_reads'] = Counter()
        self.class_info[class_name]['base_classes'] = [
            self.resolve_base_class(base, module_name) for base in node.bases]
        self.class_info[class_name]['loc'] = node.end_lineno - node.lineno + 1
        self.class_info[class_name]['lineno'] = node.lineno

        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.class_info[class_name]['methods'].append(child)
                self.analyze_method(child, class_name)
            elif isinstance(child, (ast.Assign, ast.AnnAssign)):
                targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                self.class_info[class_name]['fields'].update(
                    t.id for t in targets if isinstance(t, ast.Name))

    def analyze_method(self, node, class_name):
        """
        Analyze a method definition node and extract relevant information.

        Args:
            node (ast.FunctionDef): The method definition node to analyze.
            class_name (str): The name of the class containing the method.
        """
        info = self.class_info[class_name]
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    info['method_calls'][node.name].add(child.func.attr)
            elif isinstance(child, ast.Attribute):
                info['attr_names'].add(child.attr)
                on_self = isinstance(child.value, ast.Name) and child.value.id == 'self'
                # Instance attributes assigned anywhere in the class are fields too
                if on_self and isinstance(child.ctx, ast.Store):
                    info['fields'].add(child.attr)
                elif on_self:
                    info['self_reads'][child.attr] += 1

    def add_smell(self, name, description, file_path, module_class,
                  line_number=None, severity='medium'):
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
        if line_number is None and module_class in self.class_info:
            line_number = self.class_info[module_class]['lineno']
        self.structural_smells.append(StructuralSmell(
            name=name,
            description=description,
            file_path=file_path,
            module_class=module_class,
            line_number=line_number,
            severity=severity.lower()
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
                self.add_smell(
                    name="High Number of Methods (NOM)",
                    description=f"Class '{class_name}' has {nom} methods (excluding special methods and properties)",
                    file_path=self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    module_class=class_name,
                    severity=severity
                )
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
            wmpc2 = sum(len(method.args.args) -
                        1 for method in complex_methods)  # Subtract 1 for 'self'

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
                                  if not f.startswith('_') or f in info['attr_names']}

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
                field_usage = info['self_reads'][field]

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
                for method2 in regular_methods[i + 1:]:
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
            if class_name.rsplit('.', 1)[-1].lower().startswith('test'):
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
        Detect classes with a Deep Inheritance Tree (DIT): the longest chain of base
        classes from a class up to object. A class without bases has DIT 1. Base names
        are resolved to project classes (same module first, then a unique class of that
        name elsewhere); unresolved bases count as one level. Builtins, mixins,
        interfaces and abstract bases are not counted as levels.
        """
        framework_bases = {'object', 'Exception', 'dict', 'list', 'set', 'tuple',
                           'str', 'int', 'float'}
        by_simple_name = defaultdict(list)
        for class_name in self.class_info:
            by_simple_name[class_name.rsplit('.', 1)[-1]].append(class_name)

        def resolve(base, class_name):
            local = f"{class_name.rsplit('.', 1)[0]}.{base}"
            if local in self.class_info:
                return local
            if base in self.class_info:
                return base
            matches = by_simple_name.get(base.split('.')[-1], [])
            return matches[0] if len(matches) == 1 else None

        def is_counted(base):
            base_name = base.split('.')[-1]
            return not (base_name in framework_bases or
                        any(tag in base_name for tag in ('Mixin', 'Interface', 'ABC', 'Abstract')))

        depths, paths = {}, {}

        def depth(class_name, visiting=()):
            if class_name in depths:
                return depths[class_name]
            best, best_path = 1, [class_name]
            for base in self.class_info[class_name]['base_classes']:
                if not is_counted(base):
                    continue
                target = resolve(base, class_name)
                if target is None or target in visiting or target == class_name:
                    d, p = 1, [base]  # external or unresolvable base: one level
                else:
                    d, p = depth(target, visiting + (class_name,)), paths[target]
                if d + 1 > best:
                    best, best_path = d + 1, p + [class_name]
            depths[class_name], paths[class_name] = best, best_path
            return best

        threshold = self.thresholds['DIT_THRESHOLD']
        for class_name in self.class_info:
            # Exception taxonomies are deep by design
            if class_name.endswith(('Error', 'Exception', 'Warning')):
                continue
            dit = depth(class_name)
            if dit > threshold:
                self.add_smell(
                    "Deep Inheritance Tree (DIT)",
                    f"Class '{class_name}' has DIT of {dit}\nInheritance path: "
                    f"{'->'.join(['object'] + paths[class_name])}",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity='High' if dit > threshold * 1.5 else 'Medium'
                )

    def _line_counts(self, info):
        """(code, doc, import, blank) line counts of a module; comment lines count as none."""
        code = doc = imports = blank = 0
        for number, line in enumerate(info['lines'], start=1):
            stripped = line.strip()
            if not stripped:
                blank += 1
            elif number in info['doc_lines']:
                doc += 1
            elif stripped.startswith(('import ', 'from ')):
                imports += 1
            elif not stripped.startswith('#'):
                code += 1
        return code, doc, imports, blank

    def detect_loc(self):
        """
        Detect modules with high Lines of Code (LOC).
        """
        for module_name, info in self.module_info.items():
            file_path = self.file_paths[module_name]
            lines = info['lines']
            code_lines, doc_lines, import_lines, blank_lines = self._line_counts(info)

            # Calculate effective LOC and complexity ratio
            effective_loc = code_lines
            non_blank = len(lines) - blank_lines
            complexity_ratio = effective_loc / non_blank if non_blank > 0 else 1

            # Adjust threshold based on module type
            adjusted_threshold = self.thresholds['LOC_THRESHOLD']
            if module_name.rsplit('.', 1)[-1].startswith('test'):
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
                severity = 'High' if weighted_mpc > self.thresholds['MPC_THRESHOLD'] * \
                    1.5 else 'Medium'
                self.add_smell(
                    "High Message Passing Coupling (MPC)",
                    f"Class '{class_name}' has weighted MPC of {weighted_mpc:.1f}\n"
                    f"(External calls: {external_mpc}, Internal calls: {internal_mpc})\n"
                    f"Most frequent external calls: {dict(sorted(method_calls.items(), key=lambda x: (-x[1], x[0]))[:3])}",
                    self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown"),
                    class_name,
                    severity=severity
                )

    def detect_cbo(self):
        """
        Detect classes with high Coupling Between Object Classes (CBO): the number of
        distinct other classes and modules a class uses. Without type inference a
        coupling target is a name that is either imported into the module (from
        outside the standard library) or the name of a class defined in the project;
        local variables, parameters and builtins are not coupling targets.
        """
        project_classes = {name.rsplit('.', 1)[-1] for name in self.class_info}
        threshold = self.thresholds['CBO_THRESHOLD']

        for class_name, info in self.class_info.items():
            module_name, own_name = class_name.rsplit('.', 1)
            imported = {name for name, source in
                        self.module_info.get(module_name, {}).get('imported', {}).items()
                        if source.split('.')[0] not in STDLIB_MODULES}
            used = {node.id for method in info['methods'] for node in ast.walk(method)
                    if isinstance(node, ast.Name)}
            used.update(base.split('.')[0] for base in info['base_classes'])
            coupled = sorted(name for name in used
                             if name != own_name and (name in imported or name in project_classes))

            cbo = len(coupled)
            if cbo > threshold:
                self.add_smell(
                    "High Coupling Between Object Classes (CBO)",
                    f"Class '{class_name}' is coupled to {cbo} classes or modules: "
                    f"{', '.join(coupled[:10])}{', ...' if cbo > 10 else ''}",
                    self.file_paths.get(module_name, "Unknown"),
                    class_name,
                    severity=self._calculate_cbo_severity(cbo, threshold)
                )

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
        total_loc = sum(info['loc'] for name, info in self.module_info.items()
                        if not any(pattern in name.lower() for pattern in ('test', 'mock')))

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
            return f"{self._get_attr_base(base_node)}.{base_node.attr}"
        return str(base_node)

    def _get_attr_base(self, node):
        """Helper method to get the base object name from an attribute node."""
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return self._get_attr_base(node.value)
        return str(node.value)

    def _functions(self):
        """Yield (owner, function, file_path) for every method and module-level function."""
        for class_name, info in self.class_info.items():
            file_path = self.file_paths.get(class_name.rsplit('.', 1)[0], "Unknown")
            for method in info['methods']:
                yield class_name, method, file_path
        for module_name, info in self.module_info.items():
            for function in info['functions']:
                yield module_name, function, self.file_paths[module_name]

    def detect_cyclomatic_complexity(self):
        """
        Detect methods and functions with high cyclomatic complexity.
        """
        threshold = self.thresholds.get('CYCLOMATIC_COMPLEXITY_THRESHOLD', 10)
        for owner, function, file_path in self._functions():
            # Skip special methods
            if function.name.startswith('__') and function.name.endswith('__'):
                continue

            complexity = self.calculate_cyclomatic_complexity(function)
            if complexity > threshold:
                severity = 'High' if complexity > threshold * 1.5 else 'Medium'
                self.add_smell(
                    "High Cyclomatic Complexity",
                    f"Function '{function.name}' has cyclomatic complexity of {complexity}",
                    file_path,
                    owner,
                    function.lineno,
                    severity=severity
                )

    def calculate_cyclomatic_complexity(self, method):
        if method not in self._complexity:
            self._complexity[method] = self._cyclomatic_complexity(method)
        return self._complexity[method]

    @staticmethod
    def _cyclomatic_complexity(method):
        """
        Calculate McCabe cyclomatic complexity: 1 plus one per decision point.

        Counts if/elif statements and conditional expressions, for/while loops
        (async too), except handlers, match cases other than a bare ``case _``,
        each extra operand of and/or, and each for/if clause of a comprehension.

        Args:
            method (ast.FunctionDef): The method to analyze

        Returns:
            int: The cyclomatic complexity value
        """
        complexity = 1  # Base complexity

        for node in ast.walk(method):
            # ast.walk visits each elif as its own If node
            if isinstance(node, (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While,
                                 ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                complexity += 1 + len(node.ifs)
            elif isinstance(node, ast.match_case):
                is_wildcard = (isinstance(node.pattern, ast.MatchAs) and
                               node.pattern.pattern is None and node.guard is None)
                complexity += not is_wildcard

        return complexity

    def detect_fanout(self):
        """
        Detect modules with high fan-out (too many outgoing dependencies).
        Excludes standard library dependencies and test modules.
        """
        threshold = self.thresholds.get('MAX_FANOUT', 15)
        for module in self.module_info:
            # Skip test modules
            if module.rsplit('.', 1)[-1].startswith('test'):
                continue

            # Count only non-standard library dependencies
            significant_deps = sum(1 for successor in self.dependency_graph.successors(module)
                                   if successor.split('.')[0] not in STDLIB_MODULES)

            if significant_deps > threshold:
                severity = 'High' if significant_deps > threshold * 1.5 else 'Medium'
                self.add_smell(
                    "High Fan-out",
                    f"Module '{module}' has {significant_deps} significant outgoing dependencies",
                    self.file_paths[module],
                    module,
                    severity=severity
                )

    def detect_fanin(self):
        """
        Detect project modules with high fan-in (imported by too many project modules).
        Excludes utility and base modules which are meant to be widely used.
        """
        threshold = self.thresholds.get('MAX_FANIN', 15)
        for module in self.module_info:
            # Skip utility and base modules which are meant to have high fan-in
            parts = set(module_parts(module, self.root_package))
            if parts & {'util', 'utils', 'base', 'common', 'interface', 'interfaces'}:
                continue

            fanin = self.dependency_graph.in_degree(module)
            if fanin > threshold:
                severity = 'High' if fanin > threshold * 1.5 else 'Medium'
                self.add_smell(
                    "High Fan-in",
                    f"Module '{module}' has {fanin} incoming dependencies",
                    self.file_paths[module],
                    module,
                    severity=severity
                )

    def detect_file_length(self):
        """
        Detect files that are too long, counting code and import lines but not
        comments, docstrings or blank lines.
        """
        threshold = self.thresholds.get('MAX_FILE_LENGTH', 250)
        for module_name, info in self.module_info.items():
            code_lines, _, import_lines, _ = self._line_counts(info)
            meaningful_lines = code_lines + import_lines
            if meaningful_lines > threshold:
                severity = 'High' if meaningful_lines > threshold * 1.5 else 'Medium'
                self.add_smell(
                    name="Long File",
                    description=f"File '{module_name}' has {meaningful_lines} meaningful lines of code",
                    file_path=self.file_paths[module_name],
                    module_class=module_name,
                    severity=severity
                )

    def detect_branches(self):
        """
        Detect methods and functions with too many branches (Too Many Branches) or
        too deeply nested blocks (Deep Nesting, above MAX_NESTING_DEPTH).
        """
        threshold = self.thresholds.get('MAX_BRANCHES', 10)
        max_nesting = self.thresholds.get('MAX_NESTING_DEPTH', 4)
        for owner, function, file_path in self._functions():
            # Skip property methods and simple getters/setters
            if (any(isinstance(d, ast.Name) and d.id == 'property'
                    for d in function.decorator_list) or
                    function.name.startswith(('get_', 'set_', 'is_'))):
                continue

            branch_count = self._count_branches(function)
            if branch_count > threshold:
                self.add_smell(
                    "Too Many Branches",
                    f"Function '{function.name}' has {branch_count} branches",
                    file_path,
                    owner,
                    function.lineno,
                    severity='High' if branch_count > threshold * 1.5 else 'Medium'
                )

            nesting = self._max_nesting(function)
            if nesting > max_nesting:
                self.add_smell(
                    "Deep Nesting",
                    f"Function '{function.name}' nests blocks {nesting} levels deep",
                    file_path,
                    owner,
                    function.lineno,
                    severity='High' if nesting > max_nesting + 2 else 'Medium'
                )

    @staticmethod
    def _count_branches(function):
        """if/elif, loops, try plus each except handler, and match cases."""
        count = 0
        # ast.walk visits each elif as its own If node, so it is counted once here
        for node in ast.walk(function):
            if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.match_case)):
                count += 1
            elif isinstance(node, TRY_NODES):
                count += 1 + len(node.handlers)
        return count

    @staticmethod
    def _max_nesting(node):
        """Deepest nesting of block statements below node; an elif does not add a level."""
        deepest = 0
        stack = [(node, 0)]  # iterative: generated code nests expressions thousands deep
        while stack:
            parent, depth = stack.pop()
            deepest = max(deepest, depth)
            for child in ast.iter_child_nodes(parent):
                is_elif = (isinstance(parent, ast.If) and len(parent.orelse) == 1
                           and parent.orelse[0] is child and isinstance(child, ast.If))
                stack.append((child, depth + (isinstance(child, NESTING_NODES) and not is_elif)))
        return deepest


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
    parser.add_argument(
        "--config",
        default="code_quality_config.yaml",
        help="Path to the configuration file")
    args = parser.parse_args()

    analyze_structure(args.directory, args.config)

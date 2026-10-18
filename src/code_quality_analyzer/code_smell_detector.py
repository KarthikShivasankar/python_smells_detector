import builtins
import keyword
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations, permutations, product

import astroid
from astroid import exceptions as astroid_exceptions
from astroid import nodes

from .exceptions import CodeAnalysisError

# Set up logger
logger = logging.getLogger(__name__)


@dataclass
class CodeSmell:
    name: str
    description: str
    file_path: str
    module_class: str
    line_number: int
    severity: str = ''


class CodeSmellDetector:
    """
    A class to detect various code smells in Python source code.

    This class analyzes Python source code for common code smells and anti-patterns,
    providing a comprehensive report on potential issues in the codebase.

    Attributes:
        code_smells (list): A list to store detected code smells.
        thresholds (dict): A dictionary of threshold values for various code smell detections.
        file_content (list): A list of strings representing the content of the analyzed file.
    """

    def __init__(self, thresholds):
        """
        Initialize the CodeSmellDetector with given thresholds.

        Args:
            thresholds (dict): A dictionary of threshold values for various code smell detections.
        """
        self.code_smells = []
        self.thresholds = thresholds
        self.errors = []  # files that could not be analyzed, filled by the caller
        # Cross-file accumulation for smells needing multi-file context
        self._global_class_methods = defaultdict(list)
        self._global_class_bases = {}  # (class_name, file_path) -> frozenset of base names
        self._global_param_funcs = []  # (func_name, file_path, frozenset(params))
        self._global_code_blocks = defaultdict(list)
        self._global_class_info = {}
        self._global_class_hierarchies = defaultdict(list)
        # (smell name, group key, file_path) -> per-file finding, so a cross-file
        # finding for the same group can replace it instead of double counting
        self._file_findings = {}
        # Attribute names read on objects other than self, project-wide, and the
        # Temporary Field findings whose fields may turn out to be read elsewhere
        self._attr_reads = set()
        self._temp_field_findings = []
        # Private module functions and methods per file, and every name referenced
        # anywhere, for the project-wide Dead Code pass
        self._private_defs = []
        self._referenced_names = set()

    def detect_smells(self, file_path):
        """
        Detect code smells in the given file.
        """
        detection_methods = [
            (self.detect_long_methods, "detect_long_methods"),
            (self.detect_large_classes, "detect_large_classes"),
            (self.detect_primitive_obsession, "detect_primitive_obsession"),
            (self.detect_long_parameter_lists, "detect_long_parameter_lists"),
            (self.detect_data_clumps, "detect_data_clumps"),
            (self.detect_switch_statements, "detect_switch_statements"),
            (self.detect_temporary_fields, "detect_temporary_fields"),
            (self.detect_alternative_classes, "detect_alternative_classes"),
            (self.detect_divergent_change, "detect_divergent_change"),
            (self.detect_parallel_inheritance, "detect_parallel_inheritance"),
            (self.detect_shotgun_surgery, "detect_shotgun_surgery"),
            (self.detect_comments, "detect_comments"),
            (self.detect_duplicate_code, "detect_duplicate_code"),
            (self.detect_speculative_generality, "detect_speculative_generality"),
            (self.detect_feature_envy, "detect_feature_envy"),
            (self.detect_inappropriate_intimacy, "detect_inappropriate_intimacy"),
            (self.detect_message_chains, "detect_message_chains"),
            (self.detect_middle_man, "detect_middle_man"),
            (self.detect_data_class, "detect_data_class"),
            (self.detect_lazy_class, "detect_lazy_class"),
            (self.detect_dead_code, "detect_dead_code"),
        ]

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            try:
                module = astroid.parse(content)
            except astroid_exceptions.AstroidSyntaxError as e:
                cause = e.error if isinstance(getattr(e, 'error', None), SyntaxError) else None
                raise CodeAnalysisError(
                    message=f"SyntaxError: {cause.msg if cause else e} (line {getattr(cause, 'lineno', '?')})",
                    file_path=file_path,
                    line_number=getattr(cause, 'lineno', None)
                )

            self.file_content = content.split('\n')
            # Computed once per file, shared by several detectors
            self._module_names = self._imported_names(module)
            self._file_attr_reads = {
                n.attrname for n in module.nodes_of_class(nodes.Attribute)
                if not (isinstance(n.expr, nodes.Name) and n.expr.name in ('self', 'cls'))}
            self._attr_reads.update(self._file_attr_reads)

            # Run each detection method
            for detect_method, method_name in detection_methods:
                try:
                    logger.debug(f"Running {method_name} on {file_path}")
                    detect_method(module, file_path)
                except Exception as e:
                    logger.error(
                        f"Error in {method_name} analyzing {file_path}: {str(e)}",
                        exc_info=True
                    )
                    raise CodeAnalysisError(
                        message=f"Error in {method_name}: {str(e)}",
                        file_path=file_path,
                        function_name=method_name
                    )

        except CodeAnalysisError:
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error in {file_path}: {str(e)}")
            raise CodeAnalysisError(
                message=f"File encoding error: {str(e)}",
                file_path=file_path
            )
        except Exception as e:
            logger.error(f"Unexpected error analyzing {file_path}: {str(e)}", exc_info=True)
            raise CodeAnalysisError(
                message=f"Unexpected error: {str(e)}",
                file_path=file_path
            )

    def detect_long_methods(self, module, file_path):
        """
        Detect long methods in the given module: functions with more than
        LONG_METHOD_LINES lines that are neither blank, comments nor docstring.
        """
        for node in module.nodes_of_class(nodes.FunctionDef):
            # Skip properties
            if 'property' in self._decorator_names(node):
                continue

            doc = node.doc_node
            doc_lines = range(doc.lineno, doc.end_lineno + 1) if doc is not None else ()
            actual_lines = 0
            for line_no in range(node.fromlineno, min(node.tolineno, len(self.file_content)) + 1):
                line = self.file_content[line_no - 1].strip()
                if line and not line.startswith('#') and line_no not in doc_lines:
                    actual_lines += 1

            if actual_lines > self.thresholds["LONG_METHOD_LINES"]:
                parent_class = node.parent.name if isinstance(node.parent, nodes.ClassDef) else None
                display_name = f"{parent_class}.{node.name}" if parent_class else node.name
                self.add_smell(
                    name="Long Method",
                    description=f"'{display_name}' has {actual_lines} lines in {file_path} at line {node.lineno}",
                    file_path=file_path,
                    module_class=display_name,
                    line_number=node.lineno,
                    severity='high' if actual_lines > 2 * self.thresholds["LONG_METHOD_LINES"] else 'medium'
                )

    def detect_large_classes(self, module, file_path):
        """
        Detect large classes in the given module.
        """
        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip data classes and exception classes
            is_dataclass = False
            if node.decorators:
                for decorator in node.decorators.nodes:
                    if isinstance(decorator, nodes.Name) and decorator.name == 'dataclass':
                        is_dataclass = True
                        break
                    elif isinstance(decorator, nodes.Call):
                        if isinstance(decorator.func,
                                      nodes.Name) and decorator.func.name == 'dataclass':
                            is_dataclass = True
                            break
                    elif isinstance(decorator, nodes.Attribute):
                        if decorator.attrname == 'dataclass':
                            is_dataclass = True
                            break

            if is_dataclass or self._is_exception_class(node):
                continue

            # Count non-trivial methods (exclude simple getters/setters)
            non_trivial_methods = []
            for method in node.body:
                if isinstance(method, nodes.FunctionDef):
                    # Skip magic methods
                    if method.name.startswith('__') and method.name.endswith('__'):
                        continue
                    # Skip simple getters/setters
                    if len(method.body) == 1 and isinstance(
                            method.body[0], (nodes.Return, nodes.Assign)):
                        continue
                    non_trivial_methods.append(method)

            if len(non_trivial_methods) > self.thresholds["LARGE_CLASS_METHODS"]:
                self.add_smell(
                    name="Large Class",
                    description=f"'{node.name}' has {len(non_trivial_methods)} non-trivial methods in {file_path}",
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno
                )

    def detect_primitive_obsession(self, module, file_path):
        """
        Detect primitive obsession: functions taking more than
        PRIMITIVE_OBSESSION_COUNT parameters annotated as int/str/float/bool,
        making up over 70% of their parameters.
        """
        for node in module.nodes_of_class(nodes.FunctionDef):
            params = self._parameters(node)
            # Skip if it's a small number of total arguments
            if len(params) <= 3:
                continue

            primitives = [arg for arg, annotation in params
                          if isinstance(annotation, nodes.Name) and
                          annotation.name in ('int', 'str', 'float', 'bool')]
            if (len(primitives) > self.thresholds["PRIMITIVE_OBSESSION_COUNT"] and
                    len(primitives) / len(params) > 0.7):  # More than 70% primitives
                self.add_smell(
                    name="Primitive Obsession",
                    description=f"'{node.name}' has {len(primitives)} primitive parameters in {file_path}",
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno,
                    severity='low'
                )

    def detect_long_parameter_lists(self, module, file_path):
        """
        Detect long parameter lists, counting positional-only, regular and
        keyword-only parameters but not self / cls.
        """
        for node in module.nodes_of_class(nodes.FunctionDef):
            # Skip if it's a constructor
            if node.name == '__init__':
                continue

            count = len(self._parameters(node))
            # Allow two more parameters when the function also takes *args / **kwargs
            threshold = self.thresholds["LONG_PARAMETER_LIST"]
            if node.args.vararg or node.args.kwarg:
                threshold += 2

            if count > threshold:
                self.add_smell(
                    name="Long Parameter List",
                    description=f"'{node.name}' has {count} parameters in {file_path}",
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno,
                    severity='medium'
                )

    def detect_data_clumps(self, module, file_path):
        """
        Detect data clumps in the given module.

        A data clump is a maximal set of at least DATA_CLUMPS_THRESHOLD parameters
        shared by two or more functions. Only maximal shared sets are reported,
        not each of their subsets.
        """
        funcs = []
        for node in module.nodes_of_class(nodes.FunctionDef):
            # Skip if it's a constructor or property
            if node.name == '__init__' or (node.decorators and
                                           any(isinstance(d, nodes.Name) and d.name == 'property'
                                               for d in node.decorators.nodes)):
                continue

            # Get parameters excluding self / cls
            params = frozenset(arg.name for arg, _ in self._parameters(node))

            # Skip if too few parameters
            if len(params) < self.thresholds["DATA_CLUMPS_THRESHOLD"]:
                continue

            funcs.append((node.name, params))
            self._global_param_funcs.append((node.name, file_path, params))

        for params, members in self._maximal_param_groups([p for _, p in funcs]).items():
            names = [funcs[i][0] for i in members]
            self._file_findings[("Data Clumps", params, file_path)] = self.add_smell(
                name="Data Clumps",
                description=f"Parameters {', '.join(sorted(params))} appear together in functions: {', '.join(names)} in {file_path}",
                file_path=file_path,
                module_class=', '.join(names),
                line_number=None,
                severity='medium'
            )

    def _maximal_param_groups(self, param_sets):
        """
        Map each maximal shared parameter set (size >= DATA_CLUMPS_THRESHOLD) to the
        indices of every function whose parameters contain it.

        Every such set is the intersection of some pair of functions, so pairwise
        intersections enumerate them all without generating subsets.
        """
        # ponytail: O(n^2) over functions with >= threshold params; fine since those are rare
        groups = {}
        for i, j in combinations(range(len(param_sets)), 2):
            shared = param_sets[i] & param_sets[j]
            if len(shared) >= self.thresholds["DATA_CLUMPS_THRESHOLD"] and shared not in groups:
                groups[shared] = [k for k, p in enumerate(param_sets) if shared <= p]
        return groups

    def detect_switch_statements(self, module, file_path):
        """
        Detect switch statements in the given module.
        """
        def is_elif(node):
            parent = node.parent
            return isinstance(parent, nodes.If) and len(parent.orelse) == 1 and parent.orelse[0] is node

        def count_conditions(node):
            """Number of conditions (if + each elif) in the chain starting at node."""
            count = 1
            while len(node.orelse) == 1 and isinstance(node.orelse[0], nodes.If):
                node = node.orelse[0]
                count += 1
            return count

        for node in module.nodes_of_class(nodes.If):
            # Skip simple if statements and elif links (each chain is measured from its head)
            if not node.orelse or is_elif(node):
                continue

            # Check if this is part of a try/except block
            if any(isinstance(parent, nodes.ExceptHandler) for parent in node.node_ancestors()):
                continue

            condition_count = count_conditions(node)

            # Check for common valid patterns (a node with an else is never a guard clause)
            is_type_check = isinstance(
                node.test, nodes.Call) and getattr(
                node.test.func, 'name', '') == 'isinstance'

            if condition_count > self.thresholds["COMPLEX_CONDITIONAL"] and not is_type_check:
                self.add_smell(
                    name="Switch Statements",
                    description=f"Complex conditional with {condition_count} branches at line {node.lineno} in {file_path}",
                    file_path=file_path,
                    module_class=None,
                    line_number=node.lineno,
                    severity='medium'
                )

        for node in module.nodes_of_class(nodes.Match):
            if len(node.cases) > self.thresholds["COMPLEX_CONDITIONAL"]:
                self.add_smell(
                    name="Switch Statements",
                    description=f"match statement with {len(node.cases)} cases at line {node.lineno} in {file_path}",
                    file_path=file_path,
                    module_class=None,
                    line_number=node.lineno,
                    severity='medium'
                )

    def detect_temporary_fields(self, module, file_path):
        """
        Detect temporary fields: attributes assigned on self in __init__ that no
        other method of the class reads and no code reads through another object.
        """
        module_reads = self._file_attr_reads
        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip data classes and exception classes
            is_dataclass = False
            if node.decorators:
                for decorator in node.decorators.nodes:
                    if isinstance(decorator, nodes.Name) and decorator.name == 'dataclass':
                        is_dataclass = True
                        break
                    elif isinstance(decorator, nodes.Call):
                        if isinstance(decorator.func,
                                      nodes.Name) and decorator.func.name == 'dataclass':
                            is_dataclass = True
                            break
                    elif isinstance(decorator, nodes.Attribute):
                        if decorator.attrname == 'dataclass':
                            is_dataclass = True
                            break

            if is_dataclass or self._is_exception_class(node):
                continue

            init_fields = set()
            used_fields = set()
            cached_fields = set()  # For fields that might be used for caching

            for child in node.body:
                if isinstance(child, nodes.FunctionDef):
                    if child.name == '__init__':
                        # Check if __init__ has a comment indicating its fields are for caching
                        is_cache = any(isinstance(sibling, nodes.Expr) and
                                       isinstance(sibling.value, nodes.Const) and
                                       'cache' in str(sibling.value.value).lower()
                                       for sibling in child.body)
                        # Fields are attributes assigned on self, not parameters or locals
                        for target in child.nodes_of_class(nodes.AssignAttr):
                            if isinstance(target.expr, nodes.Name) and target.expr.name == 'self':
                                (cached_fields if is_cache else init_fields).add(target.attrname)
                    else:
                        used_fields.update(
                            n.attrname for n in child.nodes_of_class(nodes.Attribute)
                            if isinstance(n.expr, nodes.Name) and n.expr.name == 'self'
                        )

            # Exclude common patterns, cached fields and fields read through another
            # object in this file; reads in other files are removed in the cross-file pass
            temp_fields = (init_fields - used_fields - cached_fields - module_reads -
                           {'logger', 'config', 'cache', '_cache'})

            if len(temp_fields) >= self.thresholds["TEMPORARY_FIELD_THRESHOLD"]:
                smell = self.add_smell(
                    name="Temporary Field",
                    description=self._temporary_field_description(temp_fields, node.name, node.lineno, file_path),
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno,
                    severity='low'
                )
                self._temp_field_findings.append((smell, temp_fields))

    @staticmethod
    def _temporary_field_description(fields, class_name, lineno, file_path):
        return (f"Potentially unused fields {', '.join(sorted(fields))} in class '{class_name}' "
                f"at line {lineno} in {file_path}")

    def detect_alternative_classes(self, module, file_path):
        """
        Detect alternative classes with different interfaces in the given module.
        """
        class_methods = defaultdict(list)
        class_bases = {}
        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip data classes, exceptions, and abstract base classes
            is_excluded = False
            if node.decorators:
                for decorator in node.decorators.nodes:
                    if isinstance(decorator, nodes.Name) and decorator.name in {
                            'dataclass', 'abstractmethod'}:
                        is_excluded = True
                        break
                    elif isinstance(decorator, nodes.Call):
                        if isinstance(decorator.func, nodes.Name) and decorator.func.name in {
                                'dataclass', 'abstractmethod'}:
                            is_excluded = True
                            break
                    elif isinstance(decorator, nodes.Attribute):
                        if decorator.attrname in {'dataclass', 'abstractmethod'}:
                            is_excluded = True
                            break

            if (is_excluded or
                any(base.name.endswith(('Exception', 'ABC'))
                    for base in node.bases if isinstance(base, nodes.Name))):
                continue

            # Get non-private methods excluding standard methods
            methods = frozenset(
                n.name for n in node.mymethods()
                if not n.name.startswith('_') and
                n.name not in {'__init__', '__str__', '__repr__', '__eq__', '__hash__'}
            )

            # Skip if too few methods
            if len(methods) < 2:
                continue

            class_methods[methods].append(node.name)
            class_bases[node.name] = frozenset(b.as_string() for b in node.bases) - {'object'}

        for methods, classes in class_methods.items():
            if len(classes) >= self.thresholds["ALTERNATIVE_CLASSES_THRESHOLD"]:
                if not self._share_base(class_bases[c] for c in classes):
                    self._file_findings[("Alternative Classes", methods, file_path)] = self.add_smell(
                        name="Alternative Classes with Different Interfaces",
                        description=f"Classes {', '.join(classes)} share similar methods {', '.join(sorted(methods))} in {file_path}",
                        file_path=file_path,
                        module_class=', '.join(classes),
                        line_number=None,
                        severity='medium'
                    )

        # Accumulate for cross-file detection
        for methods, class_names in class_methods.items():
            for class_name in class_names:
                self._global_class_methods[methods].append((class_name, file_path))
                self._global_class_bases[(class_name, file_path)] = class_bases[class_name]

    @staticmethod
    def _share_base(base_sets):
        """True if all classes in a group have at least one base class in common."""
        return bool(frozenset.intersection(*base_sets))

    def detect_divergent_change(self, module, file_path):
        """
        Detect divergent change in the given module.
        """
        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip data classes, exceptions, and utility classes
            is_dataclass = False
            if node.decorators:
                for decorator in node.decorators.nodes:
                    if isinstance(decorator, nodes.Name) and decorator.name == 'dataclass':
                        is_dataclass = True
                        break
                    elif isinstance(decorator, nodes.Call):
                        if isinstance(decorator.func,
                                      nodes.Name) and decorator.func.name == 'dataclass':
                            is_dataclass = True
                            break
                    elif isinstance(decorator, nodes.Attribute):
                        if decorator.attrname == 'dataclass':
                            is_dataclass = True
                            break

            if (is_dataclass or
                any(base.name.endswith('Exception') for base in node.bases if isinstance(base, nodes.Name)) or
                    node.name.endswith(('Utils', 'Helper', 'Mixin'))):
                continue

            # Get method prefixes, excluding common patterns
            method_prefixes = []
            for method in node.mymethods():
                # Skip magic methods, properties, and private methods
                is_property = False
                if method.decorators:
                    for decorator in method.decorators.nodes:
                        if isinstance(decorator, nodes.Name) and decorator.name == 'property':
                            is_property = True
                            break
                        elif isinstance(decorator, nodes.Call):
                            if isinstance(decorator.func,
                                          nodes.Name) and decorator.func.name == 'property':
                                is_property = True
                                break
                        elif isinstance(decorator, nodes.Attribute):
                            if decorator.attrname == 'property':
                                is_property = True
                                break

                if (method.name.startswith('__') or is_property or method.name.startswith('_')):
                    continue

                # First word of snake_case or camelCase names: get_user / getUser -> get
                prefix = re.split(r'_|(?<=[a-z0-9])(?=[A-Z])', method.name)[0].lower()
                # Skip common CRUD and utility prefixes
                if prefix not in {'get', 'set', 'is', 'has',
                                  'validate', 'create', 'update', 'delete'}:
                    method_prefixes.append(prefix)

            unique_prefixes = set(method_prefixes)
            if (len(unique_prefixes) > self.thresholds["DIVERGENT_CHANGE_PREFIXES"] and
                    len(method_prefixes) > self.thresholds["DIVERGENT_CHANGE_METHODS"]):
                self.add_smell(
                    name="Potential Divergent Change",
                    description=f"Class '{node.name}' has {len(unique_prefixes)} different method prefixes: {', '.join(sorted(unique_prefixes))} in {file_path}",
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno,
                    severity='medium'
                )

    def detect_parallel_inheritance(self, module, file_path):
        """
        Detect parallel inheritance hierarchies in the given module.
        """
        class_hierarchies = defaultdict(list)
        class_info = {}  # Store class information for better analysis

        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip exception classes and mixins
            if (any(base.name.endswith('Exception') for base in node.bases if isinstance(base, nodes.Name)) or
                    node.name.endswith('Mixin')):
                continue

            for base in node.bases:
                if isinstance(base, nodes.Name):
                    class_hierarchies[base.name].append(node.name)
                    # Store method names for similarity comparison
                    class_info[node.name] = {m.name for m in node.mymethods()
                                             if not m.name.startswith('_')}

        # Accumulate for cross-file detection
        for base_name, child_names in class_hierarchies.items():
            for child_name in child_names:
                self._global_class_hierarchies[base_name].append((child_name, file_path))

        if len(class_hierarchies) > 1:
            parallel_hierarchies = []
            for (b1, h1), (b2, h2) in combinations(class_hierarchies.items(), 2):
                if len(h1) > 1 and len(h2) > 1:
                    # Check for naming patterns
                    if self._names_correspond(b1, h1, b2, h2):
                        # Check for method similarity
                        if (h1[0] in class_info and h2[0] in class_info and
                                (class_info[h1[0]] or class_info[h2[0]])):  # Ensure at least one set has methods
                            union_size = len(class_info[h1[0]] | class_info[h2[0]])
                            if union_size > 0:  # Prevent division by zero
                                similarity = len(class_info[h1[0]] & class_info[h2[0]]) / union_size
                                if similarity > 0.3:  # More than 30% similar methods
                                    parallel_hierarchies.extend([h1, h2])

            if parallel_hierarchies:
                self.add_smell(
                    name="Parallel Inheritance Hierarchies",
                    description=f"Parallel hierarchies detected: {' and '.join([' -> '.join(h) for h in parallel_hierarchies])} in {file_path}",
                    file_path=file_path,
                    module_class=None,
                    line_number=None,
                    severity='high'
                )

    @staticmethod
    def _names_correspond(b1, h1, b2, h2):
        """
        True if a child of base b1 and a child of base b2 share a name stem once the
        base name is removed (XmlReader/XmlWriter, Dog/DogOwner).
        """
        for c1, c2 in product(h1, h2):
            s1, s2 = c1.replace(b1, ''), c2.replace(b2, '')
            if s1 and s2 and (s1.startswith(s2) or s2.startswith(s1)):
                return True
        return False

    def detect_shotgun_surgery(self, module, file_path):
        """
        Detect potential shotgun surgery in the given module.
        """
        method_calls = defaultdict(list)
        for node in module.body:
            for call in node.nodes_of_class(nodes.Call):
                if isinstance(call.func, nodes.Name):
                    # Skip common utility methods, logging and builtins
                    if (call.func.name.lower() in {'log', 'print', 'str',
                                                   'len', 'isinstance', 'super'} or
                            call.func.name in vars(builtins) or
                            call.func.name.endswith(('Error', 'Exception', 'Warning')) or
                            isinstance(call.parent, nodes.Raise)):
                        continue

                    # Store both line number and context
                    context = None
                    for parent in call.node_ancestors():
                        if isinstance(parent, (nodes.FunctionDef, nodes.ClassDef)):
                            context = parent.name
                            break
                    method_calls[call.func.name].append((call.lineno, context))

        for method, calls in method_calls.items():
            unique_contexts = len(set(context for _, context in calls))
            if (len(calls) > self.thresholds["SHOTGUN_SURGERY_CALLS"] and
                    unique_contexts > self.thresholds["SHOTGUN_SURGERY_CONTEXTS"]):
                self.add_smell(
                    name="Potential Shotgun Surgery",
                    description=f"Method '{method}' called in {unique_contexts} different contexts across {len(calls)} locations in {file_path}",
                    file_path=file_path,
                    module_class=method,
                    line_number=calls[0][0],
                    severity='high'
                )

    def detect_comments(self, module, file_path):
        """
        Detect excessive comments in the given module and file.

        Args:
            module (astroid.Module): The AST module being analyzed
            file_path (str): Path to the file being analyzed
        """
        comment_blocks = []
        current_block = []
        code_lines = 0

        for i, line in enumerate(self.file_content):
            stripped_line = line.strip()
            if stripped_line.startswith('#'):
                current_block.append(i)
            else:
                if current_block:
                    comment_blocks.append(current_block)
                    current_block = []
                if stripped_line and not stripped_line.startswith('"""'):
                    code_lines += 1

        if current_block:
            comment_blocks.append(current_block)

        # Filter out license headers and module docstrings
        if comment_blocks and comment_blocks[0][0] == 0:
            comment_blocks.pop(0)

        # Calculate meaningful metrics
        comment_lines = sum(len(block) for block in comment_blocks)
        comment_ratio = comment_lines / max(code_lines, 1)
        large_comment_blocks = sum(1 for block in comment_blocks if len(block) > 5)

        if (comment_ratio > self.thresholds["EXCESSIVE_COMMENTS_RATIO"] and
                large_comment_blocks > self.thresholds["LARGE_COMMENT_BLOCKS"]):
            self.add_smell(
                name="Excessive Comments",
                description=f"File has {comment_ratio:.1%} comment ratio with {large_comment_blocks} large comment blocks in {file_path}",
                file_path=file_path,
                module_class=None,
                line_number=None,
                severity='low'
            )

    def detect_duplicate_code(self, module, file_path):
        """
        Detect duplicate code in the given module.
        """
        def normalize_code(node):
            """Normalize code by removing variable names and whitespace."""
            # as_string() carries no comments, so only identifiers and whitespace need handling
            code = node.as_string()
            # Replace variable names (not keywords) with placeholders
            code = re.sub(r'\b[a-zA-Z_]\w*\b',
                          lambda m: m.group() if keyword.iskeyword(m.group()) else 'VAR', code)
            # Remove whitespace
            return re.sub(r'\s+', '', code)

        code_blocks = defaultdict(list)
        for node in module.nodes_of_class(nodes.FunctionDef):
            # Skip small functions and test methods
            if (len(node.body) < self.thresholds["DUPLICATE_CODE_MIN_LINES"] or
                    node.name.startswith('test_')):
                continue

            # Skip simple getter/setter methods
            if len(node.body) == 1 and isinstance(node.body[0], (nodes.Return, nodes.Assign)):
                continue

            normalized_code = normalize_code(node)
            code_blocks[normalized_code].append((node.name, len(node.body)))

        for block, functions in code_blocks.items():
            if len(functions) >= self.thresholds["DUPLICATE_CODE_THRESHOLD"]:
                total_lines = sum(lines for _, lines in functions)
                self._file_findings[("Duplicate Code", block, file_path)] = self.add_smell(
                    name="Duplicate Code",
                    description=f"Similar code found in functions: {', '.join(f[0] for f in functions)} ({total_lines} total lines) in {file_path}",
                    file_path=file_path,
                    module_class=', '.join(f[0] for f in functions),
                    line_number=None,
                    severity='high'
                )

        # Accumulate for cross-file detection
        for normalized_code, functions in code_blocks.items():
            for func_name, num_lines in functions:
                self._global_code_blocks[normalized_code].append((func_name, file_path, num_lines))

    def detect_data_class(self, module, file_path):
        """
        Detect data classes: classes whose only methods are one-statement get_* /
        set_* accessors (at least DATA_CLASS_METHODS of them).
        """
        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip declared data holders and exceptions
            if ('dataclass' in self._decorator_names(node) or self._is_exception_class(node) or
                    node.name.endswith(('DTO', 'Model', 'Entity', 'Record'))):
                continue

            getters = setters = others = 0
            for method in node.mymethods():
                if method.name.startswith('__'):
                    continue  # Skip magic methods
                elif method.name.startswith('get_') and len(method.body) == 1:
                    getters += 1
                elif method.name.startswith('set_') and len(method.body) == 1:
                    setters += 1
                else:
                    others += 1

            # Only flag if class is purely getters/setters
            if others == 0 and getters + setters >= self.thresholds["DATA_CLASS_METHODS"]:
                self.add_smell(
                    name="Data Class",
                    description=f"Class '{node.name}' has {getters} getters and {setters} setters with no other methods in {file_path}",
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno,
                    severity='low'
                )

    def detect_dead_code(self, module, file_path):
        """
        Collect private module-level functions and private methods (one leading
        underscore) and every name the module refers to. Unreferenced ones are
        reported by the cross-file pass, once all files have been seen.
        """
        for node in module.nodes_of_class(nodes.FunctionDef):
            if not (node.name.startswith('_') and not node.name.startswith('__')):
                continue
            # Decorated functions are usually registered somewhere (routes, hooks,
            # properties, overloads) and are reachable without being named
            if node.decorators or not isinstance(node.parent, (nodes.Module, nodes.ClassDef)):
                continue
            owner = node.parent.name if isinstance(node.parent, nodes.ClassDef) else None
            # ponytail: any base may call a private hook (HelpFormatter._format_usage);
            # resolving which bases are project classes would let subclasses be checked too
            if owner and {b.as_string() for b in node.parent.bases} - {'object'}:
                continue
            self._private_defs.append((node.name, owner, file_path, node.lineno))

        referenced = self._referenced_names
        for node in module.nodes_of_class((nodes.Name, nodes.Attribute, nodes.AssignAttr,
                                           nodes.ImportFrom, nodes.Const)):
            if isinstance(node, nodes.Name):
                referenced.add(node.name)
            elif isinstance(node, (nodes.Attribute, nodes.AssignAttr)):
                referenced.add(node.attrname)
            elif isinstance(node, nodes.ImportFrom):
                referenced.update(name for name, _ in node.names)
            # Names in strings: __all__, getattr(self, '_handler'), dispatch tables
            elif isinstance(node.value, str) and node.value.isidentifier():
                referenced.add(node.value)

    def _cross_file_dead_code(self):
        unused = [d for d in self._private_defs if d[0] not in self._referenced_names]
        by_file = defaultdict(list)
        for name, owner, file_path, lineno in unused:
            by_file[file_path].append((name, owner, lineno))
        for file_path, defs in by_file.items():
            if len(defs) < self.thresholds["DEAD_CODE_THRESHOLD"]:
                continue
            for name, owner, lineno in defs:
                display_name = f"{owner}.{name}" if owner else name
                self.add_smell(
                    name="Dead Code",
                    description=f"Private function '{display_name}' is never referenced in the project ({file_path})",
                    file_path=file_path,
                    module_class=display_name,
                    line_number=lineno,
                    severity='low'
                )

    def detect_lazy_class(self, module, file_path):
        """
        Detect lazy classes: stand-alone classes (no bases, no decorators) with at
        most LAZY_CLASS_METHODS methods besides dunder methods, spanning at most
        LAZY_CLASS_LINES lines. Subclasses are skipped, since overriding one hook is how frameworks
        are extended, and so are classes without methods (namespaces, records).
        """
        for node in module.nodes_of_class(nodes.ClassDef):
            bases = {b.as_string() for b in node.bases} - {'object'}
            if (bases or node.decorators or node.keywords or
                    node.name.endswith(('Mixin', 'Interface', 'Abstract', 'Base'))):
                continue

            # Classes with only dunder methods are records or namespaces, not lazy
            all_methods = list(node.mymethods())
            if not any(not m.name.startswith('__') for m in all_methods):
                continue

            methods = [m for m in all_methods if not m.name.startswith('__')]
            total_lines = sum(m.tolineno - m.fromlineno for m in methods)
            if (len(methods) <= self.thresholds["LAZY_CLASS_METHODS"] and
                    total_lines <= self.thresholds["LAZY_CLASS_LINES"]):
                self.add_smell(
                    name="Lazy Class",
                    description=f"Class '{node.name}' has only {len(methods)} method(s) with {total_lines} total lines in {file_path}",
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno,
                    severity='low'
                )

    def detect_speculative_generality(self, module, file_path):
        """
        Detect speculative generality in the given module.
        """
        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip legitimate abstract base classes and typing.Protocol interfaces
            if (any(base.name.endswith('ABC') for base in node.bases if isinstance(base, nodes.Name)) or
                    any(base.as_string().split('[')[0].split('.')[-1] == 'Protocol'
                        for base in node.bases) or
                    node.name.endswith(('Interface', 'Base', 'Abstract'))):
                continue

            abstract_methods = []
            unused_params = []
            # A subclass method keeps the signature it overrides, used or not
            is_subclass = bool({b.as_string() for b in node.bases} - {'object'})

            for method in node.mymethods():
                # Abstract and overload stubs declare parameters they do not use
                if self._decorator_names(method) & {'abstractmethod', 'overload'}:
                    continue

                # Check for empty methods: a lone pass or ...
                body = method.body
                if len(body) == 1 and (isinstance(body[0], nodes.Pass) or (
                        isinstance(body[0], nodes.Expr) and isinstance(body[0].value, nodes.Const)
                        and body[0].value.value is Ellipsis)):
                    abstract_methods.append(method.name)

                # Subclass methods keep the signature they override; dunder methods
                # implement a protocol (__exit__, __get__) with a fixed signature
                if is_subclass or method.name.startswith('__'):
                    continue
                # Check for unused parameters; a leading underscore marks one as intentionally unused
                used_names = {n.name for n in method.nodes_of_class(nodes.Name)}
                unused_params.extend(sorted(
                    arg.name for arg, _ in self._parameters(method)
                    if arg.name not in used_names and not arg.name.startswith('_')))

            if (len(abstract_methods) >= self.thresholds["SPECULATIVE_GENERALITY_THRESHOLD"] or
                    len(unused_params) >= self.thresholds["UNUSED_PARAMETERS_THRESHOLD"]):
                description = []
                if abstract_methods:
                    description.append(
                        f"has {len(abstract_methods)} empty methods: {', '.join(abstract_methods)}")
                if unused_params:
                    description.append(
                        f"has {len(unused_params)} unused parameters: {', '.join(unused_params)}")

                self.add_smell(
                    name="Speculative Generality",
                    description=f"Class '{node.name}' {' and '.join(description)} in {file_path}",
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno,
                    severity='medium'
                )

    def detect_feature_envy(self, module, file_path):
        """
        Detect feature envy in the given module.
        """
        module_names = self._module_names
        for node in module.nodes_of_class(nodes.FunctionDef):
            # Skip property methods and simple delegators
            is_property = False
            if node.decorators:
                for decorator in node.decorators.nodes:
                    if isinstance(decorator, nodes.Name) and decorator.name == 'property':
                        is_property = True
                        break
                    elif isinstance(decorator, nodes.Call):
                        if isinstance(decorator.func,
                                      nodes.Name) and decorator.func.name == 'property':
                            is_property = True
                            break
                    elif isinstance(decorator, nodes.Attribute):
                        if decorator.attrname == 'property':
                            is_property = True
                            break

            # Envy compares use of another object with use of the method's own class,
            # so it applies to instance methods only, not to functions or static methods
            if (is_property or not isinstance(node.parent, nodes.ClassDef) or
                    node.name.startswith('test_') or
                    self._decorator_names(node) & {'staticmethod', 'classmethod'} or
                    len(node.body) == 1 and isinstance(node.body[0], nodes.Return)):
                continue

            # Track method calls by class
            class_calls = defaultdict(int)
            local_calls = 0

            for sub_node in node.nodes_of_class(nodes.Attribute):
                if isinstance(sub_node.expr, nodes.Name):
                    if sub_node.expr.name in ('self', 'cls'):
                        local_calls += 1
                    elif sub_node.expr.name not in module_names:
                        # Skip common utility objects
                        if sub_node.expr.name.lower() not in {
                                'logger', 'config', 'utils', 'helper'}:
                            class_calls[sub_node.expr.name] += 1

            if class_calls:
                max_calls = max(class_calls.values())
                max_class = max(class_calls.items(), key=lambda x: x[1])[0]

                # Check if external calls significantly outnumber local calls
                if (max_calls > self.thresholds["FEATURE_ENVY_CALLS"] and
                        max_calls > local_calls * 2):  # At least twice as many external calls
                    self.add_smell(
                        name="Feature Envy",
                        description=f"Method '{node.name}' makes {max_calls} calls to '{max_class}' but only {local_calls} local calls in {file_path}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno,
                        severity='medium'
                    )

    @staticmethod
    def _imported_names(module):
        """Names bound by import statements anywhere in the module (modules, not objects)."""
        names = set()
        for node in module.nodes_of_class((nodes.Import, nodes.ImportFrom)):
            for name, alias in node.names:
                if isinstance(node, nodes.Import):
                    names.add(alias or name.split('.')[0])
                else:
                    names.add(alias or name)
        return names

    @staticmethod
    def _root_name(node):
        """Name at the root of an attribute chain (a for a.b.c), or None."""
        while isinstance(node, (nodes.Attribute, nodes.AssignAttr)):
            node = node.expr
        return node.name if isinstance(node, nodes.Name) else None

    def detect_inappropriate_intimacy(self, module, file_path):
        """
        Detect inappropriate intimacy in the given module.
        """
        class_fields = defaultdict(set)
        class_methods = defaultdict(set)
        class_accesses = defaultdict(set)  # attributes used on objects other than self
        class_relationships = defaultdict(set)  # Track inheritance and composition
        module_names = self._module_names

        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip data classes and utility classes
            is_dataclass = False
            if node.decorators:
                for decorator in node.decorators.nodes:
                    if isinstance(decorator, nodes.Name) and decorator.name == 'dataclass':
                        is_dataclass = True
                        break
                    elif isinstance(decorator, nodes.Call):
                        if isinstance(decorator.func,
                                      nodes.Name) and decorator.func.name == 'dataclass':
                            is_dataclass = True
                            break
                    elif isinstance(decorator, nodes.Attribute):
                        if decorator.attrname == 'dataclass':
                            is_dataclass = True
                            break

            if (is_dataclass or node.name.endswith(('Utils', 'Helper', 'Factory'))):
                continue

            # Store class methods and fields
            class_methods[node.name] = {
                n.name for n in node.mymethods()
                if not n.name.startswith('__')  # Skip magic methods
            }
            # Intimacy is reaching into another class's private state; public
            # attributes are its interface and their names coincide across classes
            class_fields[node.name] = {f for f in node.instance_attrs
                                       if f.startswith('_') and not f.startswith('__')}
            # Attributes this class reads or writes on other objects (not self/cls, not modules)
            class_accesses[node.name] = {
                n.attrname for n in node.nodes_of_class((nodes.Attribute, nodes.AssignAttr))
                if n.expr.as_string() not in {'self', 'cls'} and
                self._root_name(n) not in module_names
            }

            # Track inheritance relationships
            for base in node.bases:
                if isinstance(base, nodes.Name):
                    class_relationships[node.name].add(base.name)

            # Track composition through instance variables
            for field in node.instance_attrs.values():
                if isinstance(field, nodes.AssignAttr) and isinstance(field.expr, nodes.Name):
                    class_relationships[node.name].add(field.expr.name)

        # Accumulate for cross-file detection
        for class_name in class_methods:
            key = f"{file_path}::{class_name}"
            self._global_class_info[key] = {
                "fields": class_fields[class_name],
                "methods": class_methods[class_name],
                "accesses": class_accesses[class_name],
                "relationships": class_relationships[class_name],
                "class_name": class_name,
                "file_path": file_path,
            }

        for class_name in class_methods:
            for other_class, other_fields in class_fields.items():
                if class_name != other_class:
                    # Skip if there's a valid relationship
                    if (other_class in class_relationships[class_name] or
                            class_name in class_relationships[other_class]):
                        continue

                    shared = len(class_accesses[class_name] & other_fields)
                    field_ratio = shared / len(other_fields) if other_fields else 0

                    if (shared > self.thresholds["INAPPROPRIATE_INTIMACY_SHARED"] and
                            field_ratio > 0.3):  # Uses more than 30% of the other's fields
                        self.add_smell(
                            name="Inappropriate Intimacy",
                            description=f"Class '{class_name}' might be too intimate with '{other_class}' "
                            f"(uses {shared} of its fields, {field_ratio:.1%}) in {file_path}",
                            file_path=file_path,
                            module_class=class_name,
                            line_number=None,
                            severity='medium'
                        )

    def detect_message_chains(self, module, file_path):
        """
        Detect message chains in the given module.
        """
        def get_chain_length(node):
            length = 0
            chain = []
            current = node
            while isinstance(current, nodes.Attribute):
                length += 1
                chain.append(current.attrname)
                current = current.expr
            return length, chain

        def is_builder_pattern(chain):
            """Check if the chain follows builder pattern."""
            return all(name.startswith(('set_', 'with_', 'add_')) for name in chain)

        def is_common_pattern(chain):
            """True if every link after the first object is part of one common API (paths, ORM)."""
            common_patterns = {
                'logging': {'debug', 'info', 'warning', 'error', 'critical'},
                'paths': {'parent', 'name', 'suffix', 'stem'},
                'testing': {'assert_', 'expect', 'mock'},
                'db': {'query', 'filter', 'order_by', 'limit', 'all', 'first'}
            }
            return any(all(method in pattern for method in chain[:-1])
                       for pattern in common_patterns.values())

        module_names = self._module_names
        for node in module.nodes_of_class(nodes.Attribute):
            # Measure each chain once, from its outermost attribute
            if isinstance(node.parent, nodes.Attribute) and node.parent.expr is node:
                continue
            chain_length, chain = get_chain_length(node)

            # Skip if it's a valid pattern; a.b.c.d on an imported module is a path, not a chain
            if (chain_length <= self.thresholds["MESSAGE_CHAIN_LENGTH"] or
                is_builder_pattern(chain) or
                    is_common_pattern(chain) or
                    self._root_name(node) in module_names):
                continue

            # Get context for better description
            context = None
            for parent in node.node_ancestors():
                if isinstance(parent, (nodes.FunctionDef, nodes.ClassDef)):
                    context = parent.name
                    break

            self.add_smell(
                name="Message Chains",
                description=f"Long chain ({chain_length} calls: {' -> '.join(reversed(chain))}) "
                f"in {context or 'unknown context'} at line {node.lineno} in {file_path}",
                file_path=file_path,
                module_class=context,
                line_number=node.lineno,
                severity='medium'
            )

    def detect_middle_man(self, module, file_path):
        """
        Detect middle man classes in the given module.
        """
        for node in module.nodes_of_class(nodes.ClassDef):
            # Skip known patterns and small classes
            if (node.name.endswith(('Proxy', 'Delegate', 'Adapter', 'Facade')) or
                    len(node.body) <= 3):  # Very small classes might be intentional adapters
                continue

            methods = list(node.mymethods())
            total_methods = len(methods)

            if total_methods == 0:
                continue

            delegating_methods = 0
            delegate_targets = defaultdict(list)

            for method in methods:
                # Skip property methods and magic methods
                is_property = False
                if method.decorators:
                    for decorator in method.decorators.nodes:
                        if isinstance(decorator, nodes.Name) and decorator.name == 'property':
                            is_property = True
                            break
                        elif isinstance(decorator, nodes.Call):
                            if isinstance(decorator.func,
                                          nodes.Name) and decorator.func.name == 'property':
                                is_property = True
                                break
                        elif isinstance(decorator, nodes.Attribute):
                            if decorator.attrname == 'property':
                                is_property = True
                                break

                if is_property or method.name.startswith('__'):
                    continue

                # Check if method is just delegating
                if len(method.body) == 1 and isinstance(method.body[0], nodes.Return):
                    return_value = method.body[0].value
                    func = return_value.func if isinstance(return_value, nodes.Call) else None
                    # Delegation forwards to another object: return <obj>.<method>(...),
                    # not a plain function call and not a call to one of self's own methods
                    if isinstance(func, nodes.Attribute) and func.expr.as_string() != 'self':
                        delegating_methods += 1
                        delegate_targets[func.expr.as_string()].append(method.name)

            delegation_ratio = delegating_methods / total_methods if total_methods > 0 else 0
            if (delegation_ratio > self.thresholds["MIDDLE_MAN_RATIO"] and
                    len(delegate_targets) <= 2):  # Only flag if delegating to 1-2 objects
                primary_delegate = max(delegate_targets.items(), key=lambda x: len(x[1]))
                self.add_smell(
                    name="Middle Man",
                    description=f"Class '{node.name}' delegates {delegating_methods}/{total_methods} methods "
                    f"({delegation_ratio:.1%}), mainly to {primary_delegate[0]} in {file_path}",
                    file_path=file_path,
                    module_class=node.name,
                    line_number=node.lineno,
                    severity='medium'
                )

    def detect_cross_file_smells(self):
        """
        Detect smells requiring cross-file context.
        Call this once after all per-file detect_smells() calls are complete.
        """
        self._cross_file_alternative_classes()
        self._cross_file_data_clumps()
        self._cross_file_duplicate_code()
        self._cross_file_inappropriate_intimacy()
        self._cross_file_parallel_inheritance()
        self._cross_file_temporary_fields()
        self._cross_file_dead_code()

    def _cross_file_temporary_fields(self):
        """Drop fields that some other file reads through an object, then findings left too small."""
        for smell, fields in self._temp_field_findings:
            remaining = fields - self._attr_reads
            if len(remaining) < self.thresholds["TEMPORARY_FIELD_THRESHOLD"]:
                self.code_smells.remove(smell)
            elif remaining != fields:
                smell.description = self._temporary_field_description(
                    remaining, smell.module_class, smell.line_number, smell.file_path)
        self._temp_field_findings = []

    def _cross_file_alternative_classes(self):
        for methods, entries in self._global_class_methods.items():
            if len(methods) < 2:
                continue
            files_seen = sorted({fp for _, fp in entries})
            if len(files_seen) < 2:
                continue
            if self._share_base(self._global_class_bases[e] for e in entries):
                continue
            if len(entries) >= self.thresholds["ALTERNATIVE_CLASSES_THRESHOLD"]:
                self._drop_file_findings("Alternative Classes", methods, files_seen)
                class_list = [f"{cls} ({fp})" for cls, fp in entries]
                self.add_smell(
                    name="Alternative Classes with Different Interfaces",
                    description=f"Classes {', '.join(class_list)} share similar methods {', '.join(sorted(methods))} across files",
                    file_path=", ".join(files_seen),
                    module_class=", ".join(cls for cls, _ in entries),
                    line_number=None,
                    severity='medium'
                )

    def _cross_file_data_clumps(self):
        entries = self._global_param_funcs
        for params, members in self._maximal_param_groups([p for _, _, p in entries]).items():
            files_seen = sorted({entries[i][1] for i in members})
            if len(files_seen) < 2:
                continue
            self._drop_file_findings("Data Clumps", params, files_seen)
            func_list = [f"{entries[i][0]} ({entries[i][1]})" for i in members]
            self.add_smell(
                name="Data Clumps",
                description=f"Parameters {', '.join(sorted(params))} appear together across files in: {', '.join(func_list)}",
                file_path=", ".join(files_seen),
                module_class=", ".join(entries[i][0] for i in members),
                line_number=None,
                severity='medium'
            )

    def _drop_file_findings(self, name, key, files):
        """Remove per-file findings superseded by a cross-file finding for the same group."""
        for fp in files:
            smell = self._file_findings.pop((name, key, fp), None)
            if smell is not None:
                self.code_smells.remove(smell)

    def _cross_file_duplicate_code(self):
        for normalized_code, entries in self._global_code_blocks.items():
            files_seen = sorted({fp for _, fp, _ in entries})
            if len(files_seen) < 2:
                continue
            if len(entries) >= self.thresholds["DUPLICATE_CODE_THRESHOLD"]:
                self._drop_file_findings("Duplicate Code", normalized_code, files_seen)
                total_lines = sum(nl for _, _, nl in entries)
                func_list = [f"{fn} ({fp})" for fn, fp, _ in entries]
                self.add_smell(
                    name="Duplicate Code",
                    description=f"Similar code found across files in functions: {', '.join(func_list)} ({total_lines} total lines)",
                    file_path=", ".join(files_seen),
                    module_class=", ".join(fn for fn, _, _ in entries),
                    line_number=None,
                    severity='high'
                )

    def _cross_file_inappropriate_intimacy(self):
        entries = list(self._global_class_info.values())
        for a, b in permutations(entries, 2):
            if a["file_path"] == b["file_path"]:
                continue
            if (b["class_name"] in a["relationships"] or
                    a["class_name"] in b["relationships"]):
                continue
            shared = len(a["accesses"] & b["fields"])
            field_ratio = shared / len(b["fields"]) if b["fields"] else 0
            if (shared > self.thresholds["INAPPROPRIATE_INTIMACY_SHARED"] and
                    field_ratio > 0.3):
                self.add_smell(
                    name="Inappropriate Intimacy",
                    description=(
                        f"Class '{a['class_name']}' ({a['file_path']}) might be too intimate "
                        f"with '{b['class_name']}' ({b['file_path']}) "
                        f"(uses {shared} of its fields, {field_ratio:.1%})"
                    ),
                    file_path=a["file_path"],
                    module_class=a["class_name"],
                    line_number=None,
                    severity='medium'
                )

    def _cross_file_parallel_inheritance(self):
        class_info = {}
        for key, info in self._global_class_info.items():
            class_info[info["class_name"]] = info.get("methods", set())

        hierarchies = {
            base: [child for child, _ in children]
            for base, children in self._global_class_hierarchies.items()
        }
        hierarchy_files = {
            base: {fp for _, fp in children}
            for base, children in self._global_class_hierarchies.items()
        }

        if len(hierarchies) <= 1:
            return

        for (b1, h1), (b2, h2) in combinations(hierarchies.items(), 2):
            all_files = hierarchy_files[b1] | hierarchy_files[b2]
            if len(all_files) < 2:
                continue
            if len(h1) > 1 and len(h2) > 1:
                if self._names_correspond(b1, h1, b2, h2):
                    if h1[0] in class_info and h2[0] in class_info:
                        union_size = len(class_info[h1[0]] | class_info[h2[0]])
                        if union_size > 0:
                            similarity = len(class_info[h1[0]] & class_info[h2[0]]) / union_size
                            if similarity > 0.3:
                                self.add_smell(
                                    name="Parallel Inheritance Hierarchies",
                                    description=(
                                        f"Parallel cross-file hierarchies: "
                                        f"{' -> '.join(h1)} and {' -> '.join(h2)}"
                                    ),
                                    file_path=", ".join(sorted(all_files)),
                                    module_class=None,
                                    line_number=None,
                                    severity='high'
                                )

    def print_report(self):
        """
        Print a report of all detected code smells.

        If no code smells are detected, it prints a message indicating so.
        """
        if not self.code_smells:
            print("No code smells detected.")
        else:
            print("Detected Code Smells:")
            for smell in self.code_smells:
                print(f"- {smell.name}: {smell.description}")

    @staticmethod
    def _decorator_names(node):
        """Last dotted part of each decorator: @property, @x.setter, @dataclass(frozen=True)."""
        names = set()
        for decorator in node.decorators.nodes if node.decorators else ():
            target = decorator.func if isinstance(decorator, nodes.Call) else decorator
            names.add(target.as_string().split('.')[-1])
        return names

    @staticmethod
    def _is_exception_class(node):
        return node.name.endswith(('Error', 'Exception', 'Warning')) or any(
            base.as_string().split('.')[-1].endswith(('Error', 'Exception', 'Warning'))
            for base in node.bases)

    @staticmethod
    def _parameters(node):
        """All named parameters (positional-only, regular, keyword-only) without self / cls."""
        args = node.args
        params = list(args.posonlyargs or []) + list(args.args or []) + list(args.kwonlyargs or [])
        annotations = (list(args.posonlyargs_annotations or []) + list(args.annotations or []) +
                       list(args.kwonlyargs_annotations or []))
        annotations += [None] * (len(params) - len(annotations))
        pairs = list(zip(params, annotations))
        if (pairs and pairs[0][0].name in ('self', 'cls') and
                isinstance(node.parent, nodes.ClassDef)):
            pairs = pairs[1:]
        return pairs

    def add_smell(self, name, description, file_path, module_class,
                  line_number=None, severity='medium'):
        """
        Add a detected smell to the list of code smells.

        Args:
            name (str): The name of the smell
            description (str): Description of the smell
            file_path (str): Path to the file containing the smell
            module_class (str): The module or class containing the smell
            line_number (int, optional): The line number where the smell was detected
            severity (str, optional): The severity level of the smell (default: 'medium')
        """
        smell = CodeSmell(
            name=name,
            description=description,
            file_path=file_path,
            module_class=module_class,
            line_number=line_number,
            severity=severity
        )
        self.code_smells.append(smell)
        return smell

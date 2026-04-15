import astroid
from astroid import nodes, exceptions as astroid_exceptions
import os
from collections import defaultdict
from dataclasses import dataclass

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

    def detect_smells(self, file_path):
        """
        Detect code smells in the given file.

        This method reads the file, parses it using astroid, and runs all the smell detection methods.
        If a parse error occurs, it prints the error message and continues with the analysis.

        Args:
            file_path (str): The path to the file to be analyzed.
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            
            module = astroid.parse(content)
            self.file_content = content.split('\n')
            
            # Call all smell detection methods
            self.detect_long_methods(module, file_path)
            self.detect_large_classes(module, file_path)
            self.detect_primitive_obsession(module, file_path)
            self.detect_long_parameter_lists(module, file_path)
            self.detect_data_clumps(module, file_path)
            self.detect_switch_statements(module, file_path)
            self.detect_temporary_fields(module, file_path)
            self.detect_alternative_classes(module, file_path)
            self.detect_divergent_change(module, file_path)
            self.detect_parallel_inheritance(module, file_path)
            self.detect_shotgun_surgery(module, file_path)
            self.detect_comments(file_path)
            self.detect_duplicate_code(module, file_path)
            self.detect_dead_code(module, file_path)
            self.detect_lazy_class(module, file_path)
            self.detect_speculative_generality(module, file_path)
            self.detect_feature_envy(module, file_path)
            self.detect_inappropriate_intimacy(module, file_path)
            self.detect_message_chains(module, file_path)
            self.detect_middle_man(module, file_path)
        except astroid_exceptions.AstroidSyntaxError as e:
            print(f"Parse error in file {file_path}: {str(e)}")
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")

    def detect_long_methods(self, module, file_path):
        """
        Detect long methods in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                if node.tolineno - node.fromlineno > self.thresholds["LONG_METHOD_LINES"]:
                    self.code_smells.append(CodeSmell(
                        name="Long Method",
                        description=f"'{node.name}' in {file_path} at line {node.lineno}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_large_classes(self, module, file_path):
        """
        Detect large classes in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, nodes.FunctionDef)])
                if method_count > self.thresholds["LARGE_CLASS_METHODS"]:
                    self.code_smells.append(CodeSmell(
                        name="Large Class",
                        description=f"'{node.name}' in {file_path} at line {node.lineno}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_primitive_obsession(self, module, file_path):
        """
        Detect primitive obsession in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                primitives = []
                for i, arg in enumerate(node.args.args):
                    if isinstance(arg, nodes.AssignName):
                        if i < len(node.args.annotations):
                            arg_type = node.args.annotations[i]
                            if (isinstance(arg_type, nodes.Name) and 
                                arg_type.name in ['int', 'str', 'float', 'bool']):
                                primitives.append(arg)
                if len(primitives) > self.thresholds["PRIMITIVE_OBSESSION_COUNT"]:
                    self.code_smells.append(CodeSmell(
                        name="Primitive Obsession",
                        description=f"'{node.name}' in {file_path} at line {node.lineno}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_long_parameter_lists(self, module, file_path):
        """
        Detect long parameter lists in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                if len(node.args.args) > self.thresholds["LONG_PARAMETER_LIST"]:
                    self.code_smells.append(CodeSmell(
                        name="Long Parameter List",
                        description=f"'{node.name}' in {file_path} at line {node.lineno}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_data_clumps(self, module, file_path):
        """
        Detect data clumps in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        parameter_groups = defaultdict(list)
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                params = tuple(sorted(arg.name for arg in node.args.args))
                if len(params) >= 3:
                    parameter_groups[params].append(node.name)
        
        for params, functions in parameter_groups.items():
            if len(functions) > 1:
                self.code_smells.append(CodeSmell(
                    name="Data Clumps",
                    description=f"Parameters {', '.join(params)} appear together in functions: {', '.join(functions)} in {file_path}",
                    file_path=file_path,
                    module_class=', '.join(functions),
                    line_number=None
                ))

    def detect_switch_statements(self, module, file_path):
        """
        Detect switch statements in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.If) and len(node.orelse) > self.thresholds["COMPLEX_CONDITIONAL"]:
                self.code_smells.append(CodeSmell(
                    name="Switch Statements",
                    description=f"Complex conditional at line {node.lineno} in {file_path}",
                    file_path=file_path,
                    module_class=None,
                    line_number=node.lineno
                ))

    def detect_temporary_fields(self, module, file_path):
        """
        Detect temporary fields in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                init_fields = set()
                used_fields = set()
                for child in node.body:
                    if isinstance(child, nodes.FunctionDef):
                        if child.name == '__init__':
                            init_fields = {target.name for target in child.nodes_of_class(nodes.AssignName)}
                        else:
                            used_fields.update({n.attrname for n in child.nodes_of_class(nodes.Attribute) if isinstance(n.expr, nodes.Name) and n.expr.name == 'self'})
                temp_fields = init_fields - used_fields
                if temp_fields:
                    self.code_smells.append(CodeSmell(
                        name="Temporary Field",
                        description=f"{', '.join(temp_fields)} in class '{node.name}' at line {node.lineno} in {file_path}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_alternative_classes(self, module, file_path):
        """
        Detect alternative classes with different interfaces in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        class_methods = defaultdict(list)
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                methods = frozenset(n.name for n in node.mymethods())
                class_methods[methods].append(node.name)
        
        for methods, classes in class_methods.items():
            if len(classes) > 1:
                self.code_smells.append(CodeSmell(
                    name="Alternative Classes with Different Interfaces",
                    description=f"{', '.join(classes)} in {file_path}",
                    file_path=file_path,
                    module_class=', '.join(classes),
                    line_number=None
                ))

    def detect_divergent_change(self, module, file_path):
        """
        Detect divergent change in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                method_prefixes = [n.name.split('_')[0] for n in node.mymethods()]
                if len(set(method_prefixes)) > self.thresholds["DIVERGENT_CHANGE_PREFIXES"]:
                    self.code_smells.append(CodeSmell(
                        name="Potential Divergent Change",
                        description=f"Class '{node.name}' at line {node.lineno} in {file_path}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_parallel_inheritance(self, module, file_path):
        """
        Detect parallel inheritance hierarchies in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        class_hierarchies = defaultdict(list)
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                for base in node.bases:
                    if isinstance(base, nodes.Name):
                        class_hierarchies[base.name].append(node.name)
        
        if len(class_hierarchies) > 1:
            hierarchies = [h for h in class_hierarchies.values() if len(h) > 1]
            if len(set(map(tuple, hierarchies))) > 1:
                self.code_smells.append(CodeSmell(
                    name="Parallel Inheritance Hierarchies",
                    description=f"Parallel Inheritance Hierarchies detected in {file_path}",
                    file_path=file_path,
                    module_class=None,
                    line_number=None
                ))

    def detect_shotgun_surgery(self, module, file_path):
        """
        Detect potential shotgun surgery in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        method_calls = defaultdict(set)
        for node in module.body:
            for call in node.nodes_of_class(nodes.Call):
                if isinstance(call.func, nodes.Name):
                    method_calls[call.func.name].add(call.lineno)
        
        for method, calls in method_calls.items():
            if len(calls) > self.thresholds["SHOTGUN_SURGERY_CALLS"]:
                self.code_smells.append(CodeSmell(
                    name="Potential Shotgun Surgery",
                    description=f"Method '{method}' called in multiple places in {file_path}",
                    file_path=file_path,
                    module_class=method,
                    line_number=None
                ))

    def detect_comments(self, file_path):
        """
        Detect excessive comments in the given file.

        Args:
            file_path (str): The path of the file being analyzed.
        """
        comment_lines = [i for i, line in enumerate(self.file_content) if line.strip().startswith('#')]
        if len(comment_lines) > len(self.file_content) * self.thresholds["EXCESSIVE_COMMENTS_RATIO"]:
            self.code_smells.append(CodeSmell(
                name="Excessive Comments",
                description=f"Excessive Comments detected in {file_path}",
                file_path=file_path,
                module_class=None,
                line_number=None
            ))

    def detect_duplicate_code(self, module, file_path):
        """
        Detect duplicate code in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        code_blocks = defaultdict(list)
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                block = node.as_string()
                code_blocks[block].append(node.name)
        
        for block, functions in code_blocks.items():
            if len(functions) > 1:
                self.code_smells.append(CodeSmell(
                    name="Duplicate Code",
                    description=f"Functions {', '.join(functions)} in {file_path}",
                    file_path=file_path,
                    module_class=', '.join(functions),
                    line_number=None
                ))

    def detect_data_class(self, module, file_path):
        """
        Detect data classes in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                methods = [n for n in node.mymethods()]
                if all(m.name.startswith(('__', 'get_', 'set_')) for m in methods):
                    self.code_smells.append(CodeSmell(
                        name="Data Class",
                        description=f"'{node.name}' at line {node.lineno} in {file_path}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_dead_code(self, module, file_path):
        """
        Detect dead code in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        defined_functions = set()
        called_functions = set()
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                defined_functions.add(node.name)
            for call in node.nodes_of_class(nodes.Call):
                if isinstance(call.func, nodes.Name):
                    called_functions.add(call.func.name)
        
        unused_functions = defined_functions - called_functions
        for func in unused_functions:
            self.code_smells.append(CodeSmell(
                name="Dead Code",
                description=f"Unused function '{func}' in {file_path}",
                file_path=file_path,
                module_class=func,
                line_number=None
            ))

    def detect_lazy_class(self, module, file_path):
        """
        Detect lazy classes in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                methods = list(node.mymethods())
                if len(methods) <= self.thresholds["LAZY_CLASS_METHODS"]:
                    self.code_smells.append(CodeSmell(
                        name="Lazy Class",
                        description=f"'{node.name}' at line {node.lineno} in {file_path}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_speculative_generality(self, module, file_path):
        """
        Detect speculative generality in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                abstract_methods = [n for n in node.mymethods() if n.body and isinstance(n.body[0], nodes.Pass)]
                if abstract_methods:
                    self.code_smells.append(CodeSmell(
                        name="Speculative Generality",
                        description=f"Abstract class '{node.name}' at line {node.lineno} in {file_path}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_feature_envy(self, module, file_path):
        """
        Detect feature envy in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                attr_calls = defaultdict(int)
                for sub_node in node.nodes_of_class(nodes.Attribute):
                    if isinstance(sub_node.expr, nodes.Name) and sub_node.expr.name != 'self':
                        attr_calls[sub_node.expr.name] += 1
                
                if attr_calls and max(attr_calls.values()) > self.thresholds["FEATURE_ENVY_CALLS"]:
                    envied_class = max(attr_calls, key=attr_calls.get)
                    self.code_smells.append(CodeSmell(
                        name="Feature Envy",
                        description=f"Method '{node.name}' at line {node.lineno} might be envying class related to '{envied_class}' in {file_path}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

    def detect_inappropriate_intimacy(self, module, file_path):
        """
        Detect inappropriate intimacy in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        class_fields = defaultdict(set)
        class_methods = defaultdict(set)
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                class_methods[node.name] = {n.name for n in node.mymethods()}
                class_fields[node.name] = set(node.instance_attrs.keys())
        
        for class_name, methods in class_methods.items():
            for other_class, other_fields in class_fields.items():
                if class_name != other_class:
                    shared = len(methods.intersection(other_fields))
                    if shared > self.thresholds["INAPPROPRIATE_INTIMACY_SHARED"]:
                        self.code_smells.append(CodeSmell(
                            name="Inappropriate Intimacy",
                            description=f"Class '{class_name}' might be too intimate with '{other_class}' in {file_path}",
                            file_path=file_path,
                            module_class=class_name,
                            line_number=None
                        ))

    def detect_message_chains(self, module, file_path):
        """
        Detect message chains in the given module.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        def get_chain_length(node):
            length = 0
            while isinstance(node, nodes.Attribute):
                length += 1
                node = node.expr
            return length

        for node in module.nodes_of_class(nodes.Attribute):
            chain_length = get_chain_length(node)
            if chain_length > self.thresholds["MESSAGE_CHAIN_LENGTH"]:
                self.code_smells.append(CodeSmell(
                    name="Message Chains",
                    description=f"Long chain detected at line {node.lineno} in {file_path}",
                    file_path=file_path,
                    module_class=None,
                    line_number=node.lineno
                ))

    def detect_middle_man(self, module, file_path):
        """
        Detect middle man classes in the given module.

        A middle man class is one where more than half of its methods simply delegate to another class.

        Args:
            module (astroid.Module): The parsed module to analyze.
            file_path (str): The path of the file being analyzed.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                methods = list(node.mymethods())
                total_methods = len(methods)
                
                if total_methods == 0:
                    continue  # Skip classes with no methods
                
                delegating_methods = 0
                for method in methods:
                    if len(method.body) == 1 and isinstance(method.body[0], nodes.Return):
                        if isinstance(method.body[0].value, nodes.Call):
                            delegating_methods += 1
                
                if total_methods > 0 and delegating_methods / total_methods > 0.5:
                    self.code_smells.append(CodeSmell(
                        name="Middle Man",
                        description=f"Class '{node.name}' at line {node.lineno} in {file_path}",
                        file_path=file_path,
                        module_class=node.name,
                        line_number=node.lineno
                    ))

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
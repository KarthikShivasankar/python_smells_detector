import ast
import os
from collections import defaultdict
import networkx as nx
import yaml

class StructuralSmellDetector:
    def __init__(self, config_path):
        self.structural_smells = []
        self.class_info = defaultdict(dict)
        self.module_info = defaultdict(dict)
        self.dependency_graph = nx.DiGraph()
        self.thresholds = self.load_thresholds(config_path)
        self.project_root = None

    def load_thresholds(self, config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return {k: v['value'] for k, v in config['structural_smells'].items()}

    def detect_smells(self, directory_path):
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
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)

    def analyze_file(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        
        module = ast.parse(content)
        module_name = os.path.basename(file_path)[:-3]
        self.module_info[module_name]['loc'] = len(content.split('\n'))
        
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef):
                self.analyze_class(node, module_name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.dependency_graph.add_edge(module_name, alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.dependency_graph.add_edge(module_name, node.module)

    def analyze_class(self, node, module_name):
        class_name = f"{module_name}.{node.name}"
        self.class_info[class_name]['methods'] = []
        self.class_info[class_name]['fields'] = set()
        self.class_info[class_name]['method_calls'] = defaultdict(set)
        self.class_info[class_name]['base_classes'] = [self.resolve_base_class(base, module_name) for base in node.bases]
        
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                self.class_info[class_name]['methods'].append(child)
                self.analyze_method(child, class_name)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        self.class_info[class_name]['fields'].add(target.id)

    def analyze_method(self, node, class_name):
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    self.class_info[class_name]['method_calls'][node.name].add(child.func.attr)

    def detect_nom(self):
        for class_name, info in self.class_info.items():
            nom = len(info['methods'])
            if nom > self.thresholds['NOM_THRESHOLD']:
                self.structural_smells.append(f"High Number of Methods: Class '{class_name}' has {nom} methods")

    def detect_wmpc(self):
        for class_name, info in self.class_info.items():
            wmpc1 = sum(self.calculate_cyclomatic_complexity(method) for method in info['methods'])
            wmpc2 = sum(len(method.args.args) for method in info['methods'])
            if wmpc1 > self.thresholds['WMPC1_THRESHOLD'] or wmpc2 > self.thresholds['WMPC2_THRESHOLD']:
                self.structural_smells.append(f"High Weighted Methods per Class: Class '{class_name}' (WMPC1: {wmpc1}, WMPC2: {wmpc2})")

    def detect_size2(self):
        for class_name, info in self.class_info.items():
            size2 = len(info['methods']) + len(info['fields'])
            if size2 > self.thresholds['SIZE2_THRESHOLD']:
                self.structural_smells.append(f"Large Class Size: Class '{class_name}' has size metric of {size2}")

    def detect_wac(self):
        for class_name, info in self.class_info.items():
            wac = len(info['fields'])
            if wac > self.thresholds['WAC_THRESHOLD']:
                self.structural_smells.append(f"High Weighted Attribute Count: Class '{class_name}' has {wac} fields")

    def detect_lcom(self):
        for class_name, info in self.class_info.items():
            methods = info['methods']
            fields = info['fields']
            method_field_usage = {method: set() for method in methods}
            
            for method in methods:
                for field in fields:
                    if field in info['method_calls'][method]:
                        method_field_usage[method].add(field)
            
            non_cohesive_pairs = 0
            cohesive_pairs = 0
            
            for i, method1 in enumerate(methods):
                for method2 in methods[i+1:]:
                    if not method_field_usage[method1].intersection(method_field_usage[method2]):
                        non_cohesive_pairs += 1
                    else:
                        cohesive_pairs += 1
            
            lcom = max(0, non_cohesive_pairs - cohesive_pairs)
            if lcom > self.thresholds['LCOM_THRESHOLD']:
                self.structural_smells.append(f"Lack of Cohesion in Methods: Class '{class_name}' has LCOM of {lcom}")

    def detect_rfc(self):
        for class_name, info in self.class_info.items():
            rfc = len(info['methods']) + sum(len(calls) for calls in info['method_calls'].values())
            if rfc > self.thresholds['RFC_THRESHOLD']:
                self.structural_smells.append(f"High Response for Class: Class '{class_name}' has RFC of {rfc}")

    def detect_nocc(self):
        class_hierarchy = defaultdict(list)
        for class_name in self.class_info.keys():
            module, name = class_name.split('.')
            class_hierarchy[module].append(name)
        
        for module, classes in class_hierarchy.items():
            if len(classes) > self.thresholds['NOCC_THRESHOLD']:
                self.structural_smells.append(f"High Number of Children: Module '{module}' has {len(classes)} classes")

    def detect_dit(self):
        inheritance_graph = nx.DiGraph()
        
        # Build the inheritance graph
        for class_name, info in self.class_info.items():
            module, name = class_name.split('.')
            inheritance_graph.add_node(class_name)
            
            # Get the base classes
            base_classes = self.get_base_classes(module, name)
            for base in base_classes:
                inheritance_graph.add_edge(base, class_name)
        
        # Add 'object' as the root if it's not present
        if 'object' not in inheritance_graph:
            inheritance_graph.add_node('object')
            for node in inheritance_graph.nodes():
                if inheritance_graph.in_degree(node) == 0 and node != 'object':
                    inheritance_graph.add_edge('object', node)
        
        # Calculate DIT for each class
        for class_name in inheritance_graph.nodes():
            if class_name != 'object':
                try:
                    dit = nx.shortest_path_length(inheritance_graph, 'object', class_name)
                    if dit > self.thresholds['DIT_THRESHOLD']:
                        self.structural_smells.append(f"Deep Inheritance Tree: Class '{class_name}' has DIT of {dit}")
                except nx.NetworkXNoPath:
                    # Handle cases where there's no path from 'object' to the class
                    self.structural_smells.append(f"Isolated Class in Inheritance Tree: '{class_name}'")

    def get_base_classes(self, module, class_name):
        file_path = self.find_file_for_module(module)
        if not file_path:
            return ['object']
        
        with open(file_path, 'r') as file:
            tree = ast.parse(file.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return [self.resolve_base_class(base, module) for base in node.bases]
        
        return ['object']

    def resolve_base_class(self, base_node, current_module):
        if isinstance(base_node, ast.Name):
            return f"{current_module}.{base_node.id}"
        elif isinstance(base_node, ast.Attribute):
            return f"{base_node.value.id}.{base_node.attr}"
        else:
            return 'object'

    def find_file_for_module(self, module_name):
        if self.project_root is None:
            raise ValueError("Project root is not set. Call detect_smells first.")
        
        for root, _, files in os.walk(self.project_root):
            if f"{module_name}.py" in files:
                return os.path.join(root, f"{module_name}.py")
        return None

    def detect_loc(self):
        for module_name, info in self.module_info.items():
            loc = info['loc']
            if loc > self.thresholds['LOC_THRESHOLD']:
                self.structural_smells.append(f"High Lines of Code: Module '{module_name}' has {loc} lines")

    def detect_mpc(self):
        for class_name, info in self.class_info.items():
            mpc = sum(len(calls) for calls in info['method_calls'].values())
            if mpc > self.thresholds['MPC_THRESHOLD']:
                self.structural_smells.append(f"High Method Propagation Coupling: Class '{class_name}' has MPC of {mpc}")

    def detect_cbo(self):
        for module in self.dependency_graph.nodes():
            cbo = self.dependency_graph.degree(module)
            if cbo > self.thresholds['CBO_THRESHOLD']:
                self.structural_smells.append(f"High Coupling Between Object Classes: Module '{module}' has CBO of {cbo}")

    def detect_noc(self):
        noc = len(self.class_info)
        if noc > self.thresholds['NOC_THRESHOLD']:
            self.structural_smells.append(f"High Number of Classes: Project has {noc} classes")

    def calculate_cyclomatic_complexity(self, method_node):
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

    def print_report(self):
        if not self.structural_smells:
            print("No structural smells detected.")
        else:
            print("Detected Structural Smells:")
            for smell in self.structural_smells:
                print(f"- {smell}")

def analyze_structural_smells(directory_path, config_path):
    detector = StructuralSmellDetector(config_path)
    detector.detect_smells(directory_path)
    detector.print_report()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Detect structural smells in Python code.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default="code_quality_config.yaml", help="Path to the configuration file")
    args = parser.parse_args()

    analyze_structural_smells(args.directory, args.config)


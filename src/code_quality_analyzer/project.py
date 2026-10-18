"""File discovery and import resolution shared by the detectors."""
import ast
import os
import sys

# Never project code: caches, virtualenvs, vendored installs. Hidden dirs are skipped too.
SKIP_DIRS = {'__pycache__', 'node_modules', 'site-packages', 'venv'}
STDLIB_MODULES = frozenset(sys.stdlib_module_names)


def iter_python_files(path, ignore_dirs=()):
    """Yield the .py files under path in a stable order, or path itself if it is a .py file."""
    if os.path.isfile(path):
        if path.endswith('.py'):
            yield path
        return
    ignore = set(ignore_dirs or ())
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs
                         if d not in ignore and d not in SKIP_DIRS and not d.startswith('.'))
        for name in sorted(files):
            if name.endswith('.py'):
                yield os.path.join(root, name)


def project_root(path):
    """Absolute directory that module names are taken relative to."""
    path = os.path.abspath(path)
    return path if os.path.isdir(path) else os.path.dirname(path)


def root_package(root):
    """Name of root if it is itself a package (has an __init__.py), else None."""
    return os.path.basename(root) if os.path.isfile(os.path.join(root, '__init__.py')) else None


def module_parts(module, package=None):
    """Lower-cased dotted parts of module, without the analyzed root package's own name."""
    parts = module.lower().split('.')
    return parts[1:] if package and parts[0] == package.lower() else parts


def module_name(file_path, root):
    """
    Dotted module name of file_path relative to root (pkg/mod.py -> pkg.mod,
    pkg/__init__.py -> pkg.__init__). When root is itself a package its name is
    prepended, so absolute imports of the analyzed package resolve.
    """
    rel = os.path.splitext(os.path.relpath(os.path.abspath(file_path), root))[0]
    name = rel.replace(os.sep, '.')
    package = root_package(root)
    return f"{package}.{name}" if package else name


def _is_type_checking(test):
    return (isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING' or
            isinstance(test, ast.Attribute) and test.attr == 'TYPE_CHECKING')


def iter_imports(tree, module):
    """
    Yield (candidates, lineno) for each imported name in tree. Candidates are
    absolute module names, most specific first: ``from pkg import mod`` may import
    the module pkg.mod or a name from pkg. Relative imports are resolved against
    module; imports under ``if TYPE_CHECKING:`` are skipped since they never run.
    """
    stack = [tree]
    while stack:
        node = stack.pop()
        if isinstance(node, ast.If) and _is_type_checking(node.test):
            stack.extend(node.orelse)
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield [alias.name], node.lineno
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ''
            if node.level:
                parts = module.split('.')
                if node.level >= len(parts):
                    continue  # reaches above the analyzed root: not resolvable here
                parts = parts[:-node.level]
                base = '.'.join(parts + [base] if base else parts)
            if not base:
                continue
            for alias in node.names:
                yield ([f"{base}.{alias.name}", base] if alias.name != '*' else [base]), node.lineno
        stack.extend(ast.iter_child_nodes(node))


class ModuleIndex:
    """Resolves imported names to the project modules they refer to."""

    def __init__(self, modules):
        exact, suffixes = {}, {}
        for module in modules:
            full = module[:-len('.__init__')] if module.endswith('.__init__') else module
            exact[module] = exact[full] = module
            # Proper suffixes let src/pkg/mod.py answer to pkg.mod. Single names only
            # stand for packages that do not shadow the stdlib (src/pkg/__init__.py
            # answers to pkg), so a project's utils/json.py leaves `import json` external.
            parts = full.split('.')
            last = len(parts) - 1 + (module.endswith('.__init__') and parts[-1] not in STDLIB_MODULES)
            for i in range(1, last):
                suffix = '.'.join(parts[i:])
                suffixes[suffix] = module if suffixes.get(suffix, module) == module else None
        self._exact = exact
        self._suffixes = suffixes

    def resolve(self, candidates):
        """The project module the first resolvable candidate names, or None if external."""
        for name in candidates:
            module = self._exact.get(name) or self._suffixes.get(name)
            if module:
                return module
        return None


def external_kind(name):
    """'stdlib' or 'third_party' for an import that is not a project module."""
    return 'stdlib' if name.split('.')[0] in STDLIB_MODULES else 'third_party'

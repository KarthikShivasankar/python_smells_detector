import argparse
import contextlib
import csv
import dataclasses
import json
import logging
import os
import sys
from importlib import metadata, resources

import yaml

from .architectural_smell_detector import ArchitecturalSmellDetector
from .code_smell_detector import CodeSmellDetector
from .config_handler import ConfigHandler
from .project import iter_python_files
from .structural_smell_detector import StructuralSmellDetector

DEFAULT_CONFIG_NAME = "code_quality_config.yaml"
SMELL_TYPES = ('code', 'architectural', 'structural')
TYPE_LABELS = ('Code', 'Architectural', 'Structural')
SEVERITIES = ('low', 'medium', 'high')
REPORT_SCHEMA_VERSION = 1

# Exit codes: 0 = analysis ran (and --fail-on, if given, was not triggered),
# 1 = --fail-on triggered, 2 = usage error (bad arguments, missing path or config)
EXIT_OK, EXIT_FINDINGS, EXIT_USAGE = 0, 1, 2

logger = logging.getLogger(__name__)


def _version():
    try:
        return metadata.version("code-quality-analyzer")
    except metadata.PackageNotFoundError:
        return "unknown"


def _configure_cli_logging(machine_readable=False, debug=False):
    """
    Log to stderr, and in text mode also to code_analysis.log. JSON mode writes no
    files and only logs warnings, so agents get clean stdout and quiet stderr.
    Only the CLI does this, not library imports.
    """
    handlers = [logging.StreamHandler()]
    if not machine_readable:
        handlers.append(logging.FileHandler('code_analysis.log'))
    level = logging.DEBUG if debug else logging.WARNING if machine_readable else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True,
    )


def create_parser():
    """Create and return the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="analyze_code_quality",
        description="Analyze code quality in Python projects.",
        epilog="Exit codes: 0 analysis completed; 1 --fail-on threshold reached; "
               "2 usage error (bad arguments, missing path or config file).")
    parser.add_argument("directory", help="Directory (or single .py file) to analyze")
    parser.add_argument("--config", default=DEFAULT_CONFIG_NAME,
                        help="Path to the configuration file. If omitted and no "
                             f"'{DEFAULT_CONFIG_NAME}' exists in the current directory, "
                             "the config bundled with the package is used.")
    parser.add_argument("--output",
                        help="Path to the output file (supports .txt and .csv extensions)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--type", choices=list(SMELL_TYPES),
                        help="Type of smell to analyze (default: all)")
    parser.add_argument("--ignore", nargs='*', default=[],
                        metavar="DIR",
                        help="Folder names to ignore during analysis (e.g. --ignore tests docs). "
                             "Hidden folders, __pycache__, venv, node_modules and "
                             "site-packages are always skipped.")
    parser.add_argument("--format", choices=['text', 'json'], default='text',
                        help="Report format. 'json' prints the report to stdout "
                             "(or to --output), writes no other files and sends "
                             "progress output to stderr.")
    parser.add_argument("--min-severity", choices=SEVERITIES, default='low',
                        help="Only report findings of at least this severity (default: low)")
    parser.add_argument("--fail-on", choices=SEVERITIES,
                        help="Exit with code 1 if any reported finding has at least this severity")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_version()}")
    return parser


def _severity_rank(severity):
    return SEVERITIES.index(severity) if severity in SEVERITIES else 1


def filter_by_severity(smells, min_severity='low'):
    """Smells (objects or finding dicts) whose severity is at least min_severity."""
    floor = _severity_rank(min_severity)
    return [s for s in smells
            if _severity_rank(s['severity'] if isinstance(s, dict) else s.severity) >= floor]


def run_detectors(directory, config_handler, types=SMELL_TYPES, ignore_dirs=(), errors=None):
    """
    Run the selected detectors over a directory (or a single file).

    Args:
        errors (list, optional): Receives a dict (file, detector, error) for every
            file that could not be analyzed.

    Returns:
        tuple: (code_smells, architectural_smells, structural_smells)
    """
    ignore_dirs = set(ignore_dirs or [])
    errors = [] if errors is None else errors
    code_smells, architectural_smells, structural_smells = [], [], []

    if 'code' in types:
        print("Analyzing Code Smells...")
        code_detector = CodeSmellDetector(config_handler.get_thresholds('code_smells'))
        code_smells = analyze_code_smells(directory, code_detector, ignore_dirs)
        errors.extend(code_detector.errors)

    if 'architectural' in types:
        print("Analyzing Architectural Smells...")
        arch_detector = ArchitecturalSmellDetector(
            config_handler.get_thresholds('architectural_smells'))
        architectural_smells = analyze_architectural_smells(directory, arch_detector, ignore_dirs)
        errors.extend(arch_detector.errors)

    if 'structural' in types:
        print("Analyzing Structural Smells...")
        struct_detector = StructuralSmellDetector(
            config_handler.get_thresholds('structural_smells'))
        structural_smells = analyze_structural_smells(directory, struct_detector, ignore_dirs)
        errors.extend(struct_detector.errors)

    return code_smells, architectural_smells, structural_smells


def _finding(label, smell):
    finding = {'type': label, **dataclasses.asdict(smell)}
    finding['severity'] = (finding['severity'] or 'medium').lower()
    return finding


def analyze(directory, types=SMELL_TYPES, config=DEFAULT_CONFIG_NAME, ignore=(), min_severity='low'):
    """
    Library entry point for scripts, agents and test harnesses. Returns the same
    JSON-serialisable report that ``--format json`` prints::

        {
          "schema_version": 1,
          "tool": {"name": "code-quality-analyzer", "version": "..."},
          "target": "<directory>",
          "summary": {"Code": n, "Architectural": n, "Structural": n, "total": n,
                      "by_severity": {"low": n, "medium": n, "high": n}},
          "findings": [{"type", "name", "description", "file_path",
                        "module_class", "line_number", "severity"}, ...],
          "errors": [{"file", "detector", "error"}, ...]
        }

    Findings are sorted (file, line, type, name, then the rest); ``severity`` is one of
    ``low``/``medium``/``high``. ``errors`` lists files that could not be analyzed
    (syntax or encoding errors), so an empty findings list can be trusted only
    when errors is empty too. Nothing is printed to stdout and no files are written;
    warnings are logged.

    Args:
        directory (str): Project directory, or a single .py file, to analyze.
        types (iterable): Any of ``'code'``, ``'architectural'``, ``'structural'``.
        config (str): Threshold YAML; falls back to the bundled config like the CLI.
        ignore (iterable): Directory names to skip.
        min_severity (str): Drop findings below this severity.

    Raises:
        ValueError: Unknown smell type or severity.
        FileNotFoundError: directory or config does not exist.
    """
    unknown = set(types) - set(SMELL_TYPES)
    if unknown:
        raise ValueError(f"Unknown smell types {sorted(unknown)}; expected {SMELL_TYPES}")
    if min_severity not in SEVERITIES:
        raise ValueError(f"Unknown severity {min_severity!r}; expected {SEVERITIES}")
    if not os.path.exists(directory):
        raise FileNotFoundError(f"No such file or directory: {directory}")
    if os.path.isfile(directory) and not directory.endswith('.py'):
        raise ValueError(f"Not a Python file: {directory}")
    config_handler = ConfigHandler(resolve_config_path(config))
    errors = []
    # Per-file progress lines are noise for machine consumers; warnings still go to stderr
    with open(os.devnull, 'w') as devnull, contextlib.redirect_stdout(devnull):
        groups = run_detectors(directory, config_handler, types, ignore, errors)

    findings = filter_by_severity(
        [_finding(label, smell) for label, smells in zip(TYPE_LABELS, groups) for smell in smells],
        min_severity)
    findings.sort(key=lambda f: (f['file_path'] or '', f['line_number'] or 0, f['type'], f['name'],
                                 f['module_class'] or '', f['description']))
    summary = {label: sum(f['type'] == label for f in findings) for label in TYPE_LABELS}
    summary['total'] = len(findings)
    summary['by_severity'] = {sev: sum(f['severity'] == sev for f in findings) for sev in SEVERITIES}
    return {
        'schema_version': REPORT_SCHEMA_VERSION,
        'tool': {'name': 'code-quality-analyzer', 'version': _version()},
        'target': directory,
        'summary': summary,
        'findings': findings,
        'errors': errors,
    }


def resolve_config_path(config_arg):
    """Resolve which configuration file to load.

    Precedence:
    1. An existing file at ``config_arg`` is always used.
    2. If ``config_arg`` is the default name and is absent from the current
       working directory, fall back to the config bundled inside the installed
       package so the tool works out-of-the-box after ``pip install``.
    3. Otherwise return ``config_arg`` unchanged (a missing explicit path will
       surface as a clear FileNotFoundError from ConfigHandler).

    Args:
        config_arg (str): The config path supplied on the command line.

    Returns:
        str: The path that should be handed to ConfigHandler.
    """
    if os.path.isfile(config_arg):
        return config_arg

    if config_arg == DEFAULT_CONFIG_NAME:
        try:
            packaged = resources.files("code_quality_analyzer").joinpath(DEFAULT_CONFIG_NAME)
            if packaged.is_file():
                logger.info(
                    f"No '{DEFAULT_CONFIG_NAME}' found in the current directory; "
                    "using the configuration bundled with the package.")
                return str(packaged)
        except (FileNotFoundError, ModuleNotFoundError):
            pass

    return config_arg


def analyze_code_smells(directory_path, detector, ignore_dirs=None):
    """
    Analyze a directory (or a single file) for code smells using the provided detector.
    Files that fail to parse are skipped and recorded in ``detector.errors``.

    Args:
        directory_path (str): The path to the directory to analyze
        detector (CodeSmellDetector): The detector instance to use
        ignore_dirs (list): Directory names to skip during analysis

    Returns:
        list: A list of detected code smells
    """
    files_analyzed = 0

    print(f"\nStarting code smell analysis for directory: {directory_path}")

    for file_path in iter_python_files(directory_path, ignore_dirs):
        try:
            detector.detect_smells(file_path)
            files_analyzed += 1
            print(f"Successfully analyzed: {file_path}")
        except Exception as e:
            message = str(e).split('\n')[0]
            detector.errors.append({'file': file_path, 'detector': 'CodeSmellDetector',
                                    'error': message})
            logger.warning(f"Skipping {file_path}: {message}")

    # Run smells that need cross-file context
    try:
        detector.detect_cross_file_smells()
    except Exception as e:
        logger.error(f"Error in detect_cross_file_smells: {str(e)}", exc_info=True)
        detector.errors.append({'file': directory_path, 'detector': 'CodeSmellDetector',
                                'error': f"cross-file analysis failed: {e}"})

    print(f"""
Code Smell Analysis Summary:
--------------------------
Files analyzed: {files_analyzed}
Files with errors: {len(detector.errors)}
    """)

    return detector.code_smells


def _run_project_detector(directory_path, detector, ignore_dirs):
    """Run a whole-project detector; a failure of the run is recorded in detector.errors."""
    try:
        detector.detect_smells(directory_path, ignore_dirs=ignore_dirs)
    except Exception as e:
        logger.error(f"{type(detector).__name__} failed: {e}", exc_info=True)
        detector.errors.append({'file': getattr(e, 'file_path', None) or directory_path,
                                'detector': type(detector).__name__,
                                'error': str(e).split('\n')[0]})


def analyze_architectural_smells(directory_path, detector, ignore_dirs=None):
    """
    Analyze a directory for architectural smells using the provided detector.

    Args:
        directory_path (str): The path to the directory to analyze
        detector (ArchitecturalSmellDetector): The detector instance to use
        ignore_dirs (list): Directory names to skip during analysis

    Returns:
        list: A list of detected architectural smells
    """
    print(f"\nStarting architectural smell analysis for directory: {directory_path}")
    _run_project_detector(directory_path, detector, ignore_dirs)
    print(f"\nArchitectural smell analysis complete. Found {len(detector.architectural_smells)} smells.")
    return detector.architectural_smells


def analyze_structural_smells(directory_path, detector, ignore_dirs=None):
    """
    Analyze a directory for structural smells using the provided detector.

    Args:
        directory_path (str): The path to the directory to analyze
        detector (StructuralSmellDetector): The detector instance to use
        ignore_dirs (list): Directory names to skip during analysis

    Returns:
        list: A list of detected structural smells
    """
    print(f"\nStarting structural smell analysis for directory: {directory_path}")
    _run_project_detector(directory_path, detector, ignore_dirs)
    print(f"Structural smell analysis complete. Found {len(detector.structural_smells)} smells.")
    return detector.structural_smells


def analyze_project(argv=None):
    """
    CLI entry point: analyze a Python project for code, architectural, and structural smells.

    Returns:
        int: The process exit code (see EXIT_* and ``--help``).
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    machine_readable = args.format == 'json'
    _configure_cli_logging(machine_readable, args.debug)

    if not os.path.exists(args.directory):
        parser.error(f"no such file or directory: {args.directory}")
    if os.path.isfile(args.directory) and not args.directory.endswith('.py'):
        parser.error(f"not a Python file: {args.directory}")

    ignore_dirs = set(args.ignore or [])
    if ignore_dirs:
        logger.info(f"Ignoring directories: {ignore_dirs}")
    types = (args.type,) if args.type else SMELL_TYPES

    try:
        if machine_readable:
            report = analyze(args.directory, types, args.config, ignore_dirs, args.min_severity)
            findings = report['findings']
            text = json.dumps(report, indent=2)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(text + "\n")
            else:
                print(text)
        else:
            config_path = resolve_config_path(args.config)
            logger.info(f"Loading configuration from: {config_path}")
            config_handler = ConfigHandler(config_path)
            groups = [filter_by_severity(smells, args.min_severity)
                      for smells in run_detectors(args.directory, config_handler, types, ignore_dirs)]
            findings = [s for smells in groups for s in smells]
            base_name = os.path.splitext(args.output)[0] if args.output else "code_quality_report"
            generate_report(*groups, f"{base_name}.txt", f"{base_name}.csv")
    except (FileNotFoundError, yaml.YAMLError) as e:
        parser.error(str(e))

    if args.fail_on and filter_by_severity(findings, args.fail_on):
        return EXIT_FINDINGS
    return EXIT_OK


def _report_lines(smells):
    lines = []
    for smell in smells:
        lines.append(f"- {smell.name}: {smell.description}")
        if smell.line_number:
            lines.append(f"  Line: {smell.line_number}")
        lines.append(f"  File: {smell.file_path}")
        lines.append(f"  Severity: {smell.severity}\n")
    return "\n".join(lines) + "\n"


def generate_report(code_smells, architectural_smells, structural_smells,
                    output_txt=None, output_csv=None):
    """
    Generate a report of all detected smells in both text and CSV formats.

    Args:
        code_smells (list): A list of detected CodeSmell objects
        architectural_smells (list): A list of detected ArchitecturalSmell objects
        structural_smells (list): A list of detected StructuralSmell objects
        output_txt (str, optional): The path to the output text file
        output_csv (str, optional): The path to the output CSV file
    """
    report = "Code Quality Analysis Report\n"
    report += "============================\n\n"

    for title, smells in (("Structural", structural_smells), ("Code", code_smells),
                          ("Architectural", architectural_smells)):
        if smells:
            heading = f"{title} Smells:"
            report += f"{heading}\n{'-' * len(heading)}\n" + _report_lines(smells) + "\n"
        else:
            report += f"No {title.lower()} smells detected.\n\n"

    report += "Summary:\n"
    report += "--------\n"
    report += f"Total Structural Smells: {len(structural_smells)}\n"
    report += f"Total Code Smells: {len(code_smells)}\n"
    report += f"Total Architectural Smells: {len(architectural_smells)}\n"

    if output_txt:
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Text report generated and saved to {output_txt}")

        if output_csv:
            generate_csv_report(code_smells, architectural_smells,
                                structural_smells, output_csv)
    else:
        print(report)


def generate_csv_report(code_smells, architectural_smells, structural_smells, csv_file):
    """
    Generate a CSV report of all detected smells.

    Args:
        code_smells (list): A list of detected CodeSmell objects
        architectural_smells (list): A list of detected ArchitecturalSmell objects
        structural_smells (list): A list of detected StructuralSmell objects
        csv_file (str): The path to the output CSV file
    """
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Type',
            'Name',
            'Description',
            'File',
            'Module/Class',
            'Line Number',
            'Severity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for label, smells in (('Structural', structural_smells), ('Code', code_smells),
                              ('Architectural', architectural_smells)):
            for smell in smells:
                writer.writerow({
                    'Type': label,
                    'Name': smell.name,
                    'Description': smell.description,
                    'File': smell.file_path,
                    'Module/Class': smell.module_class,
                    'Line Number': smell.line_number,
                    'Severity': smell.severity
                })

    logger.info(f"CSV report generated and saved to {csv_file}")


if __name__ == "__main__":
    sys.exit(analyze_project())

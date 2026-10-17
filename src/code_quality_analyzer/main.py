import argparse
import contextlib
import csv
import dataclasses
import json
import logging
import os
import sys
from importlib import resources

from .architectural_smell_detector import ArchitecturalSmellDetector
from .code_smell_detector import CodeSmellDetector
from .config_handler import ConfigHandler
from .exceptions import CodeAnalysisError
from .structural_smell_detector import StructuralSmellDetector

DEFAULT_CONFIG_NAME = "code_quality_config.yaml"
SMELL_TYPES = ('code', 'architectural', 'structural')

logger = logging.getLogger(__name__)


def _configure_cli_logging():
    """Log to code_analysis.log and stderr. Only the CLI does this, not library imports."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('code_analysis.log'),
            logging.StreamHandler()
        ]
    )


def create_parser():
    """Create and return the argument parser for the CLI."""
    parser = argparse.ArgumentParser(description="Analyze code quality in Python projects.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default=DEFAULT_CONFIG_NAME,
                        help="Path to the configuration file. If omitted and no "
                             f"'{DEFAULT_CONFIG_NAME}' exists in the current directory, "
                             "the config bundled with the package is used.")
    parser.add_argument("--output",
                        help="Path to the output file (supports .txt and .csv extensions)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--type", choices=['code', 'architectural', 'structural'],
                        help="Type of smell to analyze (default: all)")
    parser.add_argument("--ignore", nargs='*', default=[],
                        metavar="DIR",
                        help="Folder names to ignore during analysis (e.g. --ignore tests docs)")
    parser.add_argument("--format", choices=['text', 'json'], default='text',
                        help="Report format. 'json' prints {findings, summary} to stdout "
                             "(or to --output) and sends all progress output to stderr.")
    return parser


def run_detectors(directory, config_handler, types=SMELL_TYPES, ignore_dirs=()):
    """
    Run the selected detectors over a directory.

    Returns:
        tuple: (code_smells, architectural_smells, structural_smells)
    """
    ignore_dirs = set(ignore_dirs or [])
    code_smells, architectural_smells, structural_smells = [], [], []

    if 'code' in types:
        print("Analyzing Code Smells...")
        code_detector = CodeSmellDetector(config_handler.get_thresholds('code_smells'))
        code_smells = analyze_code_smells(directory, code_detector, ignore_dirs)

    if 'architectural' in types:
        print("Analyzing Architectural Smells...")
        arch_detector = ArchitecturalSmellDetector(
            config_handler.get_thresholds('architectural_smells'))
        architectural_smells = analyze_architectural_smells(directory, arch_detector, ignore_dirs)

    if 'structural' in types:
        print("Analyzing Structural Smells...")
        struct_detector = StructuralSmellDetector(
            config_handler.get_thresholds('structural_smells'))
        structural_smells = analyze_structural_smells(directory, struct_detector, ignore_dirs)

    return code_smells, architectural_smells, structural_smells


def analyze(directory, types=SMELL_TYPES, config=DEFAULT_CONFIG_NAME, ignore=()):
    """
    Library entry point for scripts, agents and test harnesses.

    Runs the selected detectors and returns every finding as a JSON-serialisable dict
    with the keys ``type`` (``Code``/``Architectural``/``Structural``), ``name``,
    ``description``, ``file_path``, ``module_class``, ``line_number`` and ``severity``.
    Progress output goes to stderr; no report files are written.

    Args:
        directory (str): Project directory to analyze.
        types (iterable): Any of ``'code'``, ``'architectural'``, ``'structural'``.
        config (str): Threshold YAML; falls back to the bundled config like the CLI.
        ignore (iterable): Directory names to skip.
    """
    unknown = set(types) - set(SMELL_TYPES)
    if unknown:
        raise ValueError(f"Unknown smell types {sorted(unknown)}; expected {SMELL_TYPES}")
    config_handler = ConfigHandler(resolve_config_path(config))
    with contextlib.redirect_stdout(sys.stderr):
        groups = run_detectors(directory, config_handler, types, ignore)
    return [{'type': label, **dataclasses.asdict(smell)}
            for label, smells in zip(('Code', 'Architectural', 'Structural'), groups)
            for smell in smells]


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
    Analyze a directory for code smells using the provided detector.

    Args:
        directory_path (str): The path to the directory to analyze
        detector (CodeSmellDetector): The detector instance to use
        ignore_dirs (list): Directory names to skip during analysis

    Returns:
        list: A list of detected code smells
    """
    ignore_dirs = set(ignore_dirs or [])
    errors = []
    files_analyzed = 0
    files_with_errors = 0

    print(f"\nStarting code smell analysis for directory: {directory_path}")

    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    detector.detect_smells(file_path)
                    files_analyzed += 1
                    print(f"Successfully analyzed: {file_path}")
                except CodeAnalysisError as e:
                    files_with_errors += 1
                    error_info = {
                        'file': file_path,
                        'error_type': type(e).__name__,
                        'error_msg': str(e),
                        'detector': 'CodeSmellDetector',
                        'function': getattr(e, 'function_name', 'unknown')
                    }
                    errors.append(error_info)
                    logger.error(f"Error analyzing {file_path}: {str(e)}")
                    continue
                except Exception as e:
                    files_with_errors += 1
                    error_info = {
                        'file': file_path,
                        'error_type': type(e).__name__,
                        'error_msg': str(e),
                        'detector': 'CodeSmellDetector',
                        'function': 'unknown'
                    }
                    errors.append(error_info)
                    logger.error(f"Unexpected error analyzing {file_path}: {str(e)}")
                    continue

    # Run smells that need cross-file context
    try:
        detector.detect_cross_file_smells()
    except Exception as e:
        logger.error(f"Error in detect_cross_file_smells: {str(e)}", exc_info=True)

    print(f"""
Code Smell Analysis Summary:
--------------------------
Files analyzed: {files_analyzed}
Files with errors: {files_with_errors}
Success rate: {((files_analyzed - files_with_errors) / max(files_analyzed, 1) * 100):.1f}%
    """)

    if errors:
        logger.warning("Errors encountered during code smell analysis:")
        for error in errors:
            logger.warning(f"""
File: {error['file']}
Error Type: {error['error_type']}
Error Message: {error['error_msg']}
Detector: {error['detector']}
Function: {error['function']}
            """)

    return detector.code_smells


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
    errors = []
    try:
        print(f"\nStarting architectural smell analysis for directory: {directory_path}")

        detector.detect_smells(directory_path, ignore_dirs=ignore_dirs)

        smell_count = len(detector.architectural_smells)
        print(f"\nArchitectural smell analysis complete. Found {smell_count} smells.")

        if smell_count == 0:
            print("No architectural smells were detected. Verify thresholds in config file.")

    except CodeAnalysisError as e:
        error_info = {
            'file': e.file_path,
            'error_type': type(e).__name__,
            'error_msg': str(e),
            'detector': 'ArchitecturalSmellDetector',
            'function': getattr(e, 'function_name', 'unknown')
        }
        errors.append(error_info)
        logger.error(f"Error in architectural analysis: {str(e)}", exc_info=True)
    except Exception as e:
        error_info = {
            'file': directory_path,
            'error_type': type(e).__name__,
            'error_msg': str(e),
            'detector': 'ArchitecturalSmellDetector',
            'function': 'unknown'
        }
        errors.append(error_info)
        logger.error(f"Unexpected error in architectural analysis: {str(e)}", exc_info=True)

    if errors:
        logger.warning("Errors encountered during architectural analysis:")
        for error in errors:
            logger.warning(f"""
File: {error['file']}
Error Type: {error['error_type']}
Error Message: {error['error_msg']}
Detector: {error['detector']}
Function: {error['function']}
            """)

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
    errors = []

    print(f"\nStarting structural smell analysis for directory: {directory_path}")

    try:
        detector.detect_smells(directory_path, ignore_dirs=ignore_dirs)
        print(f"Successfully analyzed: {directory_path}")

    except CodeAnalysisError as e:
        error_info = {
            'file': e.file_path,
            'error_type': type(e).__name__,
            'error_msg': str(e),
            'detector': 'StructuralSmellDetector',
            'function': getattr(e, 'function_name', 'unknown')
        }
        errors.append(error_info)
        logger.error(f"Error in structural analysis: {str(e)}", exc_info=True)
    except Exception as e:
        error_info = {
            'file': directory_path,
            'error_type': type(e).__name__,
            'error_msg': str(e),
            'detector': 'StructuralSmellDetector',
            'function': 'unknown'
        }
        errors.append(error_info)
        logger.error(f"Unexpected error in structural analysis: {str(e)}", exc_info=True)

    logger.info(
        f"Structural smell analysis complete. Found {len(detector.structural_smells)} smells.")

    return detector.structural_smells


def analyze_project():
    """
    CLI entry point: analyze a Python project for code, architectural, and structural smells.
    """
    parser = create_parser()
    args = parser.parse_args()
    _configure_cli_logging()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    ignore_dirs = set(args.ignore or [])
    if ignore_dirs:
        logger.info(f"Ignoring directories: {ignore_dirs}")

    types = (args.type,) if args.type else SMELL_TYPES

    if args.format == 'json':
        findings = analyze(args.directory, types, args.config, ignore_dirs)
        summary = {label: sum(f['type'] == label for f in findings)
                   for label in ('Code', 'Architectural', 'Structural')}
        report = json.dumps({'findings': findings, 'summary': summary}, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report + "\n")
        else:
            print(report)
        return

    if args.output:
        base_name = os.path.splitext(args.output)[0]
        output_txt = f"{base_name}.txt"
        output_csv = f"{base_name}.csv"
    else:
        output_txt = "code_quality_report.txt"
        output_csv = "code_quality_report.csv"

    try:
        config_path = resolve_config_path(args.config)
        logger.info(f"Loading configuration from: {config_path}")
        config_handler = ConfigHandler(config_path)

        code_smells, architectural_smells, structural_smells = run_detectors(
            args.directory, config_handler, types, ignore_dirs)

        generate_report(code_smells, architectural_smells, structural_smells,
                        output_txt, output_csv)

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise


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

    if structural_smells:
        report += "Structural Smells:\n"
        report += "-------------------\n"
        for smell in structural_smells:
            report += f"- {smell.name}: {smell.description}\n"
            if smell.line_number:
                report += f"  Line: {smell.line_number}\n"
            report += f"  File: {smell.file_path}\n"
            report += f"  Severity: {smell.severity}\n\n"
    else:
        report += "No structural smells detected.\n\n"

    if code_smells:
        report += "Code Smells:\n"
        report += "------------\n"
        for smell in code_smells:
            report += f"- {smell.name}: {smell.description}\n"
    else:
        report += "No code smells detected.\n\n"

    if architectural_smells:
        report += "\nArchitectural Smells:\n"
        report += "---------------------\n"
        for smell in architectural_smells:
            report += f"- {smell.name}: {smell.description}\n"
    else:
        report += "No architectural smells detected.\n\n"

    report += "\nSummary:\n"
    report += "--------\n"
    report += f"Total Structural Smells: {len(structural_smells)}\n"
    report += f"Total Code Smells: {len(code_smells)}\n"
    report += f"Total Architectural Smells: {len(architectural_smells)}\n"

    if output_txt:
        with open(output_txt, 'w') as f:
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
    with open(csv_file, 'w', newline='') as csvfile:
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

        for smell in structural_smells:
            writer.writerow({
                'Type': 'Structural',
                'Name': smell.name,
                'Description': smell.description,
                'File': smell.file_path,
                'Module/Class': smell.module_class,
                'Line Number': smell.line_number,
                'Severity': smell.severity
            })

        for smell in code_smells:
            writer.writerow({
                'Type': 'Code',
                'Name': smell.name,
                'Description': smell.description,
                'File': smell.file_path,
                'Module/Class': smell.module_class,
                'Line Number': smell.line_number,
                'Severity': smell.severity
            })

        for smell in architectural_smells:
            writer.writerow({
                'Type': 'Architectural',
                'Name': smell.name,
                'Description': smell.description,
                'File': smell.file_path,
                'Module/Class': smell.module_class,
                'Line Number': smell.line_number,
                'Severity': smell.severity
            })

    logger.info(f"CSV report generated and saved to {csv_file}")


if __name__ == "__main__":
    analyze_project()

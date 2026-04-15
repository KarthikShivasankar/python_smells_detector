import os
import argparse
import csv
from .code_smell_detector import CodeSmellDetector
from .architectural_smell_detector import ArchitecturalSmellDetector
from .structural_smell_detector import StructuralSmellDetector
from .config_handler import ConfigHandler

def analyze_project():
    """
    Analyze a Python project for code, architectural, and structural smells.

    This function orchestrates the analysis of a Python project by initializing
    and running detectors for different types of code smells.

    Args:
        directory_path (str): The path to the directory containing the Python project to analyze.
        config_file (str, optional): The path to the configuration file. Defaults to "code_quality_config.yaml".
        output_file (str, optional): The path to the output file for the report. If None, prints to console.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="Analyze code quality in Python projects.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default=os.path.expanduser("~/.code_quality_config.yaml"), help="Path to the configuration file")
    parser.add_argument("--output", help="Path to the output file for the report")
    args = parser.parse_args()

    if not args.config:
        args.config = "code_quality_config.yaml"
    
    config_handler = ConfigHandler(args.config)

    print("Analyzing Code Smells...")
    code_detector = CodeSmellDetector(config_handler.get_thresholds('code_smells'))
    code_smells = analyze_code_smells(args.directory, code_detector)

    print("Analyzing Architectural Smells...")
    arch_detector = ArchitecturalSmellDetector(config_handler.get_thresholds('architectural_smells'))
    architectural_smells = analyze_architectural_smells(args.directory, arch_detector)

    print("Analyzing Structural Smells...")
    struct_detector = StructuralSmellDetector(config_handler.get_thresholds('structural_smells'))
    structural_smells = analyze_structural_smells(args.directory, struct_detector)

    generate_report(code_smells, architectural_smells, structural_smells, args.output)

def analyze_code_smells(directory_path, detector):
    """
    Analyze a directory for code smells using the provided detector.

    This function walks through the directory and its subdirectories,
    analyzing each Python file for code smells.

    Args:
        directory_path (str): The path to the directory to analyze.
        detector (CodeSmellDetector): An instance of the CodeSmellDetector class.

    Returns:
        list: A list of detected code smells.
    """
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                detector.detect_smells(file_path)
    return detector.code_smells

def analyze_architectural_smells(directory_path, detector):
    """
    Analyze a directory for architectural smells using the provided detector.

    This function analyzes the entire project directory for architectural smells.

    Args:
        directory_path (str): The path to the directory to analyze.
        detector (ArchitecturalSmellDetector): An instance of the ArchitecturalSmellDetector class.

    Returns:
        list: A list of detected architectural smells.
    """
    detector.detect_smells(directory_path)
    return detector.architectural_smells

def analyze_structural_smells(directory_path, detector):
    """
    Analyze a directory for structural smells using the provided detector.

    This function analyzes the entire project directory for structural smells.

    Args:
        directory_path (str): The path to the directory to analyze.
        detector (StructuralSmellDetector): An instance of the StructuralSmellDetector class.

    Returns:
        list: A list of detected structural smells.
    """
    detector.detect_smells(directory_path)
    return detector.structural_smells

def generate_report(code_smells, architectural_smells, structural_smells, output_file=None):
    """
    Generate a report of all detected smells in both text and CSV formats.

    This function compiles the detected smells into a formatted report and either
    prints it to the console or writes it to a file. It also generates a CSV file
    with detailed metadata.

    Args:
        code_smells (list): A list of detected CodeSmell objects.
        architectural_smells (list): A list of detected ArchitecturalSmell objects.
        structural_smells (list): A list of detected StructuralSmell objects.
        output_file (str, optional): The path to the output file. If None, prints to console.

    Returns:
        None
    """
    # Generate text report
    report = "Code Quality Analysis Report\n"
    report += "============================\n\n"

    report += "Code Smells:\n"
    report += "------------\n"
    for smell in code_smells:
        report += f"- {smell.name}: {smell.description}\n"
    
    report += "\nArchitectural Smells:\n"
    report += "---------------------\n"
    for smell in architectural_smells:
        report += f"- {smell.name}: {smell.description}\n"

    report += "\nStructural Smells:\n"
    report += "-------------------\n"
    for smell in structural_smells:
        report += f"- {smell.name}: {smell.description}\n"

    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Text report generated and saved to {output_file}")
    else:
        print(report)

    # Generate CSV report
    csv_file = output_file.rsplit('.', 1)[0] + '.csv' if output_file else 'code_quality_report.csv'
    
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['Smell Type', 'Smell Name', 'Description', 'File Path', 'Module/Class', 'Line Number', 'Severity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        def write_smells(smells, smell_type):
            for smell in smells:
                writer.writerow({
                    'Smell Type': smell_type,
                    'Smell Name': smell.name,
                    'Description': smell.description,
                    'File Path': smell.file_path,
                    'Module/Class': smell.module_class,
                    'Line Number': smell.line_number,
                    'Severity': smell.severity
                })

        write_smells(code_smells, 'Code Smell')
        write_smells(architectural_smells, 'Architectural Smell')
        write_smells(structural_smells, 'Structural Smell')

    print(f"CSV report generated and saved to {csv_file}")

if __name__ == "__main__":
    analyze_project()


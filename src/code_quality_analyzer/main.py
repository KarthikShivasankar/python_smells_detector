import os
import argparse
import csv
import logging
from .code_smell_detector import CodeSmellDetector
from .architectural_smell_detector import ArchitecturalSmellDetector
from .structural_smell_detector import StructuralSmellDetector
from .config_handler import ConfigHandler
from .exceptions import CodeAnalysisError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def analyze_code_smells(directory_path, detector):
    """
    Analyze a directory for code smells using the provided detector.

    Args:
        directory_path (str): The path to the directory to analyze
        detector (CodeSmellDetector): The detector instance to use

    Returns:
        list: A list of detected code smells
    """
    errors = []
    files_analyzed = 0
    files_with_errors = 0
    
    print(f"\nStarting code smell analysis for directory: {directory_path}")
    
    for root, _, files in os.walk(directory_path):
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

def analyze_architectural_smells(directory_path, detector):
    """
    Analyze a directory for architectural smells using the provided detector.

    Args:
        directory_path (str): The path to the directory to analyze
        detector (ArchitecturalSmellDetector): The detector instance to use

    Returns:
        list: A list of detected architectural smells
    """
    errors = []
    try:
        print(f"\nStarting architectural smell analysis for directory: {directory_path}")
        
        detector.detect_smells(directory_path)
        
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

def analyze_project(debug=False, smell_type=None):
    """
    Analyze a Python project for code, architectural, and structural smells.

    Args:
        debug (bool): If True, enables detailed debug logging
        smell_type (str): Type of smell to analyze ('code', 'architectural', 'structural', or None for all)
    """
    parser = argparse.ArgumentParser(description="Analyze code quality in Python projects.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default="code_quality_config.yaml", help="Path to the configuration file")
    parser.add_argument("--output", help="Path to the output file (supports .txt and .csv extensions)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--type", choices=['code', 'architectural', 'structural'], 
                       help="Type of smell to analyze (default: all)")
    args = parser.parse_args()

    if args.debug or debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    smell_type = args.type or smell_type
    
    # Determine output filenames based on the --output argument
    if args.output:
        base_name = os.path.splitext(args.output)[0]
        output_txt = f"{base_name}.txt"
        output_csv = f"{base_name}.csv"
    else:
        output_txt = "code_quality_report.txt"
        output_csv = "code_quality_report.csv"

    try:
        logger.info(f"Loading configuration from: {args.config}")
        config_handler = ConfigHandler(args.config)
        
        code_smells = []
        architectural_smells = []
        structural_smells = []

        if smell_type in [None, 'code']:
            print("Analyzing Code Smells...")
            code_detector = CodeSmellDetector(config_handler.get_thresholds('code_smells'))
            code_smells = analyze_code_smells(args.directory, code_detector)

        if smell_type in [None, 'architectural']:
            print("Analyzing Architectural Smells...")
            arch_detector = ArchitecturalSmellDetector(config_handler.get_thresholds('architectural_smells'))
            architectural_smells = analyze_architectural_smells(args.directory, arch_detector)

        if smell_type in [None, 'structural']:
            print("Analyzing Structural Smells...")
            struct_detector = StructuralSmellDetector(config_handler.get_thresholds('structural_smells'))
            structural_smells = analyze_structural_smells(args.directory, struct_detector)

        generate_report(code_smells, architectural_smells, structural_smells, 
                       output_txt, output_csv)

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise

def analyze_structural_smells(directory_path, detector):
    """
    Analyze a directory for structural smells using the provided detector.

    Args:
        directory_path (str): The path to the directory to analyze
        detector (StructuralSmellDetector): The detector instance to use

    Returns:
        list: A list of detected structural smells
    """
    errors = []
    
    print(f"\nStarting structural smell analysis for directory: {directory_path}")
    
    try:
        detector.detect_smells(directory_path)
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

    # Log the summary instead of printing it
    logger.info(f"Structural smell analysis complete. Found {len(detector.structural_smells)} smells.")

    return detector.structural_smells

def analyze_structural_smells_only(directory_path, config_path="code_quality_config.yaml", output=None):
    """
    Analyze only structural smells in a Python project.

    Args:
        directory_path (str): The path to the directory to analyze
        config_path (str): Path to the configuration file
    """
    try:
        config_handler = ConfigHandler(config_path)
        struct_detector = StructuralSmellDetector(config_handler.get_thresholds('structural_smells'))
        
        print("Analyzing Structural Smells...")
        structural_smells = analyze_structural_smells(directory_path, struct_detector)
        
        # Use provided output filename or default
        if output:
            base_name = os.path.splitext(output)[0]
            txt_file = f"{base_name}.txt"
            csv_file = f"{base_name}.csv"
        else:
            txt_file = "structural_smells_report.txt"
            csv_file = "structural_smells_report.csv"
            
        generate_report([], [], structural_smells, txt_file, csv_file)
        return structural_smells
    
    except Exception as e:
        logger.error(f"Error analyzing structural smells: {str(e)}", exc_info=True)
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
    # Generate text report
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

    # Print summary
    report += "\nSummary:\n"
    report += "--------\n"
    report += f"Total Structural Smells: {len(structural_smells)}\n"
    report += f"Total Code Smells: {len(code_smells)}\n"
    report += f"Total Architectural Smells: {len(architectural_smells)}\n"

    # Write or print the report
    if output_txt:
        with open(output_txt, 'w') as f:
            f.write(report)
        print(f"Text report generated and saved to {output_txt}")
        
        # Generate CSV report with the specified filename
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
        fieldnames = ['Type', 'Name', 'Description', 'File', 'Module/Class', 'Line Number', 'Severity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Write structural smells
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

        # Write code smells
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

        # Write architectural smells
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

def analyze_code_smells_only(directory_path, config_path="code_quality_config.yaml"):
    """
    Analyze only code smells in a Python project.
    
    Args:
        directory_path (str): The path to the directory to analyze
        config_path (str): Path to the configuration file
    """
    try:
        config_handler = ConfigHandler(config_path)
        code_detector = CodeSmellDetector(config_handler.get_thresholds('code_smells'))
        
        print("Analyzing Code Smells...")
        code_smells = analyze_code_smells(directory_path, code_detector)
        
        generate_report(code_smells, [], [], "code_smells_report.txt")
        return code_smells
        
    except Exception as e:
        logger.error(f"Error analyzing code smells: {str(e)}", exc_info=True)
        raise

def analyze_architectural_smells_only(directory_path, config_path="code_quality_config.yaml"):
    """
    Analyze only architectural smells in a Python project.
    
    Args:
        directory_path (str): The path to the directory to analyze
        config_path (str): Path to the configuration file
    """
    try:
        config_handler = ConfigHandler(config_path)
        arch_detector = ArchitecturalSmellDetector(config_handler.get_thresholds('architectural_smells'))
        
        print("Analyzing Architectural Smells...")
        architectural_smells = analyze_architectural_smells(directory_path, arch_detector)
        
        generate_report([], architectural_smells, [], "architectural_smells_report.txt")
        return architectural_smells
        
    except Exception as e:
        logger.error(f"Error analyzing architectural smells: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze code quality in Python projects.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default="code_quality_config.yaml", help="Path to the configuration file")
    parser.add_argument("--output", help="Path to the output file (supports .txt and .csv extensions)")
    parser.add_argument("--type", choices=['code', 'architectural', 'structural'], 
                       help="Type of smell to analyze (default: all)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Determine output filenames based on the --output argument
    if args.output:
        base_name = os.path.splitext(args.output)[0]
        output_txt = f"{base_name}.txt"
        output_csv = f"{base_name}.csv"
    else:
        output_txt = "code_quality_report.txt"
        output_csv = "code_quality_report.csv"
    
    if args.type == 'structural':
        analyze_structural_smells_only(args.directory, args.config, args.output)
    elif args.type == 'code':
        analyze_code_smells_only(args.directory, args.config, args.output)
    elif args.type == 'architectural':
        analyze_architectural_smells_only(args.directory, args.config, args.output)
    else:
        analyze_project(args.debug, args.type)


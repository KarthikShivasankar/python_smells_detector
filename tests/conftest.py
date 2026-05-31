import os
import sys

import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# ---------------------------------------------------------------------------
# Inline threshold fixtures — no dependency on config file location
# ---------------------------------------------------------------------------

CODE_SMELL_THRESHOLDS = {
    'LONG_METHOD_LINES': 45,
    'LARGE_CLASS_METHODS': 15,
    'PRIMITIVE_OBSESSION_COUNT': 4,
    'LONG_PARAMETER_LIST': 5,
    'DATA_CLUMPS_THRESHOLD': 6,
    'COMPLEX_CONDITIONAL': 3,
    'TEMPORARY_FIELD_THRESHOLD': 3,
    'ALTERNATIVE_CLASSES_THRESHOLD': 3,
    'DIVERGENT_CHANGE_PREFIXES': 4,
    'DIVERGENT_CHANGE_METHODS': 5,
    'SHOTGUN_SURGERY_CALLS': 5,
    'SHOTGUN_SURGERY_CONTEXTS': 3,
    'EXCESSIVE_COMMENTS_RATIO': 0.3,
    'LARGE_COMMENT_BLOCKS': 5,
    'DUPLICATE_CODE_THRESHOLD': 3,   # lowered so tests don't need 15 identical functions
    'DUPLICATE_CODE_MIN_LINES': 5,
    'SPECULATIVE_GENERALITY_THRESHOLD': 4,
    'UNUSED_PARAMETERS_THRESHOLD': 6,
    'FEATURE_ENVY_CALLS': 3,
    'INAPPROPRIATE_INTIMACY_SHARED': 3,
    'MESSAGE_CHAIN_LENGTH': 3,
    'MIDDLE_MAN_RATIO': 0.5,
    'DEAD_CODE_THRESHOLD': 3,
    'LAZY_CLASS_METHODS': 4,
    'LAZY_CLASS_LINES': 20,
    'DATA_CLASS_METHODS': 4,
}

STRUCTURAL_THRESHOLDS = {
    'NOM_THRESHOLD': 10,
    'WMPC1_THRESHOLD': 20,
    'WMPC2_THRESHOLD': 20,
    'SIZE2_THRESHOLD': 15,
    'WAC_THRESHOLD': 10,
    'LCOM_THRESHOLD': 10,
    'RFC_THRESHOLD': 20,
    'NOCC_THRESHOLD': 10,
    'DIT_THRESHOLD': 3,
    'LOC_THRESHOLD': 150,
    'MPC_THRESHOLD': 25,
    'CBO_THRESHOLD': 5,
    'NOC_THRESHOLD': 7,
    'CYCLOMATIC_COMPLEXITY_THRESHOLD': 10,
    'MAX_FANOUT': 15,
    'MAX_FANIN': 15,
    'MAX_FILE_LENGTH': 250,
    'MAX_BRANCHES': 10,
    'MAX_NESTING_DEPTH': 4,
}

ARCHITECTURAL_THRESHOLDS = {
    'GOD_OBJECT_FUNCTIONS': 20,
    'UNSTABLE_DEPENDENCY_THRESHOLD': 0.8,
    'HUB_LIKE_DEPENDENCY_RATIO': 0.3,
    'REDUNDANT_ABSTRACTION_SIMILARITY': 0.7,
    'IMPROPER_API_USAGE_RATIO': 0.7,
    'CYCLIC_DEPENDENCY_MAX_LENGTH': 3,
}


@pytest.fixture
def code_smell_detector():
    from code_quality_analyzer.code_smell_detector import CodeSmellDetector
    return CodeSmellDetector(CODE_SMELL_THRESHOLDS)


@pytest.fixture
def structural_smell_detector():
    from code_quality_analyzer.structural_smell_detector import StructuralSmellDetector
    return StructuralSmellDetector(STRUCTURAL_THRESHOLDS)


@pytest.fixture
def architectural_smell_detector():
    from code_quality_analyzer.architectural_smell_detector import ArchitecturalSmellDetector
    return ArchitecturalSmellDetector(ARCHITECTURAL_THRESHOLDS)

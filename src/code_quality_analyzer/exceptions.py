class CodeAnalysisError(Exception):
    """Base exception class for code analysis errors"""
    def __init__(self, message, file_path=None, line_number=None, function_name=None):
        self.file_path = file_path
        self.line_number = line_number
        self.function_name = function_name
        super().__init__(f"{message}\nFile: {file_path}\nLine: {line_number}\nFunction: {function_name}") 
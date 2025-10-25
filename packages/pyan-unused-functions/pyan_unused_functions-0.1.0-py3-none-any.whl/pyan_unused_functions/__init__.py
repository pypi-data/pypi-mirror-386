"""
pyan-unused-functions
---------------------
A Python static analysis tool to find unused functions in your codebase.
"""

__version__ = "0.1.0"
__author__ = "mhs"
__license__ = "MIT"

from .analyzer import (
    FunctionUsageAnalyzer,
    analyze_python_file,
    find_python_files,
    analyze_codebase,
    find_unused_functions,
)

__all__ = [
    "FunctionUsageAnalyzer",
    "analyze_python_file",
    "find_python_files",
    "analyze_codebase",
    "find_unused_functions",
]

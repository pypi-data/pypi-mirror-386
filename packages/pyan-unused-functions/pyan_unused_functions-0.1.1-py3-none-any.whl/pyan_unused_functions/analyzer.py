#!/usr/bin/env python3
"""
find_unused_functions_improved.py
----------------------------------------
Finds Python functions that are defined but never called,
using Python's built-in AST module for more reliable parsing.

Usage:
    python find_unused_functions_improved.py path/to/your/code
Example:
    python find_unused_functions_improved.py .
"""

import ast
import sys
from pathlib import Path
from typing import Set, List, Tuple


class FunctionUsageAnalyzer(ast.NodeVisitor):
    """AST visitor to collect function definitions and calls."""
    
    def __init__(self, module_name: str, file_path: str):
        self.module_name = module_name
        self.file_path = file_path
        self.defined_functions: Set[str] = set()
        self.called_functions: Set[str] = set()
        self.function_locations: dict = {}  # func_name -> (file_path, line, col)
        self.class_stack: List[str] = []
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition and track class context."""
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition and record it."""
        if self.class_stack:
            # Method in a class
            func_name = f"{self.module_name}.{'.'.join(self.class_stack)}.{node.name}"
        else:
            # Top-level function
            func_name = f"{self.module_name}.{node.name}"
            
        # Skip special methods and private functions starting with _
        if not node.name.startswith('_'):
            self.defined_functions.add(func_name)
            # Store location information
            self.function_locations[func_name] = (self.file_path, node.lineno, node.col_offset)
            
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition and record it."""
        if self.class_stack:
            func_name = f"{self.module_name}.{'.'.join(self.class_stack)}.{node.name}"
        else:
            func_name = f"{self.module_name}.{node.name}"
            
        if not node.name.startswith('_'):
            self.defined_functions.add(func_name)
            # Store location information
            self.function_locations[func_name] = (self.file_path, node.lineno, node.col_offset)
            
        self.generic_visit(node)
        
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call and record it."""
        try:
            # Handle different types of function calls
            if isinstance(node.func, ast.Name):
                # Simple function call: func()
                self.called_functions.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # Method call: obj.method() or module.func()
                self._handle_attribute_call(node.func)
        except Exception:
            # Skip problematic calls rather than crash
            pass
            
        self.generic_visit(node)
        
    def _handle_attribute_call(self, node: ast.Attribute) -> None:
        """Handle attribute-based function calls."""
        parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
            
        if isinstance(current, ast.Name):
            parts.append(current.id)
            parts.reverse()
            full_name = '.'.join(parts)
            self.called_functions.add(full_name)


def analyze_python_file(file_path: Path) -> Tuple[Set[str], Set[str], dict]:
    """Analyze a single Python file and return defined/called functions and locations."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse the file
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return set(), set(), {}
            
        # Get module name from file path
        module_name = file_path.stem
        if file_path.name == '__init__.py':
            module_name = file_path.parent.name
            
        # Analyze the AST
        analyzer = FunctionUsageAnalyzer(module_name, str(file_path))
        analyzer.visit(tree)
        
        return analyzer.defined_functions, analyzer.called_functions, analyzer.function_locations
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return set(), set(), {}


def find_python_files(root_path: Path) -> List[Path]:
    """Find all Python files in the given path."""
    python_files = []
    
    for file_path in root_path.rglob("*.py"):
        # Skip common directories that shouldn't be analyzed
        skip_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache'}
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue
            
        python_files.append(file_path)
        
    return python_files


def analyze_codebase(root_path: Path) -> Tuple[Set[str], Set[str], dict]:
    """Analyze entire codebase and return all defined/called functions and locations."""
    python_files = find_python_files(root_path)
    
    if not python_files:
        print("No Python files found!")
        return set(), set(), {}
        
    print(f"Analyzing {len(python_files)} Python files...")
    
    all_defined = set()
    all_called = set()
    all_locations = {}
    
    for file_path in python_files:
        try:
            defined, called, locations = analyze_python_file(file_path)
            all_defined.update(defined)
            all_called.update(called)
            all_locations.update(locations)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            continue
            
    return all_defined, all_called, all_locations


def find_unused_functions(defined: Set[str], called: Set[str]) -> Set[str]:
    """Find functions that are defined but never called."""
    unused = set()
    
    for func in defined:
        # Check if function is called by name (without module prefix)
        func_name = func.split('.')[-1]
        
        # Function is unused if:
        # 1. Full qualified name is not called
        # 2. Simple name is not called
        # 3. No partial matches in called functions
        is_called = (
            func in called or
            func_name in called or
            any(func_name in call for call in called)
        )
        
        if not is_called:
            unused.add(func)
            
    return unused


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python find_unused_functions_improved.py <path_to_code>")
        sys.exit(1)
        
    root_path = Path(sys.argv[1])
    if not root_path.exists():
        print(f"Error: Path not found: {root_path}")
        sys.exit(1)
        
    print(f"Analyzing Python code in: {root_path}")
    
    # Analyze the codebase
    defined_functions, called_functions, function_locations = analyze_codebase(root_path)
    
    if not defined_functions:
        print("No functions found to analyze!")
        return
        
    # Find unused functions
    unused_functions = find_unused_functions(defined_functions, called_functions)
    
    # Display results
    print("\n=== Analysis Results ===")
    print(f"Total functions defined: {len(defined_functions)}")
    print(f"Total function calls found: {len(called_functions)}")
    print(f"Potentially unused functions: {len(unused_functions)}")
    
    if unused_functions:
        print("\n=== Potentially Unused Functions ===")
        for func in sorted(unused_functions):
            if func in function_locations:
                file_path, line_no, col_offset = function_locations[func]
                # Convert absolute path to relative path from root
                try:
                    rel_path = Path(file_path).relative_to(root_path)
                except ValueError:
                    rel_path = Path(file_path).name  # fallback to filename only
                
                # Extract just the function name for the message
                func_name = func.split('.')[-1]
                print(f" {rel_path}:{line_no}:{col_offset}: function '{func_name}' is defined but never used")
            else:
                print(f"  {func} (location unknown)")
        print("\nNote: This analysis may have false positives for:")
        print("  - Functions called dynamically (getattr, exec, etc.)")
        print("  - Functions used in decorators or metaclasses")
        print("  - Functions called from other modules not analyzed")
        print("  - Entry points, CLI commands, or framework callbacks")
    else:
        print("\nNo unused functions found!")


if __name__ == "__main__":
    main()
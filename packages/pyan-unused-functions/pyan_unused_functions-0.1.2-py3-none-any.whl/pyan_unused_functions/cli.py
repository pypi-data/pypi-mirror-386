"""
Command-line interface for pyan-unused-functions.
"""

import sys
from pathlib import Path
from .analyzer import analyze_codebase, find_unused_functions


def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: pyan-unused-functions <path_to_code>")
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

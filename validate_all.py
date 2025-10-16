#!/usr/bin/env python3
"""Validate all Python files and report syntax errors"""
import os
import py_compile
import sys

def check_file(filepath):
    """Check if a Python file has syntax errors"""
    try:
        py_compile.compile(filepath, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    errors = []
    for root, dirs, files in os.walk('backend'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                valid, error = check_file(filepath)
                if not valid:
                    errors.append((filepath, error))
                    print(f"ERROR: {filepath}")
                    print(f"  {error}\n")
    
    if errors:
        print(f"\nTotal files with errors: {len(errors)}")
        return 1
    else:
        print("\nAll files are valid!")
        return 0

if __name__ == '__main__':
    sys.exit(main())

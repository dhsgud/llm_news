#!/usr/bin/env python3
"""
Fix backend. imports in Python files without corrupting UTF-8 content
"""
import os
import sys

def fix_file(filepath):
    """Fix imports in a single file"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Replace as bytes to preserve encoding
        original = content
        content = content.replace(b'from backend.', b'from ')
        content = content.replace(b'import backend.', b'import ')
        
        if content != original:
            with open(filepath, 'wb') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
    except Exception as e:
        print(f"Error: {filepath} - {e}")
    return False

def main():
    fixed = 0
    for root, dirs, files in os.walk('backend'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if fix_file(path):
                    fixed += 1
    
    print(f"\nFixed {fixed} files")

if __name__ == '__main__':
    main()

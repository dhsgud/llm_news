#!/usr/bin/env python3
"""Fix encoding issues in Python files"""
import os
import sys

def fix_encoding(filepath):
    """Fix encoding issues by replacing corrupted characters"""
    try:
        # Try to read as UTF-8, replacing errors
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Decode with error handling
        try:
            text = content.decode('utf-8')
            # File is fine
            return False
        except UnicodeDecodeError:
            # File has encoding issues - try to fix
            text = content.decode('utf-8', errors='replace')
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Fixed encoding: {filepath}")
            return True
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    fixed_count = 0
    for root, dirs, files in os.walk('backend'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_encoding(filepath):
                    fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()

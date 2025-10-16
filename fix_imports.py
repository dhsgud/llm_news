import os
import re

def fix_imports_in_file(filepath):
    """Fix backend. imports in a Python file while preserving encoding"""
    try:
        # Read with UTF-8 encoding
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace imports
        original = content
        content = re.sub(r'from backend\.', 'from ', content)
        content = re.sub(r'import backend\.', 'import ', content)
        
        # Only write if changed
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    backend_dir = 'backend'
    fixed_count = 0
    
    for root, dirs, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, dirs, file)
                if fix_imports_in_file(filepath):
                    fixed_count += 1
                    print(f"Fixed: {filepath}")
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()

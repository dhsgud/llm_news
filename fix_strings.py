#!/usr/bin/env python3
"""Fix broken strings with replacement characters"""
import os
import re

def fix_broken_strings(filepath):
    """Fix strings that contain replacement characters"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Fix strings with replacement character that break syntax
        # Pattern: "text?�moretext" or "text?�moretext?)
        content = re.sub(r'"([^"]*?)\?�([^"]*?)\?([^"]*)$', r'"\1_\2"', content, flags=re.MULTILINE)
        content = re.sub(r'"([^"]*?)\?�([^"]*?)$', r'"\1_\2"', content, flags=re.MULTILINE)
        
        # Replace any remaining problematic patterns
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            # If line has unterminated string with replacement char
            if '?�' in line and line.count('"') % 2 != 0:
                # Try to fix by closing the string before the replacement char
                line = re.sub(r'"([^"]*?)\?�[^"]*$', r'"\1"', line)
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
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
                filepath = os.path.join(root, file)
                if fix_broken_strings(filepath):
                    fixed += 1
    
    print(f"\nFixed {fixed} files")

if __name__ == '__main__':
    main()

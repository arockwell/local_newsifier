#!/usr/bin/env python3
"""Fix remaining filter() calls in test files to use where() instead."""

import re
import os
from pathlib import Path

def process_file(file_path):
    """Replace filter with where in the file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the file uses filter()
    if "filter(" not in content:
        return False
    
    # Pattern to match db_session.exec(select(...)).filter(...).first()
    pattern = r'db_session\.exec\(select\((.*?)\)\)\s+\.filter\((.*?)\)\s+\.first\(\)'
    replacement = r'statement = select(\1).where(\2)\n        db_session.exec(statement).first()'
    
    new_content = re.sub(pattern, replacement, content)
    
    # Only write if changes were made
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    
    return False

def main():
    """Process all test files."""
    tests_dir = Path('tests')
    if not tests_dir.exists():
        print(f"Directory not found: {tests_dir}")
        return
    
    files_updated = 0
    
    # Process all Python files recursively
    for file_path in tests_dir.glob('**/*.py'):
        if process_file(file_path):
            print(f"Updated {file_path}")
            files_updated += 1
    
    print(f"Done! Updated {files_updated} files.")

if __name__ == "__main__":
    main()
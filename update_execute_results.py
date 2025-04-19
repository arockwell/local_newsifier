#!/usr/bin/env python
"""Update SQLModel query result handling in CRUD files."""

import os
import re
import glob

def process_file(file_path):
    """Process a single Python file to update result handling."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace simple .execute().first() pattern
    pattern1 = r'results = (db|session)\.execute\(([^)]+)\)\s+([a-zA-Z_]+) = results\.first\(\)'
    replacement1 = r'result = \1.execute(\2).first()\n        \3 = result[0] if result else None'
    
    new_content = re.sub(pattern1, replacement1, content)
    
    # Replace .execute() followed by .first() on separate lines
    pattern2 = r'results = (db|session)\.execute\(([^)]+)\)\s+db_(\w+) = results\.first\(\)'
    replacement2 = r'result = \1.execute(\2).first()\n        db_\3 = result[0] if result else None'
    
    new_content = re.sub(pattern2, replacement2, new_content)
    
    # Replace .all() pattern
    pattern3 = r'results = (db|session)\.execute\(([^)]+)\)\s+return results\.all\(\)'
    replacement3 = r'results = \1.execute(\2).all()\n        return [row[0] for row in results]'
    
    new_content = re.sub(pattern3, replacement3, new_content)
    
    # Only write if changes were made
    if new_content != content:
        print(f"Updating {file_path}")
        with open(file_path, 'w') as f:
            f.write(new_content)

def main():
    """Process all CRUD Python files in the src directory."""
    crud_dir = os.path.join(os.path.dirname(__file__), 'src', 'local_newsifier', 'crud')
    py_files = glob.glob(os.path.join(crud_dir, '**', '*.py'), recursive=True)
    
    for py_file in py_files:
        process_file(py_file)
    
    print("Done!")

if __name__ == "__main__":
    main()
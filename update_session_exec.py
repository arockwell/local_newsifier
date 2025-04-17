#!/usr/bin/env python
"""Update all db.exec references to db.execute in SQLModel code."""

import os
import re
import glob

def process_file(file_path):
    """Process a single Python file to replace db.exec with db.execute."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace db.exec with db.execute
    new_content = re.sub(r'(db|session)\.exec\(', r'\1.execute(', content)
    
    # Only write if changes were made
    if new_content != content:
        print(f"Updating {file_path}")
        with open(file_path, 'w') as f:
            f.write(new_content)

def main():
    """Process all Python files in the src directory."""
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    py_files = glob.glob(os.path.join(src_dir, '**', '*.py'), recursive=True)
    
    for py_file in py_files:
        process_file(py_file)
    
    print("Done!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Script to update session.query() to session.exec() in all Python files."""

import os
import re
from pathlib import Path

def process_file(file_path):
    """Process a file to replace session.query with session.exec."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check if file contains session.query
        if 'session.query' not in content and 'db_session.query' not in content:
            return False

        # Replace session.query pattern
        content = re.sub(
            r'(session|db_session)\.query\((.*?)\)',
            r'\1.exec(select(\2))',
            content
        )

        # Add required import for select if needed
        if 'select' in content and 'from sqlmodel import select' not in content:
            content = re.sub(
                r'from sqlmodel import (.*?)(\n)',
                r'from sqlmodel import \1, select\2',
                content
            )

        with open(file_path, 'w') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Find and process all Python files in the src and tests directories."""
    dirs_to_scan = [Path('tests')]
    files_updated = 0

    for base_dir in dirs_to_scan:
        if not base_dir.exists():
            print(f"Directory not found: {base_dir}")
            continue

        # Process all Python files recursively
        for file_path in base_dir.glob('**/*.py'):
            if process_file(file_path):
                print(f"Updated {file_path}")
                files_updated += 1

    print(f"Done! Updated {files_updated} files.")

if __name__ == '__main__':
    main()
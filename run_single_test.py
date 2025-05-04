#!/usr/bin/env python
"""Run a single test module without using the configured addopts from pyproject.toml."""

import sys
import subprocess

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_single_test.py <test_file_path> [additional pytest args]")
        sys.exit(1)
    
    test_file = sys.argv[1]
    additional_args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Construct the command
    cmd = ["python", "-m", "pytest", test_file, "-v"] + additional_args

    # Run the command
    subprocess.run(cmd)
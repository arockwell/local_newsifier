#!/usr/bin/env python3
"""Pre-push hook to check for PR_description.md."""

import os
import sys
from pathlib import Path

def main():
    """Check if PR_description.md exists and is not empty."""
    # Skip check if we're pushing to main/master
    branch = os.popen("git rev-parse --abbrev-ref HEAD").read().strip()
    if branch in ["main", "master"]:
        sys.exit(0)

    pr_desc_path = Path("PR_description.md")
    
    if not pr_desc_path.exists():
        print("Error: PR_description.md not found")
        print("Please create a PR description using scripts/create_pr.py")
        sys.exit(1)
    
    if pr_desc_path.stat().st_size == 0:
        print("Error: PR_description.md is empty")
        print("Please fill in the PR description using scripts/create_pr.py")
        sys.exit(1)
    
    # Check if the file contains the required sections
    with open(pr_desc_path) as f:
        content = f.read()
        required_sections = [
            "## Description",
            "## Changes Made",
            "## Testing",
            "## Related Issues",
            "## Checklist"
        ]
        
        missing_sections = [section for section in required_sections 
                          if section not in content]
        
        if missing_sections:
            print("Error: PR_description.md is missing required sections:")
            for section in missing_sections:
                print(f"  - {section}")
            print("\nPlease use scripts/create_pr.py to create a proper PR description")
            sys.exit(1)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""Script to automate PR creation with consistent formatting."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PR_TEMPLATE = """# {title}

## Description
[Clear explanation of changes]

## Changes Made
- [List specific changes]

## Testing
[Describe testing done]

## Related Issues
[Link issues or N/A]

## Checklist
- [ ] Code follows the project's coding standards
- [ ] Tests have been added/updated to reflect changes
- [ ] Documentation has been updated if necessary
- [ ] All tests pass
- [ ] Pre-commit hooks pass
- [ ] Changes have been tested in a local environment
"""

def run_command(cmd: str, capture_output: bool = True) -> tuple[int, str]:
    """Run a shell command and return exit code and output."""
    try:
        if capture_output:
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return process.returncode, process.stdout
        else:
            # For interactive commands like editors, don't capture output
            process = subprocess.run(cmd, shell=True)
            return process.returncode, ""
    except KeyboardInterrupt:
        print("\nCommand interrupted by user")
        return 1, ""

def get_current_branch() -> str:
    """Get the name of the current git branch."""
    code, output = run_command("git branch --show-current")
    if code != 0:
        print("Error: Failed to get current branch name")
        sys.exit(1)
    return output.strip()

def create_pr(title: str, skip_edit: bool = False) -> None:
    """Create a PR with proper description file."""
    # Ensure we're in a git repository
    if not Path(".git").is_dir():
        print("Error: Not in a git repository")
        sys.exit(1)

    # Get current branch
    branch = get_current_branch()
    if not branch:
        print("Error: Not in a git branch")
        sys.exit(1)

    # Create PR description file
    with open("PR_description.md", "w") as f:
        f.write(PR_TEMPLATE.format(title=title))

    # Open editor for modifications if requested
    if not skip_edit:
        editor = os.environ.get("EDITOR", "vim")
        print(f"\nOpening {editor} to edit PR description...")
        print("Save and close the editor when done.")
        code, _ = run_command(f"{editor} PR_description.md", capture_output=False)
        if code != 0:
            print("Error: Failed to edit PR description")
            sys.exit(1)

    # Verify the PR description was edited
    if not skip_edit:
        with open("PR_description.md") as f:
            content = f.read()
            if "[Clear explanation of changes]" in content:
                print("\nWarning: PR description appears to be unedited.")
                response = input("Continue anyway? [y/N]: ")
                if response.lower() != 'y':
                    print("Aborting PR creation. Edit PR_description.md and try again.")
                    sys.exit(1)

    # Commit PR description
    print("\nCreating PR...")
    commands = [
        "git add PR_description.md",
        'git commit -m "Add PR description"',
        f"git push origin {branch}",
        f'gh pr create --title "{title}" --body-file PR_description.md'
    ]

    for cmd in commands:
        print(f"\nRunning: {cmd}")
        code, output = run_command(cmd)
        if code != 0:
            print(f"Error running command: {cmd}")
            print(output)
            sys.exit(1)
        if output:
            print(output)

    print("\nPR created successfully!")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create a PR with consistent formatting")
    parser.add_argument("title", help="Title of the PR")
    parser.add_argument("--skip-edit", action="store_true", 
                      help="Skip opening editor for PR description")
    args = parser.parse_args()

    create_pr(args.title, args.skip_edit)

if __name__ == "__main__":
    main() 
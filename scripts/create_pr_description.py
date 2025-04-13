"""Script to create PR description from template."""

import shutil
from pathlib import Path

def create_pr_description():
    """Create PR description file from template."""
    template_path = Path('.github/pull_request_template.md')
    description_path = Path('pr_description.md')
    
    # Copy template to create description
    shutil.copy(template_path, description_path)
    print(f"Created PR description at {description_path}")
    print("Please edit the file with your PR details")

if __name__ == '__main__':
    create_pr_description() 
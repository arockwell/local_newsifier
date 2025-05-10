You'll analyze project dependencies for issues, updates, and potential improvements.

If a specific package is provided (e.g., project:review_dependencies sqlmodel):
- Focus analysis on that specific package and its dependencies
- Example: project:review_dependencies sqlmodel

If no package is specified:
- Analyze all project dependencies

Review dependencies with these steps:

1. Check for outdated dependencies:
   pip list --outdated

2. Get detailed information about installed packages:
   pip freeze > requirements_current.txt
   pip show {package_name} (if specific package provided)

3. Identify security vulnerabilities:
   pip-audit

4. Examine potential compatibility issues:
   - Check for version conflicts between packages
   - Look for dependency chains that might cause issues
   - Note deprecated packages or versions

5. For a specific package, analyze its usage in the codebase:
   grep -r "import {package_name}" src/
   grep -r "from {package_name}" src/
   
   This helps determine:
   - How extensively the package is used
   - Which modules depend on it
   - Whether it's being used efficiently

6. Suggest upgrade paths and note breaking changes:
   - Recommend safe version upgrades
   - Highlight potential breaking changes in newer versions
   - Provide migration tips for major version bumps

7. Look for unused dependencies:
   pip install pipreqs
   pipreqs --force
   diff requirements.txt requirements_current.txt

8. For each actionable item, provide a clear recommendation:
   - "Consider upgrading {package} to {version} for {benefit}"
   - "Remove unused dependency {package}"
   - "Address security vulnerability in {package}"
   - "Refactor usage of {package} to follow best practices"

This comprehensive analysis helps maintain a healthy dependency tree, reduces security risks, and ensures optimal package usage.
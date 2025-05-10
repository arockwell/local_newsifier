You'll identify potentially dead or unused code in the project to help clean up the codebase.

If a module path is provided (e.g., project:find_unused_code src/local_newsifier/tools):
- Focus analysis on that specific module
- Example: project:find_unused_code src/local_newsifier/tools

If no module path is provided:
- Analyze the entire project (src/ directory)

Find unused code with these steps:

1. Scan for unused imports:
   python -m pyflakes {module_path or "src/"}
   
   This identifies:
   - Imported modules never used
   - Imported functions or classes never used
   - Redundant imports

2. Look for functions and classes with no references:
   - For a specific function/class: grep -r "function_name" --include="*.py" {module_path or "src/"}
   - Check for classes only instantiated but methods never called
   - Identify public methods that are never called from outside the class

3. Detect commented-out code blocks:
   grep -r "^[ \t]*#[ \t]*def\|^[ \t]*#[ \t]*class" --include="*.py" {module_path or "src/"}
   grep -r "^[ \t]*#[ \t]*if\|^[ \t]*#[ \t]*for" --include="*.py" {module_path or "src/"}

4. Find duplicate functionality:
   - Look for similar function names doing similar tasks
   - Check for repeated code blocks across files
   - Identify redundant utility functions

5. Analyze test coverage to find untested code:
   python -m pytest --cov={module_path or "src/"} --cov-report=term-missing

6. For each type of unused code, provide recommendations:
   - "Remove unused import: {import_statement}"
   - "Consider removing unused function: {function_name} in {file_path}"
   - "Clean up commented code block at {file_path}:{line_number}"
   - "Refactor duplicate functionality: {function1} and {function2}"

7. For each recommendation, provide context and potential impact:
   - Why it appears unused
   - Potential risks of removal
   - Suggestions for safer removal (e.g., deprecate first)
   - Refactoring opportunities

This analysis helps maintain a cleaner, more maintainable codebase by identifying and cleaning up unused code.
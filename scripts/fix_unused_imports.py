#!/usr/bin/env python3
"""Script to automatically remove unused imports from Python files."""

import os
from typing import List, Tuple


def get_unused_imports(filename: str) -> List[Tuple[str, int]]:
    """Get list of unused imports in a file."""
    unused = []
    try:
        cmd = f"poetry run flake8 {filename} --select=F401"
        cmd += " --format='%(row)d:%(col)d:%(code)s:%(text)s'"
        result = os.popen(cmd).read()
        for line in result.strip().split("\n"):
            if line:
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    row = int(parts[0])
                    text = parts[3]
                    # Extract the import name from the message
                    if "imported but unused" in text:
                        import_name = text.split("'")[1]
                        unused.append((import_name, row))
    except Exception as e:
        print(f"Error processing {filename}: {e}")
    return unused


def remove_unused_imports(filename: str, unused_imports: List[Tuple[str, int]]) -> bool:
    """Remove unused imports from a file."""
    if not unused_imports:
        return False

    try:
        with open(filename, "r") as f:
            lines = f.readlines()

        # Create a set of line numbers with unused imports
        unused_lines = set()
        unused_names = {name for name, _ in unused_imports}

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check if this line contains any unused import
            if stripped.startswith(("import ", "from ")):
                for name in unused_names:
                    # Check various import patterns
                    if (
                        f"import {name}" in line
                        or f"import {name} " in line
                        or f"import {name}," in line
                        or f"import {name}\n" in line
                        or f"from {name} " in line
                        or f", {name}" in line
                        or f" {name}," in line
                        or f" {name} " in line
                        or f" {name}\n" in line
                        or line.strip() == f"import {name}"
                    ):

                        # Handle multi-import lines
                        if "," in stripped and "import" in stripped:
                            # Split imports and remove only the unused one
                            if " import " in stripped:
                                module, imports = stripped.split(" import ", 1)
                                import_list = [imp.strip() for imp in imports.split(",")]
                                import_list = [imp for imp in import_list if imp != name]
                                if import_list:
                                    lines[i] = f"{module} import {', '.join(import_list)}\n"
                                else:
                                    unused_lines.add(i)
                            else:
                                unused_lines.add(i)
                        else:
                            unused_lines.add(i)
                        break

        # Remove lines with unused imports
        new_lines = [line for i, line in enumerate(lines) if i not in unused_lines]

        # Write back to file
        with open(filename, "w") as f:
            f.writelines(new_lines)

        return True
    except Exception as e:
        print(f"Error removing imports from {filename}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    paths = ["src", "tests"]
    total_fixed = 0

    for path in paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    unused = get_unused_imports(filepath)
                    if unused:
                        print(f"Fixing {filepath}: {len(unused)} unused imports")
                        if remove_unused_imports(filepath, unused):
                            total_fixed += len(unused)

    print(f"\nTotal unused imports removed: {total_fixed}")

    # Run isort to clean up any import formatting issues
    print("\nRunning isort to clean up imports...")
    os.system("poetry run isort src tests")


if __name__ == "__main__":
    main()

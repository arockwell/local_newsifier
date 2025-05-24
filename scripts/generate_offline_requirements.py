#!/usr/bin/env python3
"""Generate requirements files suitable for offline installation.

This script reads the current requirements.txt and creates a version that's
compatible with available wheels by relaxing exact version pins.
"""
import os
import re
import sys
from pathlib import Path


def find_wheel_version(package_name, wheels_dir):
    """Find available wheel version for a package."""
    wheels_path = Path(wheels_dir)
    if not wheels_path.exists():
        return None

    # Normalize package name (e.g., fastapi-injectable -> fastapi_injectable)
    normalized_name = package_name.lower().replace("-", "_")

    for wheel_file in wheels_path.glob("*.whl"):
        wheel_name = wheel_file.name.lower()
        # Check if this wheel matches our package
        if wheel_name.startswith(normalized_name + "-"):
            # Extract version from wheel filename
            # Format: package-version-pyX-none-any.whl
            match = re.match(rf"{normalized_name}-([^-]+)-", wheel_name)
            if match:
                return match.group(1)

    return None


def generate_offline_requirements(requirements_file, wheels_dir, output_file):
    """Generate requirements file compatible with available wheels."""
    print(f"Reading requirements from: {requirements_file}")
    print(f"Checking wheels in: {wheels_dir}")
    print(f"Writing to: {output_file}")

    with open(requirements_file, "r") as f:
        requirements = f.readlines()

    modified_requirements = []
    modifications = []

    for line in requirements:
        line = line.strip()
        if not line or line.startswith("#"):
            modified_requirements.append(line)
            continue

        # Skip local package references
        if line.startswith("-e") or line.startswith("file://") or "local-newsifier" in line:
            # Skip local package to avoid conflicts
            continue

        # Parse package requirement
        match = re.match(r"^([a-zA-Z0-9_-]+)(==|>=|~=|!=|<=|<|>)(.+)$", line)
        if match:
            package_name = match.group(1)
            # operator = match.group(2)  # Not used but kept for reference
            version = match.group(3)

            # Find available wheel version
            wheel_version = find_wheel_version(package_name, wheels_dir)

            if wheel_version and wheel_version != version:
                # Use the wheel version
                new_line = f"{package_name}=={wheel_version}"
                modified_requirements.append(new_line)
                modifications.append(f"  {line} -> {new_line}")
            else:
                # Keep original
                modified_requirements.append(line)
        else:
            # Keep lines we can't parse
            modified_requirements.append(line)

    # Write output file
    with open(output_file, "w") as f:
        f.write("\n".join(modified_requirements))
        if modified_requirements and not modified_requirements[-1].endswith("\n"):
            f.write("\n")

    if modifications:
        print("\nModified package versions to match available wheels:")
        for mod in modifications:
            print(mod)
    else:
        print("\nNo modifications needed - all versions match available wheels")

    return len(modifications)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: generate_offline_requirements.py <requirements.txt> <wheels_dir> <output_file>"
        )
        sys.exit(1)

    requirements_file = sys.argv[1]
    wheels_dir = sys.argv[2]
    output_file = sys.argv[3]

    if not os.path.exists(requirements_file):
        print(f"Error: Requirements file not found: {requirements_file}")
        sys.exit(1)

    if not os.path.exists(wheels_dir):
        print(f"Error: Wheels directory not found: {wheels_dir}")
        sys.exit(1)

    modifications = generate_offline_requirements(requirements_file, wheels_dir, output_file)
    sys.exit(0)

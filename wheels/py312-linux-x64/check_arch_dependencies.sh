#!/bin/bash

# This script checks for architecture-specific dependencies
# ensuring we have both x86_64 and ARM64 versions for binary wheels

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="${SCRIPT_DIR}"

echo "Checking for architecture-specific dependencies in ${WHEELS_DIR}..."

# Look for wheels with architecture-specific markers
echo "### Architecture-specific wheels ###"
echo 

find "${WHEELS_DIR}" -name "*.whl" | grep -E '(aarch64|arm64|x86_64)' | sort

echo 
echo "### Checking for wheel architecture compatibility ###"
echo 

# Check for ARM64 wheels missing their x86_64 counterparts
python3 - << EOF
import os
import re
import glob

# Define patterns for architecture-specific wheels
arm_pattern = re.compile(r'.*-(aarch64|arm64).*\.whl$')
x86_pattern = re.compile(r'.*-x86_64.*\.whl$')

# Get list of all wheels
wheel_files = glob.glob("${WHEELS_DIR}/*.whl")

# Separate by architecture
arm_wheels = [w for w in wheel_files if arm_pattern.search(w)]
x86_wheels = [w for w in wheel_files if x86_pattern.search(w)]

print(f"Found {len(arm_wheels)} ARM64 wheels")
print(f"Found {len(x86_wheels)} x86_64 wheels")

# Helper function to extract package name and version
def extract_pkg_info(wheel_path):
    filename = os.path.basename(wheel_path)
    parts = filename.split('-')
    pkg_name = parts[0].lower().replace('_', '-')
    
    # Try to get version (second part in most cases)
    version = None
    if len(parts) > 1:
        version = parts[1]
    
    return pkg_name, version

# Find ARM wheels missing x86 equivalent
arm_packages = {extract_pkg_info(w)[0] for w in arm_wheels}
x86_packages = {extract_pkg_info(w)[0] for w in x86_wheels}

missing_x86 = arm_packages - x86_packages
missing_arm = x86_packages - arm_packages

if missing_x86:
    print("\nWARNING: The following packages have ARM64 wheels but no x86_64 equivalents:")
    for pkg in sorted(missing_x86):
        print(f"  - {pkg}")
else:
    print("\nAll ARM64 packages have x86_64 equivalents.")

if missing_arm:
    print("\nWARNING: The following packages have x86_64 wheels but no ARM64 equivalents:")
    for pkg in sorted(missing_arm):
        print(f"  - {pkg}")
else:
    print("\nAll x86_64 packages have ARM64 equivalents.")

print("\n### Architecture issues in dependencies ###")

# Check version mismatches between architectures
def get_pkg_versions(pkg_name, wheels):
    versions = set()
    for wheel in wheels:
        name, version = extract_pkg_info(wheel)
        if name.lower() == pkg_name.lower():
            versions.add(version)
    return versions

version_mismatches = []
common_packages = arm_packages.intersection(x86_packages)

for pkg in common_packages:
    arm_versions = get_pkg_versions(pkg, arm_wheels)
    x86_versions = get_pkg_versions(pkg, x86_wheels)
    
    if arm_versions != x86_versions:
        version_mismatches.append((pkg, arm_versions, x86_versions))

if version_mismatches:
    print("\nWARNING: The following packages have version mismatches between ARM64 and x86_64:")
    for pkg, arm_ver, x86_ver in version_mismatches:
        print(f"  - {pkg}:")
        print(f"    ARM64 versions: {', '.join(sorted(arm_ver))}")
        print(f"    x86_64 versions: {', '.join(sorted(x86_ver))}")
else:
    print("\nNo version mismatches between ARM64 and x86_64 wheels.")
EOF

echo
echo "Check complete. Make sure to build any missing architecture-specific wheels."
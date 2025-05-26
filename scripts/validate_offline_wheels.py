#!/usr/bin/env python3
"""Validate that all dependencies can be satisfied from offline wheels."""

import re
import subprocess
import sys
from pathlib import Path


def extract_missing_packages(error_output):
    """Extract missing package names from pip error output."""
    missing = set()

    # Pattern 1: "No matching distribution found for package-name"
    pattern1 = re.compile(r"No matching distribution found for ([^\s]+)")

    # Pattern 2: "Could not find a version that satisfies the requirement package-name"
    pattern2 = re.compile(r"Could not find a version that satisfies the requirement ([^\s]+)")

    for line in error_output.split("\n"):
        match1 = pattern1.search(line)
        if match1:
            missing.add(match1.group(1))

        match2 = pattern2.search(line)
        if match2:
            missing.add(match2.group(1))

    return missing


def validate_offline_install(wheel_dir=None):
    """Validate that offline installation will work."""
    if wheel_dir is None:
        wheel_dir = Path("wheels/linux-x86_64")
    else:
        wheel_dir = Path(wheel_dir)

    requirements = wheel_dir / "requirements.txt"

    if not wheel_dir.exists():
        print(f"Error: Wheel directory {wheel_dir} does not exist!")
        return False

    if not requirements.exists():
        print(f"Error: Requirements file {requirements} does not exist!")
        return False

    # Count available wheels
    wheel_count = len(list(wheel_dir.glob("*.whl")))
    print(f"Found {wheel_count} wheel files in {wheel_dir}")

    # Test installation in dry-run mode
    print("\nValidating offline installation...")
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        str(wheel_dir),
        "-r",
        str(requirements),
        "--dry-run",
        "--no-deps",  # First check without dependencies
        "--break-system-packages",  # Allow checking in system Python
    ]

    # First pass: check direct dependencies
    print("Checking direct dependencies...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("\n❌ Direct dependencies validation failed!")
        missing = extract_missing_packages(result.stderr)
        if missing:
            print(f"\nMissing packages: {', '.join(sorted(missing))}")
        print("\nFull error output:")
        print(result.stderr)
        return False

    print("✅ Direct dependencies OK")

    # Second pass: check with all dependencies
    print("\nChecking all dependencies (including transitive)...")
    cmd.remove("--no-deps")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("\n❌ Full validation failed!")
        missing = extract_missing_packages(result.stderr)
        if missing:
            print(f"\nMissing packages: {', '.join(sorted(missing))}")

        # Try to be helpful about what's missing
        print("\nAnalyzing missing dependencies...")
        for pkg in missing:
            print(f"\n  {pkg}:")
            # Check if any version exists
            existing = list(wheel_dir.glob(f"{pkg}-*.whl"))
            if existing:
                print(f"    Found wheels: {[w.name for w in existing]}")
                print("    Issue might be version mismatch")
            else:
                print("    No wheels found for this package")

        return False

    print("✅ All dependencies can be satisfied!")

    # Summary
    print("\n✅ Validation successful!")
    print(f"\n- Wheel directory: {wheel_dir}")
    print(f"\n- Total wheels: {wheel_count}")
    print("\n- All requirements can be installed offline")

    return True


def main():
    """Run validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate offline wheel installation")
    parser.add_argument(
        "--wheel-dir",
        default="wheels/linux-x86_64",
        help="Directory containing wheels (default: wheels/linux-x86_64)",
    )

    args = parser.parse_args()

    success = validate_offline_install(args.wheel_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

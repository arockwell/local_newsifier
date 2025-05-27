#!/usr/bin/env python
"""
Script to identify slow tests in the test suite.

Usage:
    poetry run python scripts/identify_slow_tests.py

This script runs the test suite with timing information and identifies
tests that take longer than a specified threshold.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Threshold in seconds to consider a test as slow
SLOW_TEST_THRESHOLD = 1.0


def get_test_durations() -> List[Tuple[str, float]]:
    """Run pytest with the --json-report flag to get test durations."""
    subprocess.run(
        [
            "poetry",
            "run",
            "pytest",
            "--json-report",
            "--json-report-file=test_report.json",
            "-xvs",  # Run verbosely without capturing output
        ],
        capture_output=True,
        text=True,
    )

    report_path = Path("test_report.json")
    if not report_path.exists():
        print("Failed to generate test report!")
        sys.exit(1)

    with open(report_path, "r") as f:
        report = json.load(f)

    # Remove the temporary report file
    report_path.unlink()

    # Extract test durations
    durations = []
    for test in report.get("tests", []):
        test_id = test.get("nodeid", "")
        duration = test.get("duration", 0)
        durations.append((test_id, duration))

    # Sort by duration (longest first)
    return sorted(durations, key=lambda x: x[1], reverse=True)


def identify_slow_tests(durations: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """Identify tests that take longer than the threshold."""
    slow_tests = []
    for test_id, duration in durations:
        if duration > SLOW_TEST_THRESHOLD:
            slow_tests.append((test_id, duration))
    return slow_tests


def generate_report(slow_tests: List[Tuple[str, float]], all_durations: List[Tuple[str, float]]):
    """Generate a report of slow tests."""
    total_tests = len(all_durations)
    slow_count = len(slow_tests)
    total_time = sum(duration for _, duration in all_durations)
    slow_time = sum(duration for _, duration in slow_tests)

    print("\n🔍 Test Performance Analysis 🔍")
    print("═════════════════════════════════════")
    print(f"Total tests: {total_tests}")
    print(f"Total test time: {total_time:.2f}s")
    print(f"Average test time: {total_time / total_tests:.2f}s")
    print("\n")
    print(f"Identified {slow_count} slow tests (>{SLOW_TEST_THRESHOLD}s)")
    slow_percentage = slow_time / total_time * 100
    print(f"Slow tests account for {slow_percentage:.1f}% of total test time")
    print("═════════════════════════════════════")
    print("\n🐢 Top 10 Slowest Tests 🐢")
    print("═════════════════════════════════════")

    for i, (test_id, duration) in enumerate(slow_tests[:10], 1):
        print(f"{i}. {test_id}: {duration:.2f}s")

    # Group slow tests by module
    modules = {}
    for test_id, duration in slow_tests:
        module = test_id.split("::")[0]
        if module not in modules:
            modules[module] = []
        modules[module].append((test_id, duration))

    print("\n📊 Slow Tests by Module 📊")
    print("═════════════════════════════════════")
    for module, tests in sorted(
        modules.items(), key=lambda x: sum(t[1] for t in x[1]), reverse=True
    ):
        module_time = sum(duration for _, duration in tests)
        module_count = len(tests)
        print(f"{module}: {module_time:.2f}s ({module_count} tests)")

    # Generate recommendations
    print("\n🚀 Recommendations 🚀")
    print("═════════════════════════════════════")
    print("1. Add @pytest.mark.slow decorator to the slow tests identified above")
    print("2. Run fast tests separately in CI with: pytest -m 'not slow'")

    # Generate a file with slow test markers
    with open("add_slow_markers.py", "w") as f:
        f.write("#!/usr/bin/env python\n")
        f.write('"""Script to add @pytest.mark.slow markers to slow tests."""\n\n')
        f.write("import re\n")
        f.write("from pathlib import Path\n\n")
        f.write("# List of tests to mark as slow\n")
        f.write("slow_tests = [\n")
        for test_id, duration in slow_tests:
            f.write(f"    # {duration:.2f}s\n")
            f.write(f'    "{test_id}",\n')
        f.write("]\n\n")
        f.write("def extract_file_and_test(test_id):\n")
        f.write('    """Extract file path and test name from test ID."""\n')
        f.write("    parts = test_id.split('::')\n")
        f.write("    file_path = parts[0]\n")
        f.write("    if len(parts) > 1:\n")
        f.write("        test_name = parts[-1]\n")
        f.write("        if len(parts) > 2:\n")
        f.write("            # Handle class::method format\n")
        f.write("            class_name = parts[1]\n")
        f.write("            return file_path, class_name, test_name\n")
        f.write("        return file_path, None, test_name\n")
        f.write("    return file_path, None, None\n\n")
        f.write("# Run this script to add slow markers\n")

    print("\nGenerated add_slow_markers.py script to help add slow markers.")


if __name__ == "__main__":
    print("Running tests to identify slow tests...")
    all_durations = get_test_durations()
    slow_tests = identify_slow_tests(all_durations)
    generate_report(slow_tests, all_durations)

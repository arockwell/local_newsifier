#!/bin/bash

# This script verifies that all wheels are present for both runtime and development dependencies

set -e

WHEELS_DIR="$(pwd)"
PROJECT_ROOT="$(cd ../../ && pwd)"

echo "Verifying that all wheels are present for Python 3.12 on Linux x86_64..."

# Create a temporary virtualenv for testing
echo "Creating temporary virtualenv..."
python -m venv /tmp/wheel_test_venv
source /tmp/wheel_test_venv/bin/activate

# Install pip and wheel first
pip install --no-index --find-links="${WHEELS_DIR}" pip wheel

# Try to install the project in development mode with all extras
echo "Attempting to install project with all dependencies (including development)..."
pip install --no-index --find-links="${WHEELS_DIR}" -e "${PROJECT_ROOT}[dev]"

if [ $? -eq 0 ]; then
    echo "✅ All wheels are present! Installation successful."
else
    echo "❌ Installation failed. Some wheels may be missing."
    exit 1
fi

# Clean up
deactivate
rm -rf /tmp/wheel_test_venv

echo "Verification complete."
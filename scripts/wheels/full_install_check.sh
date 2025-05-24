#!/bin/bash

# This script performs a complete installation check
# It checks for missing dependencies and ensures compatibility
# with both ARM64 and x86_64 architectures

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="${SCRIPT_DIR}"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"

echo "Performing complete installation check for Python 3.12..."

# First, verify arch compatibility
echo "Checking architecture compatibility..."
"${SCRIPT_DIR}/check_arch_dependencies.sh"

# Create a temporary virtual environment for testing
echo "Creating temporary virtual environment for installation testing..."
rm -rf /tmp/wheel_test_venv
python -m venv /tmp/wheel_test_venv
source /tmp/wheel_test_venv/bin/activate

# Install the project and all dependencies
echo "Installing the project and all dependencies using the installation helper..."
"${SCRIPT_DIR}/install_helper.sh"

# Verify the installation by importing key modules
echo "Verifying imports of key modules..."
python -c "
import importlib

modules_to_check = [
    'sqlalchemy',
    'greenlet',
    'typing_extensions',
    'fastapi',
    'fastapi_injectable',
    'uvicorn',
    'uvloop',
    'watchfiles',
    'httptools',
    'websockets',
    'pytest',
    'pytest_asyncio',
    'starlette'
]

missing = []
for module in modules_to_check:
    try:
        importlib.import_module(module)
        print(f'✅ Successfully imported {module}')
    except ImportError as e:
        print(f'❌ Failed to import {module}: {e}')
        missing.append(module)

if missing:
    print(f'\\nThe following modules could not be imported: {missing}')
    exit(1)
else:
    print('\\nAll modules successfully imported!')
"

# Clean up
deactivate
rm -rf /tmp/wheel_test_venv

echo "Complete installation check finished successfully!"
echo "All dependencies are present and importable."
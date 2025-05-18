#!/bin/bash
# Test the offline installation process
# Usage: ./scripts/test_offline_install.sh [python_command]
# Example: ./scripts/test_offline_install.sh python3.12

set -e

# Use the provided Python command or default to the system Python
PYTHON_CMD=${1:-python3}

# Verify Python command exists
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: Python command '$PYTHON_CMD' not found"
    echo "Usage: $0 [python_command]"
    echo "Example: $0 python3.12"
    exit 1
fi

# Get Python version information
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

# Determine platform type for directory name
if [[ "$(uname)" == "Darwin" ]]; then
    OS_TYPE="macos"
elif [[ "$(uname)" == "Linux" ]]; then
    OS_TYPE="linux"
elif [[ "$(uname)" == *"MINGW"* ]] || [[ "$(uname)" == *"MSYS"* ]]; then
    OS_TYPE="windows"
else
    OS_TYPE="other"
fi

# Create an abbreviated architecture name
MACHINE_TYPE=$(uname -m)
if [[ "$MACHINE_TYPE" == "x86_64" ]] || [[ "$MACHINE_TYPE" == "AMD64" ]]; then
    ARCH="x64"
elif [[ "$MACHINE_TYPE" == "arm64" ]] || [[ "$MACHINE_TYPE" == "aarch64" ]]; then
    ARCH="arm64"
else
    ARCH="$MACHINE_TYPE"
fi

PYTHON_DIR="py${PYTHON_VERSION//./}-${OS_TYPE}-${ARCH}"
WHEELS_DIR="wheels/${PYTHON_DIR}"

echo "Testing offline installation for Python $PYTHON_VERSION on $OS_TYPE-$ARCH"

# Check if the wheels directory exists
if [ ! -d "$WHEELS_DIR" ]; then
    echo "Warning: Platform-specific wheels directory not found: $WHEELS_DIR"
    echo "Checking for Python version-specific directory..."
    
    # Fall back to version-specific directory without platform
    PYTHON_DIR="py${PYTHON_VERSION//./}"
    WHEELS_DIR="wheels/${PYTHON_DIR}"
    
    if [ ! -d "$WHEELS_DIR" ]; then
        echo "Error: No wheels directory found for Python $PYTHON_VERSION"
        echo "Please build wheels first with: ./scripts/build_wheels.sh $PYTHON_CMD"
        echo "For cross-platform support, wheels need to be built on each target platform."
        exit 1
    else
        echo "Found Python version-specific wheels directory without platform: $WHEELS_DIR"
        echo "Note: These wheels may not be compatible with your current platform."
    fi
fi

# Count the wheels
WHEEL_COUNT=$(find "$WHEELS_DIR" -name "*.whl" | wc -l)
echo "Found $WHEEL_COUNT wheel files in $WHEELS_DIR"

# Check for SQLAlchemy wheel specifically
SQLALCHEMY_WHEEL=$(find "$WHEELS_DIR" -name "sqlalchemy*.whl" | head -1)
if [ -z "$SQLALCHEMY_WHEEL" ]; then
    echo "Error: SQLAlchemy wheel not found in $WHEELS_DIR"
    echo "Please rebuild wheels with: ./scripts/build_wheels.sh $PYTHON_CMD"
    exit 1
else
    echo "Found SQLAlchemy wheel: $(basename "$SQLALCHEMY_WHEEL")"
fi

# Create a temporary virtual environment for testing
TEMP_VENV=$(mktemp -d)
echo "Creating temporary virtual environment in $TEMP_VENV"

# Initialize virtual environment
$PYTHON_CMD -m venv "$TEMP_VENV"
VENV_PIP="$TEMP_VENV/bin/pip"

# Simulate offline installation
echo "Testing offline installation..."
$VENV_PIP install --no-index --find-links="$WHEELS_DIR" -r requirements.txt

# Check that SQLAlchemy was installed
if $TEMP_VENV/bin/python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__} successfully installed')" 2>/dev/null; then
    echo "✅ Offline installation test passed: SQLAlchemy was installed correctly"
    TEST_RESULT=0
else
    echo "❌ Offline installation test failed: SQLAlchemy was not installed correctly"
    TEST_RESULT=1
fi

# Clean up
echo "Cleaning up temporary virtual environment"
rm -rf "$TEMP_VENV"

exit $TEST_RESULT
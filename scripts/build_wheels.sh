#!/bin/bash
# Build wheels for dependencies in requirements.txt
# Usage: ./scripts/build_wheels.sh [python_command]
# Example: ./scripts/build_wheels.sh python3.12
#          ./scripts/build_wheels.sh python3.13

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
PYTHON_PLATFORM=$($PYTHON_CMD -c "import platform; print(platform.platform())")
PYTHON_MACHINE=$($PYTHON_CMD -c "import platform; print(platform.machine())")

# Determine platform type for directory name
if [[ "$PYTHON_PLATFORM" == *"macOS"* ]] || [[ "$PYTHON_PLATFORM" == *"Darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$PYTHON_PLATFORM" == *"Linux"* ]]; then
    OS_TYPE="linux"
elif [[ "$PYTHON_PLATFORM" == *"Windows"* ]]; then
    OS_TYPE="windows"
else
    OS_TYPE="other"
fi

# Create an abbreviated architecture name
if [[ "$PYTHON_MACHINE" == "x86_64" ]] || [[ "$PYTHON_MACHINE" == "AMD64" ]]; then
    ARCH="x64"
elif [[ "$PYTHON_MACHINE" == "arm64" ]] || [[ "$PYTHON_MACHINE" == "aarch64" ]]; then
    ARCH="arm64"
else
    ARCH="$PYTHON_MACHINE"
fi

echo "Building wheels for Python $PYTHON_VERSION on $OS_TYPE-$ARCH ($PYTHON_PLATFORM)"

# Create a platform-specific directory to avoid mixing wheels from different platforms
WHEELS_DIR="wheels/py${PYTHON_VERSION//./}-${OS_TYPE}-${ARCH}"
mkdir -p "$WHEELS_DIR"

echo "Downloading wheels to $WHEELS_DIR..."

# Make sure pip is up to date
$PYTHON_CMD -m pip install --upgrade pip

# Download build dependencies first
$PYTHON_CMD -m pip wheel poetry-core -w "$WHEELS_DIR"

# Download all dependencies with their dependencies
$PYTHON_CMD -m pip wheel -r requirements.txt -w "$WHEELS_DIR"

# Download base tools without dependencies
$PYTHON_CMD -m pip wheel --no-deps --wheel-dir="$WHEELS_DIR" pip setuptools wheel

# Create a manifest file to record platform info
echo "Python Version: $PYTHON_VERSION" > "$WHEELS_DIR/manifest.txt"
echo "Platform: $PYTHON_PLATFORM" >> "$WHEELS_DIR/manifest.txt"
echo "OS Type: $OS_TYPE" >> "$WHEELS_DIR/manifest.txt"
echo "Architecture: $ARCH" >> "$WHEELS_DIR/manifest.txt"
echo "Machine: $PYTHON_MACHINE" >> "$WHEELS_DIR/manifest.txt"
echo "Date: $(date)" >> "$WHEELS_DIR/manifest.txt"
echo "Wheel Count: $(find "$WHEELS_DIR" -name "*.whl" | wc -l)" >> "$WHEELS_DIR/manifest.txt"

# Create a .platform file to make it easier for scripts to identify the platform
echo "$OS_TYPE-$ARCH" > "$WHEELS_DIR/.platform"

echo "Wheels successfully stored in $WHEELS_DIR"
echo "To install using these wheels:"
echo "$PYTHON_CMD -m pip install --no-index --find-links=$WHEELS_DIR -r requirements.txt"

#!/bin/bash
# Build the missing coverage wheel for Linux x86_64 platform

set -euo pipefail

echo "Building coverage wheel for Linux x86_64..."

# Define wheel directory
WHEEL_DIR="wheels/py312-linux-x86_64"

# Ensure directory exists
mkdir -p "$WHEEL_DIR"

# Create a temporary requirements file with just coverage
TEMP_REQ=$(mktemp)
echo "coverage>=7.8.0" > "$TEMP_REQ"

echo "Downloading coverage wheel for Linux x86_64 (Python 3.12)..."

# Download wheels - try multiple platform tags for compatibility
pip download \
    --platform manylinux2014_x86_64 \
    --platform manylinux_2_17_x86_64 \
    --platform manylinux_2_28_x86_64 \
    --platform manylinux_2_34_x86_64 \
    --platform linux_x86_64 \
    --python-version 312 \
    --only-binary :all: \
    --dest "$WHEEL_DIR" \
    -r "$TEMP_REQ" || {
        echo "Failed with platform-specific download, trying without platform restriction..."
        pip download \
            --only-binary :all: \
            --dest "$WHEEL_DIR" \
            coverage>=7.8.0
    }

# Clean up
rm -f "$TEMP_REQ"

# Check if coverage wheel was downloaded
COVERAGE_WHEEL=$(find "$WHEEL_DIR" -name "coverage-*.whl" | grep -E "cp312|py3" | head -1)
if [ -n "$COVERAGE_WHEEL" ]; then
    echo "Successfully downloaded: $(basename "$COVERAGE_WHEEL")"
else
    echo "ERROR: Failed to download coverage wheel!"
    exit 1
fi

echo "Done! Coverage wheel added to $WHEEL_DIR/"

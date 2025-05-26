#!/bin/bash
# Build wheels for Linux x86_64 platform only

set -euo pipefail

echo "Building wheels for Linux x86_64..."

# Define wheel directory
WHEEL_DIR="wheels/linux-x86_64"

# Clean existing directory (but keep requirements.txt)
if [ -f "$WHEEL_DIR/requirements.txt" ]; then
    cp "$WHEEL_DIR/requirements.txt" /tmp/requirements_backup.txt
fi

rm -rf "$WHEEL_DIR"
mkdir -p "$WHEEL_DIR"

if [ -f "/tmp/requirements_backup.txt" ]; then
    mv /tmp/requirements_backup.txt "$WHEEL_DIR/requirements.txt"
fi

# Ensure requirements.txt exists
if [ ! -f "$WHEEL_DIR/requirements.txt" ]; then
    echo "Error: $WHEEL_DIR/requirements.txt not found!"
    echo "Creating from main requirements.txt..."
    grep -v "^-e" requirements.txt > "$WHEEL_DIR/requirements.txt"
fi

echo "Downloading wheels for Linux x86_64 (Python 3.12)..."

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
    -r "$WHEEL_DIR/requirements.txt" || true

# Some packages might not have wheels, try getting them without platform restriction
echo "Attempting to download any missing packages..."
pip download \
    --only-binary :all: \
    --dest "$WHEEL_DIR" \
    -r "$WHEEL_DIR/requirements.txt" || true

# Create manifest
echo "Creating wheel manifest..."
find "$WHEEL_DIR" -name "*.whl" | sort > "$WHEEL_DIR/manifest.txt"

# Count wheels
WHEEL_COUNT=$(find "$WHEEL_DIR" -name "*.whl" | wc -l)
echo "Downloaded $WHEEL_COUNT wheel files"

echo "Done! Wheels are in $WHEEL_DIR/"

#!/bin/bash
# Build wheels for Linux x86_64 platform including development dependencies

set -euo pipefail

echo "Building wheels for Linux x86_64 (including dev dependencies)..."

# Define wheel directory
WHEEL_DIR="wheels/py312-linux-x86_64"

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

echo "Downloading runtime wheels for Linux x86_64 (Python 3.12)..."

# Download runtime wheels - try multiple platform tags for compatibility
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

# Download development dependencies if requirements-dev.txt exists
if [ -f "requirements-dev.txt" ]; then
    echo "Downloading development wheels for Linux x86_64 (Python 3.12)..."
    pip download \
        --platform manylinux2014_x86_64 \
        --platform manylinux_2_17_x86_64 \
        --platform manylinux_2_28_x86_64 \
        --platform manylinux_2_34_x86_64 \
        --platform linux_x86_64 \
        --python-version 312 \
        --only-binary :all: \
        --dest "$WHEEL_DIR" \
        -r requirements-dev.txt || true
fi

# Some packages might not have wheels, try getting them without platform restriction
echo "Attempting to download any missing packages..."
pip download \
    --only-binary :all: \
    --dest "$WHEEL_DIR" \
    -r "$WHEEL_DIR/requirements.txt" || true

if [ -f "requirements-dev.txt" ]; then
    pip download \
        --only-binary :all: \
        --dest "$WHEEL_DIR" \
        -r requirements-dev.txt || true
fi

# Create manifest
echo "Creating wheel manifest..."
find "$WHEEL_DIR" -name "*.whl" | sort > "$WHEEL_DIR/manifest.txt"

# Verify critical dev dependencies
echo "Verifying critical development dependencies..."
MISSING_DEPS=""

# Check for coverage (needed by pytest-cov)
if ! find "$WHEEL_DIR" -name "coverage-*.whl" | grep -q .; then
    MISSING_DEPS="$MISSING_DEPS coverage"
fi

# Check for other critical dev dependencies
for dep in pytest pytest_cov pytest_mock pytest_asyncio black isort flake8; do
    if ! find "$WHEEL_DIR" -name "${dep}-*.whl" -o -name "${dep//_/-}-*.whl" | grep -q .; then
        MISSING_DEPS="$MISSING_DEPS $dep"
    fi
done

if [ -n "$MISSING_DEPS" ]; then
    echo "WARNING: Missing critical development dependencies:$MISSING_DEPS"
    echo "These may need to be downloaded separately or built from source."
fi

# Count wheels
WHEEL_COUNT=$(find "$WHEEL_DIR" -name "*.whl" | wc -l)
echo "Downloaded $WHEEL_COUNT wheel files"

# Create a README for the directory
cat > "$WHEEL_DIR/README.md" << EOF
# Linux x86_64 Wheels for Python 3.12

This directory contains pre-built wheel files for offline installation on Linux x86_64 systems.

## Installation

For runtime dependencies:
\`\`\`bash
pip install --no-index --find-links=. -r requirements.txt
\`\`\`

For development dependencies:
\`\`\`bash
pip install --no-index --find-links=. -r ../../requirements-dev.txt
\`\`\`

## Contents

- Runtime dependencies from \`requirements.txt\`
- Development dependencies from \`requirements-dev.txt\`
- Total wheels: $WHEEL_COUNT

Generated on: $(date)
EOF

echo "Done! Wheels are in $WHEEL_DIR/"

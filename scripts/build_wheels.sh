#!/bin/bash
# Build wheels for dependencies in requirements.txt
# Usage: ./scripts/build_wheels.sh

set -e

WHEELS_DIR="wheels"
mkdir -p "$WHEELS_DIR"

echo "Downloading wheels to $WHEELS_DIR..."
# Download build dependencies first
pip wheel poetry-core -w "$WHEELS_DIR"

# Download all dependencies
pip wheel -r requirements.txt -w "$WHEELS_DIR"

# Download all dependencies recursively (including build dependencies)
pip wheel --no-deps --wheel-dir="$WHEELS_DIR" pip setuptools wheel
pip wheel --no-deps --wheel-dir="$WHEELS_DIR" -r requirements.txt

echo "Wheels stored in $WHEELS_DIR"

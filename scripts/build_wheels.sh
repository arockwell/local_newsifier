#!/bin/bash
# Build wheels for dependencies in requirements.txt
# Usage: ./scripts/build_wheels.sh

set -e

WHEELS_DIR="wheels"
mkdir -p "$WHEELS_DIR"

echo "Downloading wheels to $WHEELS_DIR..."
pip wheel -r requirements.txt -w "$WHEELS_DIR"
echo "Wheels stored in $WHEELS_DIR"

#!/bin/bash

# This script builds all dev dependency wheels for Linux x86_64 and Python 3.12
# It ensures all development and testing dependencies are available for offline installation

set -e

# Resolve repository root based on this script's location
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

PYTHON_VERSION="3.12"
OUTPUT_DIR="${ROOT_DIR}/wheels/py312-linux-x64"
mkdir -p "$OUTPUT_DIR"

echo "Building development dependency wheels for Python ${PYTHON_VERSION} on Linux x86_64..."

# Create a requirements.txt with all dev dependencies
cat > dev_requirements.txt << EOF
pytest>=8.0.0
pytest-mock>=3.12.0
pytest-cov>=4.1.0
pytest-asyncio>=0.26.0
pre-commit>=3.6.0
black>=24.1.1
isort>=5.13.2
flake8>=7.0.0
flake8-docstrings>=1.7.0
pytest-profiling>=1.8.1
pytest-xdist>=3.6.1
EOF

# Run a Docker container to build the wheels
docker run --rm -v "${OUTPUT_DIR}:/wheels" -v "${OUTPUT_DIR}/dev_requirements.txt:/requirements.txt" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building wheels inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel -r /requirements.txt --wheel-dir=/wheels
    echo 'Wheels built successfully!'
"

# Clean up
rm -f dev_requirements.txt

echo "Done building dev dependency wheels."
#!/bin/bash
# Build SQLAlchemy wheels for Linux platforms using Docker
# Usage: ./scripts/build_linux_wheels.sh [python_version]
# Example: ./scripts/build_linux_wheels.sh 3.13

set -e

# Default to Python 3.13 if no version is specified
PYTHON_VERSION=${1:-"3.13"}
PYTHON_VERSION_DOTLESS=${PYTHON_VERSION//./}

# Normalize Python version format
if [[ "$PYTHON_VERSION" == "python"* ]]; then
    PYTHON_VERSION=${PYTHON_VERSION#python}
fi

echo "Building SQLAlchemy wheel for Python $PYTHON_VERSION on Linux using Docker"

# Determine the architecture of the Docker container
ARCH="x64"  # Default to x64 for Linux
if [[ $(docker info | grep "Architecture" | awk '{print $2}') == "aarch64" || $(docker info | grep "Architecture" | awk '{print $2}') == "arm64" ]]; then
    ARCH="arm64"
fi

# Create volume directories to share with the container
WHEEL_OUTPUT_DIR="wheels/py${PYTHON_VERSION_DOTLESS}-linux-${ARCH}"
mkdir -p "$WHEEL_OUTPUT_DIR"

# Run a simple container to just build the SQLAlchemy wheel
echo "Running container to build SQLAlchemy wheel..."
docker run --rm \
    -v "$(pwd)/$WHEEL_OUTPUT_DIR:/wheels" \
    python:${PYTHON_VERSION} \
    /bin/bash -c "pip install --upgrade pip && pip wheel sqlalchemy==2.0.41 -w /wheels"

# Create a platform identifier file
echo "linux-${ARCH}" > "$WHEEL_OUTPUT_DIR/.platform"

echo "SQLAlchemy wheel for Python $PYTHON_VERSION has been built in $WHEEL_OUTPUT_DIR"
echo "Organize the wheels using ./scripts/organize_wheels.sh"
#!/bin/bash
# Build wheels for Linux platforms using Docker
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

echo "Building wheels for Python $PYTHON_VERSION on Linux using Docker"

# Build the Docker image
echo "Building Docker image for Python $PYTHON_VERSION..."
docker build -t local-newsifier-wheel-builder-py$PYTHON_VERSION_DOTLESS -f scripts/Dockerfile --build-arg PYTHON_VERSION=$PYTHON_VERSION .

# Create volume directories to share with the container
WHEEL_OUTPUT_DIR="wheels/py${PYTHON_VERSION_DOTLESS}-linux-x64"
mkdir -p "$WHEEL_OUTPUT_DIR"

# Run the container to build wheels
echo "Running container to build wheels..."
docker run --rm \
    -v "$(pwd)/requirements.txt:/app/requirements.txt" \
    -v "$(pwd)/$WHEEL_OUTPUT_DIR:/app/$WHEEL_OUTPUT_DIR" \
    local-newsifier-wheel-builder-py$PYTHON_VERSION_DOTLESS

echo "Linux wheels for Python $PYTHON_VERSION have been built in $WHEEL_OUTPUT_DIR"
echo "Organize the wheels using ./scripts/organize_wheels.sh"
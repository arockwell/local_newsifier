#!/bin/bash
# Build Python package wheels for Linux platforms using Docker
# Usage: ./scripts/build_linux_wheels.sh [python_version]
# Example: ./scripts/build_linux_wheels.sh 3.12

set -e

# Default to Python 3.12 if no version is specified
PYTHON_VERSION=${1:-"3.12"}
PYTHON_VERSION_DOTLESS=${PYTHON_VERSION//./}

# Normalize Python version format
if [[ "$PYTHON_VERSION" == "python"* ]]; then
    PYTHON_VERSION=${PYTHON_VERSION#python}
fi

echo "Building all dependency wheels for Python $PYTHON_VERSION on Linux using Docker"

# Determine the architecture of the Docker container
ARCH="x64"  # Default to x64 for Linux
if [[ $(docker info | grep "Architecture" | awk '{print $2}') == "aarch64" || $(docker info | grep "Architecture" | awk '{print $2}') == "arm64" ]]; then
    ARCH="arm64"
fi

# Create volume directories to share with the container
WHEEL_OUTPUT_DIR="wheels/py${PYTHON_VERSION_DOTLESS}-linux-${ARCH}"
mkdir -p "$WHEEL_OUTPUT_DIR"

# Docker build command with PostgreSQL build dependencies
DOCKER_BUILD_CMD='apt-get update && apt-get install -y build-essential libpq-dev && pip install --upgrade pip && pip wheel -r /requirements.txt -w /wheels'

# Build for both ARM64 and x64 architectures if on ARM64
if [[ "$ARCH" == "arm64" ]]; then
    echo "Building for both arm64 and x64 architectures..."
    
    # First build for arm64
    echo "Building wheels for Python $PYTHON_VERSION on linux-arm64..."
    docker run --rm \
        -v "$(pwd)/$WHEEL_OUTPUT_DIR:/wheels" \
        -v "$(pwd)/requirements.txt:/requirements.txt" \
        python:${PYTHON_VERSION} \
        /bin/bash -c "$DOCKER_BUILD_CMD"
    
    # Create a platform identifier file
    echo "linux-${ARCH}" > "$WHEEL_OUTPUT_DIR/.platform"
    echo "Python Version: $PYTHON_VERSION" > "$WHEEL_OUTPUT_DIR/manifest.txt"
    echo "Platform: Linux-arm64" >> "$WHEEL_OUTPUT_DIR/manifest.txt"
    echo "Date: $(date)" >> "$WHEEL_OUTPUT_DIR/manifest.txt"
    echo "Wheel Count: $(find "$WHEEL_OUTPUT_DIR" -name "*.whl" | wc -l)" >> "$WHEEL_OUTPUT_DIR/manifest.txt"
    
    # Then build for x86_64 (x64)
    echo "Now building wheels for Python $PYTHON_VERSION on linux-x64..."
    X64_WHEEL_DIR="wheels/py${PYTHON_VERSION_DOTLESS}-linux-x64"
    mkdir -p "$X64_WHEEL_DIR"
    
    # Use --platform to specify x86_64 architecture
    docker run --rm --platform linux/amd64 \
        -v "$(pwd)/$X64_WHEEL_DIR:/wheels" \
        -v "$(pwd)/requirements.txt:/requirements.txt" \
        python:${PYTHON_VERSION} \
        /bin/bash -c "$DOCKER_BUILD_CMD"
    
    # Create a platform identifier file for x64
    echo "linux-x64" > "$X64_WHEEL_DIR/.platform"
    echo "Python Version: $PYTHON_VERSION" > "$X64_WHEEL_DIR/manifest.txt"
    echo "Platform: Linux-x86_64" >> "$X64_WHEEL_DIR/manifest.txt"
    echo "Date: $(date)" >> "$X64_WHEEL_DIR/manifest.txt"
    echo "Wheel Count: $(find "$X64_WHEEL_DIR" -name "*.whl" | wc -l)" >> "$X64_WHEEL_DIR/manifest.txt"
    
    echo "All dependency wheels for Python $PYTHON_VERSION have been built in:"
    echo "- $WHEEL_OUTPUT_DIR (arm64)"
    echo "- $X64_WHEEL_DIR (x86_64)"
else
    # Regular build for x64
    echo "Building wheels for Python $PYTHON_VERSION on linux-x64..."
    docker run --rm \
        -v "$(pwd)/$WHEEL_OUTPUT_DIR:/wheels" \
        -v "$(pwd)/requirements.txt:/requirements.txt" \
        python:${PYTHON_VERSION} \
        /bin/bash -c "$DOCKER_BUILD_CMD"
    
    # Create a platform identifier file
    echo "linux-x64" > "$WHEEL_OUTPUT_DIR/.platform"
    echo "Python Version: $PYTHON_VERSION" > "$WHEEL_OUTPUT_DIR/manifest.txt"
    echo "Platform: Linux-x86_64" >> "$WHEEL_OUTPUT_DIR/manifest.txt"
    echo "Date: $(date)" >> "$WHEEL_OUTPUT_DIR/manifest.txt"
    echo "Wheel Count: $(find "$WHEEL_OUTPUT_DIR" -name "*.whl" | wc -l)" >> "$WHEEL_OUTPUT_DIR/manifest.txt"
    
    echo "All dependency wheels for Python $PYTHON_VERSION have been built in $WHEEL_OUTPUT_DIR"
fi

echo "NOTE: For psycopg2-binary and other platform-specific packages, ensure you have the correct build dependencies in the Docker container."
echo "If any wheels are missing, check that all build dependencies are installed."
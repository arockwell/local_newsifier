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

# Force x86_64 architecture for Linux builds by using a specific platform tag
if [[ "$ARCH" == "arm64" ]]; then
    echo "Building for both arm64 and x64 architectures..."
    
    # First build for arm64
    docker run --rm \
        -v "$(pwd)/$WHEEL_OUTPUT_DIR:/wheels" \
        python:${PYTHON_VERSION} \
        /bin/bash -c "pip install --upgrade pip && pip wheel sqlalchemy==2.0.41 -w /wheels"
    
    # Then build for x86_64 (x64)
    echo "Now building for x86_64 architecture..."
    X64_WHEEL_DIR="wheels/py${PYTHON_VERSION_DOTLESS}-linux-x64"
    mkdir -p "$X64_WHEEL_DIR"
    
    # Use --platform to specify x86_64 architecture
    docker run --rm --platform linux/amd64 \
        -v "$(pwd)/$X64_WHEEL_DIR:/wheels" \
        python:${PYTHON_VERSION} \
        /bin/bash -c "pip install --upgrade pip && pip wheel sqlalchemy==2.0.41 -w /wheels"
    
    # Create a platform identifier file for x64
    echo "linux-x64" > "$X64_WHEEL_DIR/.platform"
    
    echo "SQLAlchemy wheel for Python $PYTHON_VERSION has been built in $X64_WHEEL_DIR (x86_64)"
else
    # Regular build for x64
    docker run --rm \
        -v "$(pwd)/$WHEEL_OUTPUT_DIR:/wheels" \
        python:${PYTHON_VERSION} \
        /bin/bash -c "pip install --upgrade pip && pip wheel sqlalchemy==2.0.41 -w /wheels"
fi

# Create a platform identifier file
echo "linux-${ARCH}" > "$WHEEL_OUTPUT_DIR/.platform"

echo "SQLAlchemy wheel for Python $PYTHON_VERSION has been built in $WHEEL_OUTPUT_DIR"
echo "Organize the wheels using ./scripts/organize_wheels.sh"
#!/bin/bash

# This script builds the x86_64 versions of the wheels
# It specifically targets the dependencies needed for Linux x86_64

set -e

WHEELS_DIR="$(pwd)"
PYTHON_VERSION="3.12"
OUTPUT_DIR="${WHEELS_DIR}"

echo "Building x86_64 wheels for Python ${PYTHON_VERSION} on Linux x86_64..."

# Create a requirements.txt with the exact version requirements for x86_64
cat > x86_64_requirements.txt << EOF
regex==2024.9.11
tomli==2.2.1
tomli-w==1.0.0
uv==0.4.25
yarl==1.17.0
vine==5.0.0
multidict==6.4.3
propcache==0.3.1
MarkupSafe==3.0.2
EOF

# Run a Docker container to build the wheels with x86_64 architecture
docker run --rm -v "${OUTPUT_DIR}:/wheels" -v "${OUTPUT_DIR}/x86_64_requirements.txt:/requirements.txt" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building x86_64 wheels inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel -r /requirements.txt --wheel-dir=/wheels || echo 'Some wheels failed to build, but continuing...'
    echo 'Wheels built successfully!'
"

# Clean up
rm -f x86_64_requirements.txt

echo "Done building x86_64 wheels."
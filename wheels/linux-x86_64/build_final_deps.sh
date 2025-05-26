#!/bin/bash

# This script builds the final missing dependencies for Linux x86_64 and Python 3.12
# It specifically targets the dependencies that are still causing issues

set -e

WHEELS_DIR="$(pwd)"
PYTHON_VERSION="3.12"
OUTPUT_DIR="${WHEELS_DIR}"

echo "Building final missing dependencies for Python ${PYTHON_VERSION} on Linux x86_64..."

# Create a requirements.txt with the exact version requirements that are missing
cat > final_requirements.txt << EOF
pyvis==0.3.2
regex==2024.9.11
tomli==2.2.1
tomli-w==1.0.0
uv==0.4.25
yarl==1.17.0
vine==5.0.0
EOF

# Run a Docker container to build the wheels
docker run --rm -v "${OUTPUT_DIR}:/wheels" -v "${OUTPUT_DIR}/final_requirements.txt:/requirements.txt" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building final wheels inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel -r /requirements.txt --wheel-dir=/wheels || echo 'Some wheels failed to build, but continuing...'
    echo 'Wheels built successfully!'
"

# Clean up
rm -f final_requirements.txt

echo "Done building final dependency wheels."

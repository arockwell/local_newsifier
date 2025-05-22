#!/bin/bash

# This script builds missing x86_64 versions of architecture-specific wheels
# that already have ARM64 versions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="${SCRIPT_DIR}"
PYTHON_VERSION="3.12"
OUTPUT_DIR="${WHEELS_DIR}"

echo "Building missing x86_64 wheels for Python ${PYTHON_VERSION}..."

# Look for ARM-specific wheels that need an x86_64 counterpart
ARM_WHEELS=$(find "${WHEELS_DIR}" -name "*aarch64*.whl" -o -name "*arm64*.whl" | grep -v "x86_64")

# Create a requirements file with their matching packages
cat > missing_x86_wheels.txt << EOF
# Build x86_64 versions of wheels that only have ARM64 versions currently
uvicorn==0.34.2
uvloop==0.21.0
watchfiles==1.0.5
websockets==15.0.1
httptools==0.6.4
python-dotenv==1.1.0
PyYAML==6.0.2
EOF

# Run a Docker container to build the wheels
docker run --rm -v "${OUTPUT_DIR}:/wheels" -v "${OUTPUT_DIR}/missing_x86_wheels.txt:/requirements.txt" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building missing x86_64 wheels inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel -r /requirements.txt --wheel-dir=/wheels
    
    # Also explicitly build uvicorn with standard
    pip wheel uvicorn[standard] --wheel-dir=/wheels
    
    echo 'Missing x86_64 wheels built successfully!'
"

# Clean up
rm -f missing_x86_wheels.txt

echo "Done building missing x86_64 wheels."
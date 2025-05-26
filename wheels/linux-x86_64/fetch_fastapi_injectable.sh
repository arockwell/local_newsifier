#!/bin/bash

# This script specifically builds fastapi-injectable and its dependencies
# for Python 3.12 on Linux x86_64

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="${SCRIPT_DIR}"
PYTHON_VERSION="3.12"
OUTPUT_DIR="${WHEELS_DIR}"

echo "Building fastapi-injectable for Python ${PYTHON_VERSION} on Linux x86_64..."

# Create a requirements file for fastapi-injectable
cat > fastapi_injectable_reqs.txt << EOF
fastapi-injectable==0.7.0
EOF

# Run a Docker container to build the wheels
docker run --rm -v "${OUTPUT_DIR}:/wheels" -v "${OUTPUT_DIR}/fastapi_injectable_reqs.txt:/requirements.txt" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building fastapi-injectable inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel -r /requirements.txt --wheel-dir=/wheels

    # Also build any direct dependencies just to be safe
    pip wheel fastapi-injectable==0.7.0 --wheel-dir=/wheels

    echo 'fastapi-injectable wheel built successfully!'
"

# Clean up
rm -f fastapi_injectable_reqs.txt

echo "Done building fastapi-injectable wheel."

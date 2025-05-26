#!/bin/bash

# This script builds the missing fastapi-injectable wheel for Linux x86_64 and Python 3.12

set -e

WHEELS_DIR="$(pwd)"
PROJECT_ROOT="$(cd ../../ && pwd)"
PYTHON_VERSION="3.12"
PLATFORM="linux-x64"
OUTPUT_DIR="${WHEELS_DIR}"

echo "Building missing wheel for fastapi-injectable for Python ${PYTHON_VERSION} on ${PLATFORM}..."
echo "Project root: ${PROJECT_ROOT}"
echo "Output directory: ${OUTPUT_DIR}"

# Create a requirements.txt with just the package
cat > missing_requirements.txt << EOF
fastapi-injectable==0.7.0
EOF

# Run a Docker container to build the wheels
docker run --rm -v "${OUTPUT_DIR}:/wheels" -v "${OUTPUT_DIR}/missing_requirements.txt:/requirements.txt" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel -r /requirements.txt --wheel-dir=/wheels
"

# Clean up
rm -f missing_requirements.txt

echo "Done building missing wheel."
echo "The following wheel was created:"
find "${OUTPUT_DIR}" -name "fastapi_injectable*.whl" -type f -newer "${OUTPUT_DIR}/build_missing_fastapi_injectable.sh" -exec basename {} \;

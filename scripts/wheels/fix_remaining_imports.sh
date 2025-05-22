#!/bin/bash

# This script will identify and fix any remaining import dependencies
# for Python 3.12 on Linux x86_64

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="${SCRIPT_DIR}"
PYTHON_VERSION="3.12"
OUTPUT_DIR="${WHEELS_DIR}"

echo "Building additional dependencies for Python ${PYTHON_VERSION} on Linux x86_64..."

# Create a requirements file with potential missing packages
cat > remaining_imports.txt << EOF
fastapi-injectable==0.7.0
anyio>=4.0.0
starlette>=0.46.0
pydantic>=2.11.0
typing-extensions>=4.13.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0
pytest-cov>=4.1.0
pytest-xdist>=3.3.0
pytest-profiling>=1.7.0
httpx>=0.23.0
EOF

# Run a Docker container to build the wheels
docker run --rm -v "${OUTPUT_DIR}:/wheels" -v "${OUTPUT_DIR}/remaining_imports.txt:/requirements.txt" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building additional dependencies inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel -r /requirements.txt --wheel-dir=/wheels
    
    # Also check for required ARM64 wheels
    pip wheel pydantic-core==2.33.2 --wheel-dir=/wheels
    pip wheel uvicorn[standard] --wheel-dir=/wheels
    
    echo 'Additional dependencies built successfully!'
"

# Clean up
rm -f remaining_imports.txt

echo "Done building additional dependencies."
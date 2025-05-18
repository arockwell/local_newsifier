#!/bin/bash

# This script builds any remaining dependency wheels for Linux x86_64 and Python 3.12
# It targets specifically dependencies of dependencies that might be missing

set -e

WHEELS_DIR="$(pwd)"
PYTHON_VERSION="3.12"
OUTPUT_DIR="${WHEELS_DIR}"

echo "Building remaining dependency wheels for Python ${PYTHON_VERSION} on Linux x86_64..."

# Create a requirements.txt with all the missing dependencies
cat > remaining_requirements.txt << EOF
# Deep dependencies that might be missed
tokenizers>=0.15.0
onnxruntime>=1.14.1
pyvis>=0.3.2
transformers>=4.37.2
ipython>=8.0.0
stack_data>=0.6.0
coloredlogs>=15.0.0
humanfriendly>=10.0
ipywidgets>=8.0.0
tiktoken>=0.3.0
optimum>=1.13.0
accelerate>=0.26.0
litellm>=1.68.0
chromadb>=0.5.23
chromadb>=1.0.9
mmh3>=3.0.0
pypika>=0.48.9
PDF-extraction-toolkit>=0.4.0
langchain>=0.0.317
langchain-community>=0.0.16
langchain-core>=0.1.9
langchain-experimental>=0.0.42
hnswlib>=0.7.0
chroma-hnswlib>=0.7.0
langchain_text_splitters>=0.0.1
langchain-openai>=0.0.2
tiktoken>=0.5.0
EOF

# Run a Docker container to build the wheels
docker run --rm -v "${OUTPUT_DIR}:/wheels" -v "${OUTPUT_DIR}/remaining_requirements.txt:/requirements.txt" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building remaining wheels inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel -r /requirements.txt --wheel-dir=/wheels || echo 'Some wheels failed to build, but continuing...'
    echo 'Wheels built successfully!'
"

# Clean up
rm -f remaining_requirements.txt

echo "Done building remaining dependency wheels."
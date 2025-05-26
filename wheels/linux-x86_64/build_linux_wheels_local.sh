#!/bin/bash
# Build Python package wheels for Linux platforms using Docker
# Modified for Claude Code environment

set -e

# Use Python 3.12
PYTHON_VERSION="3.12"
PYTHON_VERSION_DOTLESS="312"

echo "Building all dependency wheels for Python $PYTHON_VERSION on Linux using Docker"

# Set up requirements file
REQUIREMENTS_FILE="requirements.txt"
echo "fastapi>=0.110.0
uvicorn>=0.27.0
jinja2>=3.1.3
python-multipart>=0.0.9
pydantic>=2.11.3
pydantic-settings>=2.2.1
sqlalchemy>=2.0.27
sqlmodel>=0.0.24
psycopg2-binary>=2.9.9
python-dateutil>=2.9.0
psutil==7.0.0
itsdangerous>=2.1.2
alembic>=1.13.1
celery>=5.3.6
redis>=5.0.0
spacy>=3.8.4
beautifulsoup4>=4.13.3
requests>=2.32.3
crewai>=0.114.0
tenacity>=9.1.2
textblob>=0.18.0
click>=8.1.7
tabulate>=0.9.0" > $REQUIREMENTS_FILE

# Docker build command with PostgreSQL build dependencies
DOCKER_BUILD_CMD='apt-get update && apt-get install -y build-essential libpq-dev python3-dev && pip install --upgrade pip && pip wheel -r /requirements.txt -w /wheels'

# Build for x86_64 (x64)
echo "Building wheels for Python $PYTHON_VERSION on linux-x64..."
# Use --platform to specify x86_64 architecture
docker run --rm --platform linux/amd64 \
    -v "$(pwd):/wheels" \
    -v "$(pwd)/$REQUIREMENTS_FILE:/requirements.txt" \
    python:${PYTHON_VERSION} \
    /bin/bash -c "$DOCKER_BUILD_CMD"

# Create a platform identifier file
echo "linux-x64" > .platform
echo "Python Version: $PYTHON_VERSION" > manifest.txt
echo "Platform: Linux-x86_64" >> manifest.txt
echo "Date: $(date)" >> manifest.txt
echo "Wheel Count: $(find . -name "*.whl" | wc -l)" >> manifest.txt

echo "All dependency wheels for Python $PYTHON_VERSION have been built"

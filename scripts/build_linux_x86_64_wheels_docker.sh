#!/bin/bash
# Build Linux x86_64 wheels using Docker to ensure we get the right platform

set -euo pipefail

echo "Building Linux x86_64 wheels using Docker..."

# Define wheel directory
WHEEL_DIR="wheels/py312-linux-x86_64"

# Create temporary Dockerfile
cat > /tmp/Dockerfile.wheel-builder << 'EOF'
FROM python:3.12-slim

WORKDIR /build

# Install pip tools
RUN pip install --upgrade pip wheel

# Copy requirements
COPY wheels/py312-linux-x86_64/requirements.txt /build/requirements.txt

# Download all wheels
RUN pip download \
    --platform manylinux2014_x86_64 \
    --platform manylinux_2_17_x86_64 \
    --platform manylinux_2_28_x86_64 \
    --platform linux_x86_64 \
    --python-version 312 \
    --only-binary :all: \
    --dest /wheels \
    -r requirements.txt || true

# For packages without platform-specific wheels, download any version
RUN pip download \
    --only-binary :all: \
    --dest /wheels \
    -r requirements.txt || true

# Create manifest
RUN find /wheels -name "*.whl" | sort > /wheels/manifest.txt

# Count wheels
RUN echo "Downloaded $(find /wheels -name '*.whl' | wc -l) wheel files"
EOF

echo "Building Docker image..."
docker build -f /tmp/Dockerfile.wheel-builder -t wheel-builder .

echo "Extracting wheels..."
# Create container and copy wheels out
docker create --name wheel-extract wheel-builder
docker cp wheel-extract:/wheels/. "$WHEEL_DIR/"
docker rm wheel-extract

# Cleanup
rm -f /tmp/Dockerfile.wheel-builder

# Count wheels
WHEEL_COUNT=$(find "$WHEEL_DIR" -name "*.whl" | wc -l)
echo "✅ Downloaded $WHEEL_COUNT wheel files to $WHEEL_DIR"

# Also copy our requirements.txt back if it was overwritten
if [ ! -f "$WHEEL_DIR/requirements.txt" ]; then
    grep -v "^-e" requirements.txt > "$WHEEL_DIR/requirements.txt"
fi

echo "Done!"

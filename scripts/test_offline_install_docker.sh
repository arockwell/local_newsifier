#!/bin/bash
# Test offline installation in a Docker container to ensure it works without internet

set -e

echo "=== Testing Offline Installation in Docker ==="
echo

# Define paths
WHEEL_DIR="wheels/linux-x86_64"

# Check if wheels exist
if [ ! -d "$WHEEL_DIR" ] || [ $(find "$WHEEL_DIR" -name "*.whl" | wc -l) -eq 0 ]; then
    echo "Error: No wheels found in $WHEEL_DIR"
    echo "Run 'make build-wheels-linux-x86_64' first"
    exit 1
fi

# Create Dockerfile for testing
cat > /tmp/Dockerfile.offline-test << 'EOF'
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy everything needed
COPY . .

# Disable network access (simulate offline environment)
# Note: This is a simplified approach; in practice you might use iptables
ENV PIP_NO_INDEX=1
ENV PIP_FIND_LINKS=/app/wheels/linux-x86_64

# Test installation
RUN pip install --upgrade pip && \
    pip install -r wheels/linux-x86_64/requirements.txt && \
    pip install --no-deps -e .

# Verify installation
RUN python -c "import local_newsifier; print('✅ Import successful!')"

CMD ["python", "-c", "import local_newsifier; print('Offline installation test passed!')"]
EOF

echo "Building Docker image..."
docker build -f /tmp/Dockerfile.offline-test -t local-newsifier-offline-test .

echo
echo "Running test container..."
docker run --rm local-newsifier-offline-test

echo
echo "✅ Offline installation test passed!"

# Cleanup
rm -f /tmp/Dockerfile.offline-test

echo
echo "Optional: To test interactively, run:"
echo "  docker run --rm -it local-newsifier-offline-test bash"

#!/bin/bash
# Test script for fastapi-injectable adapter

# Set environment variables for test
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=local_newsifier
export LOG_LEVEL=INFO
export SECRET_KEY=test_secret_key

# Make sure we're in the project root directory
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)
echo "Running tests from $ROOT_DIR"

# Check if we have the fastapi-injectable package installed
echo "Checking for fastapi-injectable package..."
if ! poetry run pip list | grep -q fastapi-injectable; then
    echo "Installing fastapi-injectable..."
    poetry add fastapi-injectable
fi

# First, test the standalone script
echo "Testing standalone fastapi-injectable script..."
poetry run python scripts/test_fastapi_injectable.py &
PID1=$!

# Wait for server to start
sleep 5

# Test the endpoints
echo "Testing standalone endpoints..."
curl -v http://localhost:8000/test/di 2>&1 | grep -v "curl: " || echo "Failed to connect to standalone server"
curl -v http://localhost:8000/test/article-service 2>&1 | grep -v "curl: " || echo "Failed to connect to standalone server"
curl -v http://localhost:8000/test/container 2>&1 | grep -v "curl: " || echo "Failed to connect to standalone server"

# Kill the standalone server
echo "Stopping standalone server..."
kill $PID1 2>/dev/null || true

# Now test with the full API
echo "Testing integration with main API..."
cd "$ROOT_DIR/src" && poetry run uvicorn local_newsifier.api.main:app --reload &
PID2=$!

# Wait for server to start
sleep 5

# Test the injectable endpoints
echo "Testing injectable API endpoints..."
curl -v http://localhost:8000/injectable/info 2>&1 | grep -v "curl: " || echo "Failed to connect to API server"
curl -v http://localhost:8000/injectable/stats 2>&1 | grep -v "curl: " || echo "Failed to connect to API server"

# Test regular endpoints still work
echo "Testing regular API endpoints still work..."
curl -v http://localhost:8000/health 2>&1 | grep -v "curl: " || echo "Failed to connect to API server"
curl -v http://localhost:8000/config 2>&1 | grep -v "curl: " || echo "Failed to connect to API server"

# Done
echo "Press Ctrl+C to stop the API server"
wait $PID2
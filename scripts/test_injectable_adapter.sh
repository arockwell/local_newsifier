#!/bin/bash
# Unified test script for fastapi-injectable integration

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

# Parse command line arguments
FULL_TEST=true
RUN_SERVER=false
API_INTEGRATION=false

while [ "$1" != "" ]; do
    case $1 in
        --server)
            RUN_SERVER=true
            FULL_TEST=false
            ;;
        --api-integration)
            API_INTEGRATION=true
            FULL_TEST=false
            ;;
        --all)
            FULL_TEST=true
            ;;
        *)
            echo "Unknown option: $1"
            echo "Available options: --server, --api-integration, --all"
            exit 1
            ;;
    esac
    shift
done

# Run the appropriate test mode
if [ "$FULL_TEST" = true ]; then
    echo "Running full test suite"
    poetry run python scripts/test_fastapi_injectable.py
elif [ "$RUN_SERVER" = true ]; then
    echo "Running standalone test server"
    poetry run python scripts/test_fastapi_injectable.py --server
elif [ "$API_INTEGRATION" = true ]; then
    echo "Running API integration tests"
    # First run the automated tests
    poetry run python scripts/test_fastapi_injectable.py --api-integration
    
    # Then start the API server for manual testing
    echo "Starting API server for manual tests..."
    cd "$ROOT_DIR/src" && poetry run uvicorn local_newsifier.api.main:app --reload &
    PID=$!
    
    # Wait for server to start
    sleep 5
    
    # Print test instructions
    echo ""
    echo "API server is running. Test the following endpoints:"
    echo "- http://localhost:8000/injectable/info"
    echo "- http://localhost:8000/injectable/stats"
    echo "- http://localhost:8000/health"
    echo "- http://localhost:8000/config"
    echo ""
    echo "Press Ctrl+C to stop the API server"
    
    # Wait for user to press Ctrl+C
    wait $PID
fi

echo "Tests completed"
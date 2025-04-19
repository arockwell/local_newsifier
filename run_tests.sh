#!/bin/bash
# Script to run tests with SQLite in-memory database

set -euo pipefail

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Default to running all tests
RUN_ALL=1
SPECIFIC_TEST=""

# Process command line arguments
if [ $# -gt 0 ]; then
    RUN_ALL=0
    SPECIFIC_TEST="$1"
fi

run_tests() {
    local name="$1"
    local path="$2"
    
    echo -e "${BLUE}=== Running ${name} Tests ===${NC}"
    if poetry run pytest "$path" -v; then
        echo -e "${GREEN}✓ ${name} tests passed${NC}\n"
        return 0
    else
        echo -e "${RED}✗ ${name} tests failed${NC}\n"
        return 1
    fi
}

# Run a specific test if provided
if [ $RUN_ALL -eq 0 ]; then
    echo -e "${YELLOW}Running specific test: ${SPECIFIC_TEST}${NC}"
    poetry run pytest "$SPECIFIC_TEST" -v
    exit $?
fi

# Run all tests in one go with our improved configuration
echo -e "${BLUE}=== Running All Tests ===${NC}"
if poetry run pytest -v; then
    echo -e "${GREEN}✓ All tests passed${NC}\n"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}\n"
    
    # Run individual test modules to identify which ones are failing
    echo -e "${YELLOW}Running tests by module to identify failures:${NC}\n"
    
    failed_groups=()
    
    # Run each test module
    if ! run_tests "Config" "tests/config/"; then
        failed_groups+=("Config")
    fi
    
    if ! run_tests "CRUD" "tests/crud/"; then
        failed_groups+=("CRUD")
    fi
    
    if ! run_tests "Flow" "tests/flows/"; then
        failed_groups+=("Flow")
    fi
    
    if ! run_tests "Model" "tests/models/"; then
        failed_groups+=("Model")
    fi
    
    if ! run_tests "Tools" "tests/tools/"; then
        failed_groups+=("Tools")
    fi
    
    echo -e "${RED}The following test groups failed:${NC}"
    for group in "${failed_groups[@]}"; do
        echo -e "${RED}- ${group}${NC}"
    done
    exit 1
fi
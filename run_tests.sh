#!/bin/bash
# Script to run tests with improved SQLModel configuration

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

run_test_group() {
    local group_name="$1"
    local path="$2"
    
    echo -e "${BLUE}=== Running ${group_name} Tests ===${NC}"
    if poetry run pytest "$path" -v; then
        echo -e "${GREEN}✓ ${group_name} tests passed${NC}\n"
        return 0
    else
        echo -e "${RED}✗ ${group_name} tests failed${NC}\n"
        return 1
    fi
}

# Run a specific test if provided
if [ $RUN_ALL -eq 0 ]; then
    echo -e "${YELLOW}Running specific test: ${SPECIFIC_TEST}${NC}"
    poetry run pytest "$SPECIFIC_TEST" -v
    exit $?
fi

# Otherwise run all test groups
failed_groups=()

# Run each test module
if ! run_test_group "Config" "tests/config/"; then
    failed_groups+=("Config")
fi

if ! run_test_group "Flow" "tests/flows/"; then
    failed_groups+=("Flow")
fi

if ! run_test_group "CRUD" "tests/crud/"; then
    failed_groups+=("CRUD")
fi

if ! run_test_group "Model" "tests/models/"; then
    failed_groups+=("Model")
fi

if ! run_test_group "Tools" "tests/tools/"; then
    failed_groups+=("Tools")
fi

# Summary
echo -e "${BLUE}=== Test Summary ===${NC}"

if [ ${#failed_groups[@]} -eq 0 ]; then
    echo -e "${GREEN}All tests executed successfully!${NC}"
    echo -e "${BLUE}With our new test configuration, we can now run tests in a single command:${NC}"
    echo -e "${YELLOW}poetry run pytest${NC}"
    exit 0
else
    echo -e "${RED}The following test groups failed:${NC}"
    for group in "${failed_groups[@]}"; do
        echo -e "${RED}- ${group}${NC}"
    done
    exit 1
fi
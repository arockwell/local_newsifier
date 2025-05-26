#!/bin/bash
# Verify that all required wheels are present for offline installation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if a platform directory is specified
if [ $# -eq 0 ]; then
    echo "Usage: $0 <platform-directory>"
    echo "Example: $0 wheels/py312-linux-x86_64"
    exit 1
fi

WHEEL_DIR="$1"

if [ ! -d "$WHEEL_DIR" ]; then
    echo -e "${RED}Error: Directory $WHEEL_DIR does not exist${NC}"
    exit 1
fi

echo "Verifying wheels in $WHEEL_DIR..."
echo

# Function to check if a wheel exists for a package
check_wheel() {
    local package="$1"
    local normalized_name="${package//_/-}"

    if find "$WHEEL_DIR" -name "${package}-*.whl" -o -name "${normalized_name}-*.whl" | grep -q .; then
        echo -e "${GREEN}✓${NC} $package"
        return 0
    else
        echo -e "${RED}✗${NC} $package"
        return 1
    fi
}

# Track missing packages
MISSING_RUNTIME=()
MISSING_DEV=()

# Check runtime dependencies
echo "Checking runtime dependencies..."
while IFS= read -r line; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^# ]] && continue

    # Extract package name (handle different requirement formats)
    package=$(echo "$line" | sed -E 's/([a-zA-Z0-9_-]+).*/\1/')

    if ! check_wheel "$package"; then
        MISSING_RUNTIME+=("$package")
    fi
done < <(grep -v "^-e" requirements.txt 2>/dev/null || echo "")

echo

# Check development dependencies
echo "Checking development dependencies..."
if [ -f "requirements-dev.txt" ]; then
    while IFS= read -r line; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^# ]] && continue

        # Extract package name
        package=$(echo "$line" | sed -E 's/([a-zA-Z0-9_-]+).*/\1/')

        if ! check_wheel "$package"; then
            MISSING_DEV+=("$package")
        fi
    done < requirements-dev.txt
else
    echo -e "${YELLOW}Warning: requirements-dev.txt not found${NC}"
fi

echo

# Special check for coverage (needed by pytest-cov)
echo "Checking critical sub-dependencies..."
check_wheel "coverage"

echo
echo "Summary:"
echo "--------"

TOTAL_WHEELS=$(find "$WHEEL_DIR" -name "*.whl" | wc -l)
echo "Total wheels found: $TOTAL_WHEELS"

if [ ${#MISSING_RUNTIME[@]} -eq 0 ] && [ ${#MISSING_DEV[@]} -eq 0 ]; then
    echo -e "${GREEN}All required dependencies are present!${NC}"
    exit 0
else
    if [ ${#MISSING_RUNTIME[@]} -gt 0 ]; then
        echo -e "${RED}Missing runtime dependencies:${NC}"
        printf '%s\n' "${MISSING_RUNTIME[@]}"
    fi

    if [ ${#MISSING_DEV[@]} -gt 0 ]; then
        echo -e "${RED}Missing development dependencies:${NC}"
        printf '%s\n' "${MISSING_DEV[@]}"
    fi

    echo
    echo -e "${YELLOW}To download missing wheels, run:${NC}"
    echo "pip download --platform <platform> --python-version 312 --only-binary :all: --dest $WHEEL_DIR <package-name>"

    exit 1
fi

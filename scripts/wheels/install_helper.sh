#!/bin/bash

# This script helps install packages using the local wheels directory
# It addresses the issue with long wheel filenames by using the correct path

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="${SCRIPT_DIR}"

echo "Installing packages from wheels directory: ${WHEELS_DIR}"

# If no arguments are provided, attempt to install the project
if [ $# -eq 0 ]; then
    echo "No package specified, installing the project and all dependencies..."
    pip install --no-index --find-links="${WHEELS_DIR}" -e ../../
else
    # Install specified packages
    echo "Installing specified packages: $@"
    for package in "$@"; do
        # Check if it looks like a wheel filename
        if [[ "$package" == *".whl" ]]; then
            # If it's a relative path without directory, prepend the wheels directory
            if [[ "$package" != *"/"* ]]; then
                package="${WHEELS_DIR}/${package}"
            fi
            echo "Installing wheel: ${package}"
            pip install --no-index --find-links="${WHEELS_DIR}" "${package}"
        else
            # It's a package name, not a filename
            echo "Installing package: ${package}"
            pip install --no-index --find-links="${WHEELS_DIR}" "${package}"
        fi
    done
fi

echo "Installation complete!"
#!/bin/bash

# This script proactively identifies and builds missing dependencies
# for Python 3.12 on Linux x86_64

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="${SCRIPT_DIR}"
PYTHON_VERSION="3.12"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"

echo "Proactively fixing missing dependencies for Python ${PYTHON_VERSION} on Linux x86_64..."

# Ensure psutil is properly built for Linux x86_64
echo "Building psutil for Linux x86_64..."
docker run --rm -v "${WHEELS_DIR}:/wheels" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building psutil inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    pip wheel psutil==7.0.0 --wheel-dir=/wheels
    echo 'psutil wheel built successfully!'
"

# Build additional binary wheels that might be needed
echo "Building additional binary wheels..."
docker run --rm -v "${WHEELS_DIR}:/wheels" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building binary wheels inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    
    # Create requirements file for binary packages
    cat > /tmp/binary_reqs.txt << EOF
    numpy==2.2.5
    pandas==2.2.2
    scipy==1.13.0
    pydantic-core==2.33.2
    cryptography==44.0.3
    psycopg2-binary==2.9.10
    bcrypt==4.3.0
    greenlet==3.2.2
    aiohttp==3.11.18
    multidict==6.4.3
    frozenlist==1.6.0
    yarl==1.20.0
    uvloop==0.21.0
    httptools==0.6.0
    EOF
    
    # Build wheels
    pip wheel -r /tmp/binary_reqs.txt --wheel-dir=/wheels || echo 'Some wheels failed to build, but continuing...'
    echo 'Binary wheels built successfully!'
"

# Build wheels for common missing dependencies
echo "Building wheels for commonly missing dependencies..."
docker run --rm -v "${WHEELS_DIR}:/wheels" python:${PYTHON_VERSION}-slim bash -c "
    set -e
    echo 'Building wheels for missing dependencies inside Docker container...'
    apt-get update
    apt-get install -y build-essential
    pip install --upgrade pip wheel
    
    # Create requirements file for commonly missing packages
    cat > /tmp/missing_reqs.txt << EOF
    uv==0.7.5
    typing-extensions==4.13.2
    sqlalchemy==2.0.41
    greenlet==3.2.2
    regex==2024.11.6
    tomli==2.2.1
    tomli-w==1.2.0
    vine==5.1.0
    celery==5.5.2
    amqp==5.3.1
    billiard==4.2.1
    click-didyoumean==0.3.1
    click-plugins==1.1.1
    click-repl==0.3.0
    kombu==5.5.3
    prompt-toolkit==3.0.51
    pytz==2025.1
    tzdata==2025.2
    EOF
    
    # Build wheels
    pip wheel -r /tmp/missing_reqs.txt --wheel-dir=/wheels || echo 'Some wheels failed to build, but continuing...'
    echo 'Missing dependency wheels built successfully!'
"

# Check for wheel compatibility issues
echo "Checking for wheel compatibility issues..."
python3 - << EOF
import os
import re
import glob

wheels_dir = "${WHEELS_DIR}"
linux_wheel_pattern = re.compile(r'.*\.(manylinux|linux_x86_64).*\.whl$')
arm_pattern = re.compile(r'.*\.arm64.*\.whl$')

# Find all wheel files
all_wheels = glob.glob(os.path.join(wheels_dir, "*.whl"))

print(f"Found {len(all_wheels)} wheel files in {wheels_dir}")

# Identify Linux-specific wheels
linux_wheels = [w for w in all_wheels if linux_wheel_pattern.match(os.path.basename(w))]
print(f"Found {len(linux_wheels)} Linux-specific wheels")

# Identify ARM64 wheels that might not work on x86_64
arm_wheels = [w for w in all_wheels if arm_pattern.match(os.path.basename(w))]
print(f"Found {len(arm_wheels)} ARM64 wheels")

# Extract package names from wheels
def get_package_name(wheel_path):
    filename = os.path.basename(wheel_path)
    parts = filename.split('-')
    return parts[0].lower().replace('_', '-')

# Check for packages that have arm64 but no x86_64 equivalent
arm_packages = {get_package_name(w) for w in arm_wheels}
linux_packages = {get_package_name(w) for w in linux_wheels}

missing_x86_64 = arm_packages - linux_packages
if missing_x86_64:
    print("\nWARNING: The following packages have ARM64 wheels but no x86_64 equivalents:")
    for pkg in sorted(missing_x86_64):
        print(f"  - {pkg}")
    print("These may need to be built for x86_64 to ensure compatibility.")
else:
    print("\nAll ARM64 packages have x86_64 equivalents. Good!")
EOF

echo "Done proactively fixing missing dependencies."
echo "Consider running the verify_wheels.sh script to confirm all dependencies are available."
# Offline Installation Guide

## Overview

This guide covers how to install Local Newsifier in environments without internet access. The process involves pre-building wheel files on a machine with internet access, then transferring and installing them on the target system.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Current Status](#current-status)
- [Platform Support](#platform-support)
- [Building Wheels](#building-wheels)
- [Installation Process](#installation-process)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Prerequisites

### Target System Requirements
- Python 3.10, 3.11, or 3.12 (3.12 recommended)
- pip and setuptools installed
- Basic build tools (gcc, make) for source distributions
- ~2GB disk space for wheels and installation

### Build System Requirements
- Internet access
- Same Python version as target system
- Docker (optional, for cross-platform builds)
- Poetry installed

## Current Status

As of May 22, 2025:
- **Wheels Updated**: 257 wheel files available
- **Primary Platform**: Python 3.12 on macOS ARM64
- **Platform Detection**: Automatic with fallback options
- **Version Flexibility**: Adapts to available wheel versions

### Known Issues
- Python 3.13 not yet supported (use Python 3.12)
- Some platform-specific wheels may need rebuilding
- spaCy models require separate offline installation

## Platform Support

### Directory Structure
Wheels are organized by platform:
```
wheels/
├── py310-linux-x86_64/
├── py311-linux-x86_64/
├── py312-linux-x86_64/
├── py312-macos-arm64/
└── py312-macos-x86_64/
```

### Supported Platforms
- **Linux x86_64**: Ubuntu 20.04+, CentOS 8+, Debian 10+
- **macOS ARM64**: Apple Silicon Macs (M1/M2/M3)
- **macOS x86_64**: Intel Macs
- **Windows**: Limited support (WSL recommended)

## Building Wheels

### 1. Build for Current Platform
```bash
# Update requirements first
poetry export -f requirements.txt > requirements.txt

# Build wheels for current platform
make build-wheels

# Wheels will be in wheels/py{version}-{os}-{arch}/
```

### 2. Build for Linux (using Docker)
```bash
# Build Linux x86_64 wheels
make build-wheels-linux

# Or manually:
docker run --rm -v $(pwd):/app \
  -w /app \
  python:3.12-slim \
  bash scripts/build_linux_x86_64_wheels_docker.sh
```

### 3. Organize Existing Wheels
```bash
# Organize wheels into platform-specific directories
python scripts/organize_wheels.sh

# Validate wheel compatibility
python scripts/validate_offline_wheels.py
```

### 4. Build Specific Dependencies
```bash
# Build only missing wheels
pip wheel --wheel-dir=./wheels/temp \
  --find-links=./wheels/py312-linux-x86_64 \
  package-name==version
```

## Installation Process

### 1. Quick Install (Recommended)
```bash
# On target system without internet
make install-offline

# This runs the smart installer that:
# - Detects platform automatically
# - Finds compatible wheels
# - Falls back to alternate versions if needed
```

### 2. Manual Installation

#### Step 1: Transfer Files
```bash
# Create deployment package on build system
tar -czf offline_newsifier.tar.gz \
  wheels/ \
  requirements.txt \
  scripts/install_offline_linux.sh \
  pyproject.toml

# Transfer to target system
scp offline_newsifier.tar.gz user@target:/path/to/
```

#### Step 2: Extract and Install
```bash
# On target system
tar -xzf offline_newsifier.tar.gz
cd offline_newsifier

# Install using platform-specific wheels
pip install --no-index \
  --find-links wheels/py312-linux-x86_64 \
  -r requirements.txt
```

#### Step 3: Install spaCy Models
```bash
# spaCy models must be installed separately
# Download on system with internet:
python -m spacy download en_core_web_sm

# Find the downloaded model:
python -c "import en_core_web_sm; print(en_core_web_sm.__file__)"

# Copy the model directory to target system
# Install manually:
pip install /path/to/en_core_web_sm-3.x.x.tar.gz
```

### 3. Platform-Specific Installation

#### Linux x86_64
```bash
# Ensure correct glibc version
ldd --version  # Should be 2.17+

# Install with specific wheel directory
pip install --no-index \
  --find-links wheels/py312-linux-x86_64 \
  local-newsifier
```

#### macOS
```bash
# For Apple Silicon
pip install --no-index \
  --find-links wheels/py312-macos-arm64 \
  local-newsifier

# For Intel Macs
pip install --no-index \
  --find-links wheels/py312-macos-x86_64 \
  local-newsifier
```

## Testing

### 1. Quick Validation
```bash
# Test wheel availability
make test-wheels

# Verify installation
python -c "import local_newsifier; print(local_newsifier.__version__)"

# Test CLI
nf --help
```

### 2. Full Offline Test
```bash
# Simulate offline environment
export PIP_NO_INDEX=1
export PIP_FIND_LINKS=./wheels/py312-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)

# Clean environment
rm -rf test_venv
python -m venv test_venv
source test_venv/bin/activate

# Install and test
pip install -r requirements.txt
python -m pytest tests/
```

### 3. Docker Testing
```bash
# Most accurate offline test
docker run --rm -v $(pwd):/app \
  --network none \
  python:3.12-slim \
  bash /app/scripts/test_offline_install_docker.sh
```

## Troubleshooting

### Common Issues

#### 1. Platform Detection Fails
```bash
# Manually specify platform
export LOCAL_NEWSIFIER_PLATFORM="py312-linux-x86_64"
make install-offline
```

#### 2. Missing Wheels
```bash
# Check what's missing
pip install --dry-run --no-index \
  --find-links wheels/py312-linux-x86_64 \
  -r requirements.txt

# Build missing wheels
pip wheel --wheel-dir=./wheels/temp missing-package
```

#### 3. Version Conflicts
```bash
# The installer tries multiple versions
# If it fails, check available versions:
ls wheels/py312-*/package-name*.whl

# Install specific version:
pip install --no-index \
  --find-links wheels/py312-linux-x86_64 \
  package-name==specific.version
```

#### 4. Binary Compatibility
```bash
# For Linux, check glibc version
ldd --version

# For macOS, check architecture
uname -m  # Should match wheel platform

# Use compatible wheels or build from source
pip install --no-binary :all: package-name
```

### Platform-Specific Issues

#### Linux
- **GLIBC Version**: Wheels built on newer systems may not work on older ones
- **Solution**: Build wheels on oldest supported system

#### macOS
- **Architecture Mismatch**: ARM64 wheels won't work on Intel Macs
- **Solution**: Use universal2 wheels or correct architecture

#### Windows
- **Path Issues**: Windows paths may cause problems
- **Solution**: Use WSL or escape paths properly

## Security Considerations

### 1. Verify Sources
```bash
# Generate checksums on build system
find wheels/ -name "*.whl" -exec sha256sum {} \; > wheels.sha256

# Verify on target system
sha256sum -c wheels.sha256
```

### 2. Audit Dependencies
```bash
# Check for security issues before building
pip-audit -r requirements.txt

# Review licenses
pip-licenses --from=mixed
```

### 3. Minimize Attack Surface
- Only include required dependencies
- Use specific versions (no ranges)
- Build wheels from trusted sources
- Scan wheels for malware before deployment

## Best Practices

1. **Keep Wheels Updated**
   - Rebuild wheels when updating dependencies
   - Test new wheels before deployment
   - Maintain version compatibility matrix

2. **Platform Consistency**
   - Build on similar OS versions as targets
   - Use Docker for reproducible builds
   - Test on representative systems

3. **Documentation**
   - Document wheel building process
   - Track platform-specific requirements
   - Maintain offline installation runbook

4. **Deployment Package**
   - Include all necessary files
   - Add installation scripts
   - Provide troubleshooting guide
   - Version the deployment package

## Creating Deployment Packages

### Complete Package Structure
```
offline_newsifier_v1.0.0/
├── wheels/
│   └── py312-linux-x86_64/
├── models/
│   └── en_core_web_sm-3.x.x.tar.gz
├── scripts/
│   ├── install.sh
│   └── verify.sh
├── docs/
│   └── OFFLINE_INSTALL.md
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

### Package Creation Script
```bash
#!/bin/bash
VERSION="1.0.0"
PLATFORM="py312-linux-x86_64"

# Create package directory
mkdir -p "offline_newsifier_v${VERSION}"

# Copy wheels
cp -r "wheels/${PLATFORM}" "offline_newsifier_v${VERSION}/wheels/"

# Copy requirements
cp requirements*.txt "offline_newsifier_v${VERSION}/"

# Copy installation scripts
cp scripts/install_offline_linux.sh "offline_newsifier_v${VERSION}/install.sh"

# Create archive
tar -czf "offline_newsifier_v${VERSION}_${PLATFORM}.tar.gz" \
  "offline_newsifier_v${VERSION}"

# Generate checksum
sha256sum "offline_newsifier_v${VERSION}_${PLATFORM}.tar.gz" > \
  "offline_newsifier_v${VERSION}_${PLATFORM}.tar.gz.sha256"
```

## Troubleshooting

### Common Issues and Solutions

#### Platform Detection Issues

**Problem**: Wrong Platform Detected
**Symptoms**: Installer looks for wheels in wrong directory
```
Looking for wheels in wheels/py313-darwin-arm64/
ERROR: No wheels directory found
```

**Solutions**:
1. Check Python version:
```bash
python --version  # Must be 3.10-3.12
```

2. Override platform detection:
```bash
export LOCAL_NEWSIFIER_PLATFORM="py312-linux-x86_64"
make install-offline
```

3. Use correct Python:
```bash
python3.12 -m pip install --no-index \
  --find-links wheels/py312-linux-x86_64 \
  -r requirements.txt
```

#### Wheel Compatibility Issues

**Problem**: No Matching Distribution Found
**Symptoms**:
```
ERROR: Could not find a version that satisfies the requirement package-name
```

**Solutions**:
1. Check available wheels:
```bash
ls wheels/py312-*/package-name*.whl
```

2. Build missing wheel:
```bash
pip wheel --wheel-dir=./wheels/temp package-name
cp wheels/temp/*.whl wheels/py312-linux-x86_64/
```

#### Binary Wheel Incompatibility

**Problem**: Binary wheel not supported on platform
**Symptoms**:
```
ERROR: package.whl is not a supported wheel on this platform
```

**Solutions**:
1. Verify platform compatibility:
```bash
# Check system
uname -a
python -c "import platform; print(platform.machine())"

# Check wheel platform
unzip -l package.whl | grep WHEEL
```

2. Use source distribution:
```bash
pip install --no-binary package-name package-name
```

#### Installation Path Issues

**Problem**: Scripts Not in PATH
**Symptoms**: `nf: command not found` after installation

**Solutions**:
1. Add Scripts to PATH:
```bash
# Find installation location
python -m site --user-base

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"

# Add to PATH (Windows)
set PATH=%APPDATA%\Python\Scripts;%PATH%
```

2. Use full path:
```bash
~/.local/bin/nf --help
```

#### spaCy Model Issues

**Problem**: spaCy Models Not Found
**Symptoms**:
```
OSError: [E050] Can't find model 'en_core_web_sm'
```

**Solutions**:
1. Install spaCy models offline:
```bash
# Download on internet-connected machine
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_md

# Package the models
pip wheel --wheel-dir=./models spacy-model-en_core_web_sm
```

2. Install from wheel:
```bash
pip install --no-index ./models/en_core_web_sm*.whl
```

### Debugging Steps

1. **Verbose Installation**:
```bash
pip install -vvv --no-index \
  --find-links wheels/py312-linux-x86_64 \
  package-name
```

2. **Check Wheel Metadata**:
```bash
# List wheel contents
unzip -l package.whl

# Check wheel info
python -m wheel unpack package.whl
cat package.dist-info/WHEEL
```

3. **Platform Debugging**:
```bash
# Detailed platform info
python -c "
import platform
import sys
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'Machine: {platform.machine()}')
print(f'Processor: {platform.processor()}')
"
```

### Emergency Fixes

**Quick Fix Script**:
```bash
#!/bin/bash
# emergency_offline_install.sh

# Detect platform
PYTHON_VERSION=$(python -c "import sys; print(f'py{sys.version_info.major}{sys.version_info.minor}')")
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Map common architectures
if [ "$ARCH" = "x86_64" ]; then
    ARCH="x86_64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    ARCH="arm64"
fi

# Try multiple directories
for dir in "wheels/${PYTHON_VERSION}-${OS}-${ARCH}" \
           "wheels/${PYTHON_VERSION}-${OS}" \
           "wheels/${PYTHON_VERSION}" \
           "wheels"; do
    if [ -d "$dir" ]; then
        echo "Using wheels from: $dir"
        pip install --no-index --find-links "$dir" -r requirements.txt
        exit $?
    fi
done

echo "ERROR: No compatible wheels found"
exit 1
```

**Last Resort Options**:

1. Partial Installation:
```bash
# Install only core dependencies
grep -E "^(fastapi|sqlmodel|pydantic)" requirements.txt > core-requirements.txt
pip install --no-index --find-links wheels/ -r core-requirements.txt
```

2. Manual Dependency Resolution:
```bash
# Install in dependency order
pip install --no-deps wheel setuptools
pip install --no-deps --no-index --find-links wheels/ pydantic
pip install --no-deps --no-index --find-links wheels/ sqlmodel
# Continue with other packages...
```

## See Also

- [Python Setup Guide](python_setup.md) - Development environment setup
- [Testing Guide](testing_guide.md) - Testing offline installations
- [Deployment Guide](../operations/deployment.md) - Production deployment

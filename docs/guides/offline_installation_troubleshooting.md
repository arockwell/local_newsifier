# Offline Installation Troubleshooting

## Common Issues and Solutions

### Platform Detection Issues

#### Problem: Wrong Platform Detected
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

### Wheel Compatibility Issues

#### Problem: No Matching Distribution Found
**Symptoms**:
```
ERROR: Could not find a version that satisfies the requirement package-name
```

**Solutions**:
1. Check available wheels:
```bash
ls wheels/py312-*/package-name*.whl
```

2. Try alternate versions:
```bash
# The installer attempts these automatically:
# 1. Exact version from requirements.txt
# 2. Any version of the package
# 3. Skip non-critical packages
```

3. Build missing wheel:
```bash
pip wheel --wheel-dir=./wheels/temp package-name
cp wheels/temp/*.whl wheels/py312-linux-x86_64/
```

#### Problem: Binary Wheel Incompatibility
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

### Installation Path Issues

#### Problem: Scripts Not in PATH
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

### Dependency Resolution Issues

#### Problem: Version Conflicts
**Symptoms**:
```
ERROR: Cannot install package-a and package-b because these package versions have conflicting dependencies
```

**Solutions**:
1. Check requirements compatibility:
```bash
# Generate fresh requirements
poetry lock
poetry export -f requirements.txt > requirements.txt
```

2. Install with relaxed constraints:
```bash
# Create temporary requirements without versions
cat requirements.txt | cut -d'=' -f1 > requirements-no-versions.txt
pip install --no-index --find-links wheels/ -r requirements-no-versions.txt
```

### spaCy Model Issues

#### Problem: spaCy Models Not Found
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

3. Link manually:
```bash
python -m spacy link /path/to/en_core_web_sm en_core_web_sm
```

### Mixed Architecture Issues

#### Problem: Mixed Wheels in Directory
**Symptoms**: Some packages install, others fail with platform errors

**Solutions**:
1. Clean up mixed wheels:
```bash
# Remove non-matching architectures
find wheels/py312-linux-x86_64 -name "*-macosx*.whl" -delete
find wheels/py312-linux-x86_64 -name "*-win*.whl" -delete
```

2. Validate wheel directory:
```bash
python scripts/validate_offline_wheels.py wheels/py312-linux-x86_64
```

### Build Tool Issues

#### Problem: Missing Build Dependencies
**Symptoms**:
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solutions**:
1. Install build tools:
```bash
# Linux
sudo apt-get install build-essential python3-dev

# macOS
xcode-select --install

# Windows
# Install Visual Studio Build Tools
```

2. Use pre-built wheels only:
```bash
pip install --only-binary :all: --no-index \
  --find-links wheels/ -r requirements.txt
```

## Debugging Steps

### 1. Verbose Installation
```bash
pip install -vvv --no-index \
  --find-links wheels/py312-linux-x86_64 \
  package-name
```

### 2. Check Wheel Metadata
```bash
# List wheel contents
unzip -l package.whl

# Check wheel info
python -m wheel unpack package.whl
cat package.dist-info/WHEEL
```

### 3. Test Individual Packages
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Test each package
for wheel in wheels/py312-linux-x86_64/*.whl; do
    pip install --no-deps "$wheel" || echo "Failed: $wheel"
done
```

### 4. Platform Debugging
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

# Check GLIBC version (Linux)
ldd --version

# Check macOS version
sw_vers
```

## Prevention Strategies

### 1. Standardize Wheel Building
- Always build on the oldest supported OS version
- Use Docker for consistent builds
- Document build environment

### 2. Regular Testing
- Test offline installation weekly
- Automate with CI/CD
- Test on multiple platforms

### 3. Wheel Organization
- One platform per directory
- Clear naming conventions
- Remove obsolete wheels

### 4. Documentation
- Keep platform matrix updated
- Document known issues
- Maintain compatibility notes

## Emergency Fixes

### Quick Fix Script
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

### Last Resort Options

1. **Partial Installation**:
```bash
# Install only core dependencies
grep -E "^(fastapi|sqlmodel|pydantic)" requirements.txt > core-requirements.txt
pip install --no-index --find-links wheels/ -r core-requirements.txt
```

2. **Source Installation**:
```bash
# If wheels fail, try source distributions
pip install --no-binary :all: --no-index \
  --find-links wheels/ package-name
```

3. **Manual Dependency Resolution**:
```bash
# Install in dependency order
pip install --no-deps wheel setuptools
pip install --no-deps --no-index --find-links wheels/ pydantic
pip install --no-deps --no-index --find-links wheels/ sqlmodel
# Continue with other packages...
```

## Getting Help

If issues persist:
1. Check the [GitHub Issues](https://github.com/anthropics/local-newsifier/issues)
2. Review the [main installation guide](offline_installation.md)
3. Contact support with:
   - Platform details (`uname -a`, `python --version`)
   - Error messages
   - List of wheels directory contents
   - Installation commands used

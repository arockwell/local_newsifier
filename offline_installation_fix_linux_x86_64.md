# Linux x86_64 Offline Installation Fix

**Status**: Resolved
**Date**: 2025-05-26
**Issue**: Missing coverage wheel preventing offline test execution

## Issue Summary

The offline installation test failed on Linux x86_64 because the `coverage` wheel is missing from the `wheels/py312-linux-x86_64/` directory. This prevents the installation of `pytest-cov`, which depends on `coverage`.

## Failure Details

From `linxu_x86_64_failure.txt`:

1. Poetry setup failed initially due to missing `poetry-core` package
2. Runtime dependencies installed successfully using platform-specific directory:
   ```bash
   poetry run pip install --no-index --find-links=wheels/py312-linux-x64 -r requirements.txt
   ```
3. Development dependencies installation failed:
   ```bash
   poetry run pip install --no-index --find-links=wheels/py312-linux-x64 -r requirements-dev.txt
   ```
   Error: Missing `coverage` wheel needed by `pytest-cov`

## Current State

### Coverage Wheel Availability
- ✅ Linux aarch64: `coverage-7.8.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl`
- ✅ macOS arm64: `coverage-7.8.1-cp312-cp312-macosx_11_0_arm64.whl`
- ❌ Linux x86_64: **MISSING**

### Other Development Dependencies Status
All other development dependencies appear to be present in the Linux x86_64 directory:
- pytest
- pytest-mock
- pytest-asyncio
- pre-commit
- black
- isort
- flake8
- flake8-docstrings
- pytest-profiling
- pytest-xdist

## Solution

We need to build and add the `coverage` wheel for Linux x86_64 (Python 3.12):

1. **Immediate Fix**: Download or build `coverage` wheel for Linux x86_64:
   ```bash
   # Expected filename pattern:
   coverage-7.8.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
   # or
   coverage-7.8.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
   ```

2. **Build Script Update**: Update the Linux wheel building scripts to ensure `coverage` is included

3. **Validation**: After adding the wheel, verify the installation works:
   ```bash
   poetry run pip install --no-index --find-links=wheels/py312-linux-x86_64 -r requirements-dev.txt
   poetry run pytest --version
   ```

## Next Steps

1. Check if there's a build script in the `wheels/py312-linux-x86_64/` directory that needs updating
2. Build or download the missing `coverage` wheel
3. Test the offline installation process again
4. Update any build automation to prevent this issue in the future

## Implementation

### Script Created

A new script has been created at `scripts/build_missing_coverage_wheel.sh` to download the missing coverage wheel:

```bash
#!/bin/bash
# This script downloads the coverage wheel for Linux x86_64
chmod +x scripts/build_missing_coverage_wheel.sh
./scripts/build_missing_coverage_wheel.sh
```

### Long-term Fix

The root cause is that the main build script `scripts/build_linux_x86_64_wheels.sh` only processes runtime dependencies from `requirements.txt`, not development dependencies from `requirements-dev.txt`.

To prevent this issue in the future, we should:

1. **Update the main build script** to also process `requirements-dev.txt`:
   ```bash
   # In scripts/build_linux_x86_64_wheels.sh, after processing requirements.txt:
   if [ -f "requirements-dev.txt" ]; then
       pip download \
           --platform manylinux2014_x86_64 \
           --platform manylinux_2_17_x86_64 \
           --python-version 312 \
           --only-binary :all: \
           --dest "$WHEEL_DIR" \
           -r requirements-dev.txt || true
   fi
   ```

2. **Create a comprehensive wheel verification script** that checks both runtime and dev dependencies are present

3. **Update the CI/CD pipeline** to run wheel verification after building

## Verification

After adding the coverage wheel, verify the fix:

```bash
# Test the offline installation
cd /path/to/project
poetry env use python3.12
poetry run pip install --no-index --find-links=wheels/py312-linux-x86_64 -r requirements.txt
poetry run pip install --no-index --find-links=wheels/py312-linux-x86_64 -r requirements-dev.txt
poetry run pytest --version
```

## Scripts Created

1. **`scripts/build_missing_coverage_wheel.sh`** - Quick fix to download just the missing coverage wheel
2. **`scripts/build_linux_x86_64_wheels_complete.sh`** - Improved build script that includes dev dependencies
3. **`scripts/verify_offline_wheels.sh`** - Verification script to check all dependencies are present

## Resolution Summary

The issue was caused by the build process only downloading runtime dependencies, not development dependencies. The immediate fix is to run `scripts/build_missing_coverage_wheel.sh` to add the coverage wheel. The long-term fix is to use the improved build script that handles both runtime and development dependencies.

To apply the fix:
```bash
# Quick fix - download just the missing coverage wheel
./scripts/build_missing_coverage_wheel.sh

# Or rebuild all wheels including dev dependencies
./scripts/build_linux_x86_64_wheels_complete.sh

# Verify all dependencies are present
./scripts/verify_offline_wheels.sh wheels/py312-linux-x86_64
```

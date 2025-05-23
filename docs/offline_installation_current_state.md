# Offline Installation - Current State

This document summarizes the current state of offline installation as of the latest fixes.

## What Works

1. **Platform Detection** ✅
   - Automatically detects Python version, OS, and architecture
   - Correctly finds platform-specific wheel directories
   - Falls back to version-only directories when needed

2. **Version Flexibility** ✅
   - New `generate_offline_requirements.py` script adjusts versions
   - Matches available wheels instead of failing on exact versions
   - Shows which versions were adjusted

3. **Error Messages** ✅
   - Clear messages about missing directories
   - Lists available wheel directories on failure
   - Helpful guidance on next steps

## Current Issues

### 1. Outdated Wheels
**Problem**: The wheels in the repository are outdated compared to current dependencies.

**Example**:
- Project needs: `chromadb==1.0.9`, `fastapi==0.115.9`
- Wheels have: `chromadb==0.6.3`, `fastapi==0.112.4`

**Solution**: Rebuild wheels with current dependencies
```bash
poetry shell  # Use Poetry environment to avoid system Python issues
make build-wheels
```

### 2. Python Version Mismatch
**Problem**: System Python (3.13) vs Project Python (3.12)

**Solution**: Use explicit Python version
```bash
PYTHON=python3.12 make install-offline
```

### 3. Incomplete Platform Coverage
**Problem**: Some platform directories have very few wheels (e.g., `py313-macos-arm64` only has 1 wheel)

**Solution**: Build wheels for each Python version you need to support

## How to Test Offline Installation

### Quick Test (Recommended)
```bash
# 1. Ensure you have current wheels
poetry shell
make build-wheels

# 2. Test with explicit Python version
PYTHON=python3.12 make test-wheels
```

### Manual Test
```bash
# 1. Use the correct Python version
PYTHON=python3.12 make install-offline

# 2. If it fails, check which wheels directory was used
# Look for "Using platform-specific wheels: ..." in output

# 3. Verify that directory has all needed wheels
ls -la wheels/py312-macos-arm64/ | wc -l  # Should be 200+ files
```

## Best Practices Going Forward

1. **Keep Wheels Updated**
   - Rebuild wheels whenever dependencies change
   - Test offline installation after rebuilding
   - Commit updated wheels to repository

2. **Use Poetry Environment**
   - Always use `poetry shell` before building wheels
   - This ensures correct Python version and avoids system package conflicts

3. **Test Multiple Platforms**
   - Build wheels on each target platform
   - Or use Docker for Linux wheels: `make build-wheels-linux`

4. **Document Python Version**
   - Project requires Python 3.12.10 (specified in pyproject.toml)
   - Ensure this is clearly communicated to users

## Verification Steps

After offline installation, verify:
```bash
# 1. Check Poetry environment
poetry env info

# 2. Test imports
poetry run python -c "import local_newsifier; print('✓ Package installed')"
poetry run python -c "import fastapi; print('✓ FastAPI installed')"
poetry run python -c "import sqlalchemy; print('✓ SQLAlchemy installed')"

# 3. Run a simple test
poetry run pytest tests/models/test_base_state.py -v
```

## Troubleshooting Commands

```bash
# See what's in your wheels directory
fd -e whl . wheels/ | wc -l  # Count total wheels
fd -e whl . wheels/py312-macos-arm64/ | wc -l  # Count platform-specific

# Check for specific package
fd "chromadb.*whl" wheels/

# Compare requirements vs available wheels
poetry run python scripts/generate_offline_requirements.py \
    requirements.txt wheels/py312-macos-arm64 /tmp/check.txt
```

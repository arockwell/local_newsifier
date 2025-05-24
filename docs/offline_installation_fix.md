# Offline Installation Fix Documentation

This document explains the fixes applied to resolve offline installation issues.

## Problems Identified

### 1. Wrong Wheels Directory Path
**Issue**: The `install-offline` target was looking for wheels in the root `wheels/` directory, but the build scripts create platform-specific directories like:
- `wheels/py312-macos-arm64/`
- `wheels/py312-linux-x64/`
- `wheels/py312/` (fallback)

**Fix**: Added platform detection to automatically find the correct wheels directory.

### 2. Main Install Target Requires Internet
**Issue**: The `make install` target runs `poetry install --no-interaction` which always tries to reach PyPI, making it unsuitable for offline environments.

**Fix**: Keep `make install` for online environments and ensure `make install-offline` properly handles all offline needs.

### 3. spaCy Model Checks Failed
**Issue**: The spaCy model checks attempted to import spacy before it was installed, causing failures.

**Fix**: Added a check to verify spaCy is installed before attempting to load models.

### 4. Platform Detection Logic
**Issue**: Different scripts used different platform detection methods, leading to inconsistencies.

**Fix**: Standardized platform detection across Makefile and scripts.

## How Platform Detection Works

The fixed offline installation now:

1. Detects your Python version (e.g., `py312`)
2. Detects your OS (e.g., `macos`, `linux`)
3. Detects your architecture (e.g., `arm64`, `x64`)
4. Looks for wheels in this order:
   - Platform-specific: `wheels/py312-macos-arm64/`
   - Version-specific: `wheels/py312/`
   - Fails with helpful error if neither exists

## Testing Offline Installation

### Quick Test
```bash
# Build wheels for your platform
make build-wheels

# Test the offline installation
make test-wheels
```

### Full Offline Test
```bash
# 1. Build wheels on connected machine
make build-wheels

# 2. Simulate offline environment
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export PIP_NO_INDEX=1

# 3. Run offline installation
make install-offline

# 4. Verify installation
poetry run python -c "import local_newsifier; print('Success!')"
```

## Troubleshooting

### "No wheels found for py312 on macos-arm64"
This means wheels haven't been built for your platform. Run:
```bash
make build-wheels
```

### "spaCy models must be manually provided"
For true offline installation, spaCy models need to be downloaded separately:
```bash
# On connected machine
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg

# Find the downloaded models
python -c "import spacy; print(spacy.util.get_package_path('en_core_web_sm'))"

# Copy these to your offline environment
```

### Different Platform Errors
If deploying to a different platform than where you built wheels:
```bash
# On target platform
make build-wheels

# Or use Docker to build Linux wheels
make build-wheels-linux
```

## Best Practices

1. **Always test offline installation** before deployment:
   ```bash
   make test-wheels
   ```

2. **Build platform-specific wheels** for each deployment target

3. **Include wheels in version control** for reproducible deployments

4. **Document platform requirements** in your deployment guide

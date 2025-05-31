# Offline Installation Guide - Linux x86_64

This guide explains how to install Local Newsifier in environments without internet access, specifically for Linux x86_64 systems.

## Prerequisites

- Linux x86_64 system
- Python 3.10, 3.11, or 3.12 installed
- Pre-built wheel package directory (`wheels/linux-x86_64`)
- Basic build tools (gcc, make) for any source packages

## Quick Start

If you already have the pre-built wheels, simply run:

```bash
make install-offline-linux-x86_64
```

Or manually:

```bash
./scripts/install_offline_linux.sh
```

## Building Wheels (Internet Required)

To prepare wheels for offline installation, run this on a machine with internet:

```bash
# Build all wheels for Linux x86_64
make build-wheels-linux-x86_64

# Validate the wheels are complete
make validate-offline
```

This creates a `wheels/linux-x86_64` directory containing:
- All required wheel files
- A `requirements.txt` file with exact versions
- A `manifest.txt` listing all wheels

## Manual Offline Installation

If you prefer to install manually:

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Upgrade pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **Install from wheels:**
   ```bash
   pip install \
       --no-index \
       --find-links wheels/linux-x86_64 \
       -r wheels/linux-x86_64/requirements.txt
   ```

4. **Install the package:**
   ```bash
   pip install --no-deps -e .
   ```

## Validation

To verify your offline installation will work:

```bash
# Validate wheels are complete
python scripts/validate_offline_wheels.py

# Test in Docker (simulates offline environment)
./scripts/test_offline_install_docker.sh
```

## Troubleshooting

### Missing Wheels

If validation fails with missing packages:

1. Check the error message for specific packages
2. On a machine with internet, download the missing wheels:
   ```bash
   pip download <package-name> \
       --platform manylinux2014_x86_64 \
       --python-version 312 \
       --only-binary :all: \
       --dest wheels/linux-x86_64
   ```

### Version Conflicts

If you see version conflict errors:

1. Ensure you're using the correct Python version (3.10-3.12)
2. Check that all wheels are for the correct platform
3. Verify no duplicate versions exist in the wheel directory

### Build Tools Required

Some packages may require compilation. Ensure these are installed:

```bash
# Debian/Ubuntu
sudo apt-get install gcc g++ make python3-dev

# RHEL/CentOS
sudo yum install gcc gcc-c++ make python3-devel
```

## SpaCy Models

SpaCy language models require separate offline installation:

1. **On a machine with internet:**
   ```bash
   # Download models
   python -m spacy download en_core_web_sm
   python -m spacy download en_core_web_lg

   # Package them
   python -m spacy package en_core_web_sm ./spacy_models --name en_core_web_sm
   python -m spacy package en_core_web_lg ./spacy_models --name en_core_web_lg
   ```

2. **On the offline machine:**
   ```bash
   # Install packaged models
   pip install spacy_models/en_core_web_sm-*/dist/*.whl
   pip install spacy_models/en_core_web_lg-*/dist/*.whl
   ```

## Wheel Directory Structure

The `wheels/linux-x86_64` directory should contain:

```
wheels/linux-x86_64/
├── requirements.txt     # Exact versions of all packages
├── manifest.txt        # List of all wheel files
├── alembic-*.whl
├── apify_client-*.whl
├── beautifulsoup4-*.whl
├── celery-*.whl
├── chromadb-*.whl
├── click-*.whl
├── crewai-*.whl
├── fastapi-*.whl
├── fastapi_injectable-*.whl
└── ... (200+ more wheels)
```

## Platform Compatibility

These wheels are built specifically for:
- **OS**: Linux
- **Architecture**: x86_64 (AMD64)
- **Python**: 3.12 (compatible with 3.10-3.12)
- **ABI**: cp312 (CPython 3.12)

Common platform tags:
- `manylinux2014_x86_64`: Most compatible
- `manylinux_2_17_x86_64`: Newer glibc requirement
- `manylinux_2_28_x86_64`: Even newer glibc
- `linux_x86_64`: Generic Linux

## Creating a Deployment Package

To create a complete offline deployment package:

```bash
# Create deployment directory
mkdir -p local-newsifier-offline
cd local-newsifier-offline

# Copy necessary files
cp -r ../wheels/linux-x86_64 wheels
cp -r ../src .
cp -r ../scripts .
cp ../pyproject.toml .
cp ../requirements.txt .
cp ../Makefile .

# Create tarball
cd ..
tar -czf local-newsifier-offline.tar.gz local-newsifier-offline/

# Transfer to offline system and extract
# On offline system:
tar -xzf local-newsifier-offline.tar.gz
cd local-newsifier-offline
make install-offline-linux-x86_64
```

## Security Considerations

When preparing wheels for offline installation:

1. **Verify sources**: Download wheels only from PyPI or trusted sources
2. **Check signatures**: Verify package signatures when possible
3. **Version pinning**: Use exact versions to ensure reproducibility
4. **Audit dependencies**: Review all transitive dependencies
5. **Test thoroughly**: Validate in an isolated environment

## Support

If you encounter issues:

1. Check the validation script output
2. Review wheel manifest for missing packages
3. Ensure Python and system requirements match
4. Check file permissions on wheel directory

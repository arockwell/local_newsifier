# Python Setup Guide

This guide provides instructions for setting up the Python environment for Local Newsifier using Poetry.

## Python Version

The project requires Python 3.10-3.13, with Python 3.12 recommended to match our CI environment.

A `.python-version` file is included in the project root that specifies Python 3.12.10.

## Setup with Poetry

We use Poetry for dependency management:

```bash
# Install dependencies using Poetry
make setup-poetry -- --no-index --find-links=wheels

# Activate the Poetry environment
poetry shell

# Install spaCy models
make setup-spacy
```

Running `make setup-poetry -- --no-index --find-links=wheels` installs all
packages from the `wheels/` directory and is required before executing
`make test` in an offline environment.

### Offline Installation

If your deployment environment cannot reach PyPI, the repository includes pre-built wheels for offline installation.

#### Wheels directory

All wheels live under the `wheels/` directory, organized by Python version and platform. This directory allows Poetry and pip to install packages without internet access.

If you need to build new wheels on a machine with internet access:

```bash
# Build wheels for the current Python version on the current platform
./scripts/build_wheels.sh

# Or specify a Python version explicitly
./scripts/build_wheels.sh python3.12
./scripts/build_wheels.sh python3.13
```

Wheels are organized by both Python version and platform to ensure compatibility:

```
wheels/
├── py310/                  # Cross-platform wheels for Python 3.10
├── py311/                  # Cross-platform wheels for Python 3.11
├── py312/                  # Cross-platform wheels for Python 3.12
├── py313/                  # Cross-platform wheels for Python 3.13
├── py310-macos-arm64/      # Platform-specific wheels for Python 3.10 on macOS arm64
├── py311-macos-arm64/      # Platform-specific wheels for Python 3.11 on macOS arm64
├── py312-linux-x64/        # Platform-specific wheels for Python 3.12 on Linux x64
└── ...                     # Other platform-specific directories
```

For cross-platform support, you'll need to build wheels on each target platform (macOS, Linux, Windows) separately and commit all platform-specific directories.

After building wheels, commit them to the repository to ensure true offline installation:

```bash
# Organize any wheels at the root level
make organize-wheels

# Add and commit wheels
git add wheels/py*/
git commit -m "Update wheels for offline installation for [platform]"
```

#### Offline Installation on Target Machine

On the target machine without internet access, install packages using the appropriate platform-specific directory if available, or fall back to the version-specific directory:

```bash
# For Python 3.12 on Linux x64
python3.12 -m pip install --no-index --find-links=wheels/py312-linux-x64 -r requirements.txt

# If platform-specific directory isn't available, fall back to version directory
python3.12 -m pip install --no-index --find-links=wheels/py312 -r requirements.txt
```

#### Testing Offline Installation

You can test the offline installation process before deploying:

```bash
# Test with current Python version on current platform
./scripts/test_offline_install.sh

# Test with specific Python version
./scripts/test_offline_install.sh python3.12
```

The test script will automatically detect your platform and look for the appropriate wheel directory. If a platform-specific directory isn't found, it will fall back to the version-specific directory.

If you need to manually select a specific Python version for Poetry to use:

```bash
# Tell Poetry which Python version to use
poetry env use python3.12  # or the path to your Python executable
```

## Troubleshooting

### Common Issues

1. **"ImportError: No module named X"**
   Make sure you're in the Poetry environment: `poetry shell`

2. **"Incompatible Python version"**
   Check which Python version Poetry is using: `poetry env info`

3. **"spaCy model not found"**
   Install the required models: `make setup-spacy`

4. **"No matching distribution found for sqlalchemy..."**
   This typically happens during offline installation when wheels for your Python version or platform are missing.
   Build wheels for your specific Python version and platform:
   ```bash
   ./scripts/build_wheels.sh python3.xx  # Replace with your Python version
   ```
   If you're on a different platform (e.g., Linux) than where the wheels were built (e.g., macOS), you'll need to build platform-specific wheels or use the `--platform` option with pip to specify the target platform.

### Poetry Environment Management

List Poetry environments:
```bash
poetry env list
```

Remove a Poetry environment:
```bash
poetry env remove <environment-name>
```

Create a fresh environment:
```bash
poetry env remove --all
poetry install
```

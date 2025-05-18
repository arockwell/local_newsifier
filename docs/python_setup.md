# Python Setup Guide

This guide provides instructions for setting up the Python environment for Local Newsifier using Poetry.

## Python Version

The project requires Python 3.10-3.13, with Python 3.12 recommended to match our CI environment.

A `.python-version` file is included in the project root that specifies Python 3.12.3.

## Setup with Poetry

We use Poetry for dependency management:

```bash
# Install dependencies using Poetry
make setup-poetry

# Activate the Poetry environment
poetry shell

# Install spaCy models
make setup-spacy
```

### Offline Installation

If your deployment environment cannot reach PyPI, build dependency wheels on a
machine with internet access:

```bash
# Build wheels for the current Python version
./scripts/build_wheels.sh

# Or specify a Python version explicitly
./scripts/build_wheels.sh python3.12
./scripts/build_wheels.sh python3.13
```

Wheels are organized by Python version to ensure compatibility:

```
wheels/
├── py310/     # Wheels for Python 3.10
├── py311/     # Wheels for Python 3.11
├── py312/     # Wheels for Python 3.12
└── py313/     # Wheels for Python 3.13
```

Copy the generated `wheels/` directory to the target machine and install
packages locally using the appropriate Python version subdirectory:

```bash
# For Python 3.13
python3.13 -m pip install --no-index --find-links=wheels/py313 -r requirements.txt

# For Python 3.12
python3.12 -m pip install --no-index --find-links=wheels/py312 -r requirements.txt
```

You can test the offline installation process with:

```bash
./scripts/test_offline_install.sh [python_command]
```

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
   This typically happens during offline installation when wheels for your Python version are missing.
   Build wheels for your specific Python version:
   ```bash
   ./scripts/build_wheels.sh python3.xx  # Replace with your Python version
   ```

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

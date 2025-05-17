# Python Setup Guide

This guide provides instructions for setting up the Python environment for Local Newsifier using Poetry.

## Python Version

The project requires Python 3.10-3.12, with Python 3.12 recommended to match our CI environment.

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
make build-wheels
```

Copy the generated `wheels/` directory to the target machine and install
packages locally:

```bash
pip install --no-index --find-links=wheels -r requirements.txt
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

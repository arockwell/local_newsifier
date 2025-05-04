# Python Environment Setup Guide

This guide provides instructions for setting up a consistent Python development environment for the Local Newsifier project.

## Recommended Python Version

The Local Newsifier project requires Python 3.10-3.12, but we recommend using **Python 3.12** to match our CI environment.

A `.python-version` file is included in the project root to help tools like pyenv automatically select the correct version.

## Setup with pyenv (Recommended)

[pyenv](https://github.com/pyenv/pyenv) helps manage multiple Python versions on your system.

### Installation

#### macOS
```bash
# Install with Homebrew
brew install pyenv

# Add to shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

#### Linux
```bash
# Install dependencies
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl git

# Install pyenv
curl https://pyenv.run | bash

# Add to shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

### Installing the Correct Python Version

```bash
# Install Python 3.12.3
pyenv install 3.12.3

# Set as local version for this project
# (This happens automatically due to the .python-version file)
cd /path/to/local_newsifier
pyenv local 3.12.3

# Verify installation
python --version  # Should display Python 3.12.3
```

## Setup with Poetry

We use Poetry for dependency management. After setting up the correct Python version:

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Configure Poetry to use the project's Python version
cd /path/to/local_newsifier
poetry env use 3.12.3

# Install dependencies
poetry install

# Verify installation
poetry run python --version  # Should display Python 3.12.3
```

## External Dependencies

### spaCy Models

The project requires specific spaCy models. Install them with:

```bash
# Within Poetry environment
poetry run python -m spacy download en_core_web_sm
poetry run python -m spacy download en_core_web_lg
```

### PostgreSQL and Redis

For local development, you'll need:
- PostgreSQL 14+ (17 recommended to match CI)
- Redis server for Celery

See the `.env.example` file for configuration details.

## Troubleshooting

### Common Issues

1. **"ImportError: No module named X"**
   Make sure you're in the Poetry environment: `poetry shell`

2. **"Incompatible Python version"**
   Verify your Python version and update if needed: `python --version`

3. **"spaCy model not found"**
   Install required models: `poetry run python -m spacy download en_core_web_lg`

4. **"postgres_fdw extension not available"**
   Make sure you have the PostgreSQL development packages installed: `sudo apt install postgresql-server-dev-all`

### Version Compatibility Checks

Run the version check script to verify your environment:

```bash
# Check environment compatibility
poetry run python -c "import sys; import spacy; import sqlmodel; print(f'Python: {sys.version}\\nspaCy: {spacy.__version__}\\nSQLModel: {sqlmodel.__version__}')"
```

## CI Environment

Our GitHub Actions CI runs with:
- Python 3.12
- PostgreSQL 17
- Poetry 1.7.1

Matching this environment locally will minimize "works on my machine" issues.

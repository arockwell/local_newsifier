# Local System Setup Recommendations

This guide provides recommendations for setting up your local development environment for the Local Newsifier project, specifically tailored to macOS systems.

## Current System Issues

Based on our analysis, the following issues were identified:

1. **Python Version Mismatch**:
   - You're using Python 3.13.2 (from Homebrew) but the project requires 3.10-3.12
   - This can cause compatibility issues with some packages

2. **Multiple Python Installations**:
   - You have multiple Python versions installed via Homebrew (3.11, 3.12, 3.13)
   - No version management system like pyenv to switch between versions

3. **Global Package Installation**:
   - Some key packages are installed globally, which can cause conflicts

## Recommended System Setup

### 1. Install pyenv for Python Version Management

pyenv allows you to easily switch between Python versions per project:

```bash
# Install pyenv with Homebrew
brew install pyenv

# Add to your shell (for zsh)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload your shell
source ~/.zshrc
```

### 2. Install Python 3.12 with pyenv

```bash
# Install Python 3.12.3 (matches our CI environment)
pyenv install 3.12.3

# Set it as your local version in the project directory
cd ~/dev/local_newsifier
pyenv local 3.12.3

# Verify it worked
python --version  # Should show Python 3.12.3
```

### 3. Create Isolated virtualenvs with Poetry

```bash
# Update poetry to use the correct Python version
cd ~/dev/local_newsifier
poetry env use $(pyenv which python)

# Install dependencies in the isolated environment
poetry install

# Activate the environment
poetry shell

# Verify package installation paths (should be in .venv)
poetry run pip list
```

### 4. Use Docker for Maximum Consistency

For the most consistent environment:

```bash
# Build and start the Docker development environment
cd ~/dev/local_newsifier
make docker-build
make docker-up

# Run tests in the Docker environment to verify setup
make docker-test
```

## Additional macOS Tips

### Fix Homebrew Python Path Conflicts

Add this to your `~/.zshrc` to prefer pyenv over Homebrew Python:

```bash
# Ensure pyenv shims take priority over Homebrew
export PATH="$PYENV_ROOT/shims:$PATH"
```

### Install PostgreSQL and Redis Locally

```bash
# Install database services
brew install postgresql@15 redis

# Start services
brew services start postgresql@15
brew services start redis
```

### Configure VS Code for Poetry

1. Install the Python extension for VS Code
2. Set the interpreter to your Poetry environment:
   - Open Command Palette (⌘⇧P)
   - "Python: Select Interpreter"
   - Choose the Poetry environment

### Create Project-Specific Environment Variables

Create a `.env.local` file (not tracked in git) for your personal settings:

```
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_HOST=localhost

# Your personal cursor ID to avoid database conflicts
CURSOR_DB_ID=alex
```

## Troubleshooting Common macOS Issues

### Python SSL Certificate Issues

If you encounter SSL errors:

```bash
# Install certificates package
pip install certifi

# Set the SSL_CERT_FILE environment variable
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
```

### PostgreSQL Connection Issues

If you have problems connecting to PostgreSQL:

```bash
# Create the database
createdb local_newsifier

# Verify connection
psql -d local_newsifier -c "SELECT 1"
```

### Package Installation Conflicts

If you experience dependency conflicts:

```bash
# Clean Poetry environment and reinstall
poetry env remove $(poetry env info -p)
poetry install
```

By following these recommendations, you'll have a consistent environment that minimizes "works on my machine" problems.

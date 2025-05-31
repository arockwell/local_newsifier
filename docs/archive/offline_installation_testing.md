# Testing Offline Installation

This guide explains how to test the offline installation process for Local Newsifier.

## Overview

Offline installation is crucial for environments without internet access. The process involves:
1. Building wheels on a connected machine
2. Transferring the wheels to the offline environment
3. Installing from the local wheels directory

## Building Wheels

### On Your Current Platform

Build wheels for your current Python version and platform:

```bash
# Build for current Python/platform
make build-wheels

# Build for all Python versions on current platform
make build-wheels-all

# Build for specific Python version
./scripts/build_wheels.sh python3.12
```

### For Linux Platforms

If you need Linux wheels but are on macOS/Windows:

```bash
# Build Linux wheels using Docker (requires Docker)
make build-wheels-linux
```

### Organizing Wheels

After building, organize wheels by platform:

```bash
make organize-wheels
```

This creates directories like:
- `wheels/py312/` - Cross-platform wheels
- `wheels/py312-macos-arm64/` - Platform-specific wheels
- `wheels/py312-linux-x64/` - Platform-specific wheels

## Testing the Offline Installation

### Quick Test

The easiest way to test offline installation:

```bash
# Test with current Python version
make test-wheels

# Test with specific Python version
./scripts/test_offline_install.sh python3.12
```

This script:
1. Creates a temporary virtual environment
2. Installs all dependencies without internet access
3. Verifies key packages are installed correctly
4. Reports any missing dependencies

### Manual Testing

For more thorough testing:

1. **Simulate offline environment**:
   ```bash
   # Create a new directory
   mkdir offline-test
   cd offline-test

   # Copy the project (excluding .git for speed)
   rsync -av --exclude='.git' --exclude='__pycache__' \
         --exclude='.pytest_cache' /path/to/local_newsifier/ .

   # Remove any existing Poetry environments
   rm -rf ~/.cache/pypoetry/virtualenvs/local-newsifier*
   ```

2. **Test the installation**:
   ```bash
   # Ensure Poetry is installed
   which poetry || curl -sSL https://install.python-poetry.org | python3 -

   # Run offline installation
   make install-offline

   # Activate the environment
   poetry shell

   # Verify installation
   python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
   python -c "import spacy; print('spaCy:', spacy.__version__)"
   python -c "import local_newsifier; print('Local Newsifier installed!')"
   ```

3. **Run tests to verify**:
   ```bash
   make test
   ```

### Testing in Docker (Most Accurate)

For the most accurate offline testing, use Docker:

```bash
# Create a Dockerfile for testing
cat > Dockerfile.offline-test << 'EOF'
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy project files
WORKDIR /app
COPY . .

# Disable network access (simulate offline)
RUN echo "127.0.0.1 pypi.org" >> /etc/hosts && \
    echo "127.0.0.1 files.pythonhosted.org" >> /etc/hosts

# Test offline installation
RUN make install-offline

# Verify installation
RUN poetry run python -c "import local_newsifier; print('Success!')"
EOF

# Build and test
docker build -f Dockerfile.offline-test -t offline-test .
```

## Troubleshooting

### Common Issues

1. **Missing platform-specific wheels**:
   ```
   ERROR: Could not find a version that satisfies the requirement psycopg2-binary
   ```
   Solution: Build wheels on the target platform or use Docker to build Linux wheels.

2. **Wrong Python version**:
   ```
   ERROR: Package requires a different Python: 3.12.0 not in '>=3.10,<3.13'
   ```
   Solution: Ensure wheels match your Python version. Use `python --version` to check.

3. **Missing development dependencies**:
   ```
   ERROR: Could not find a version that satisfies the requirement pytest
   ```
   Solution: Ensure both requirements.txt and requirements-dev.txt wheels are built.

### Verification Checklist

After offline installation, verify these components work:

- [ ] Poetry environment is created
- [ ] All Python packages are installed
- [ ] spaCy models are available (for true offline, these must be pre-downloaded)
- [ ] Database can be initialized
- [ ] Tests can run successfully
- [ ] CLI commands work (`nf --help`)
- [ ] API can start (`make run-api`)

## Best Practices

1. **Test on clean systems**: Always test on a system without cached packages
2. **Match platforms**: Build wheels on the same OS/architecture as deployment
3. **Include all dependencies**: Don't forget development dependencies for testing
4. **Version everything**: Keep wheels organized by Python version and platform
5. **Document versions**: Note which Python/platform versions you've tested

## Platform-Specific Notes

### macOS
- Wheels built on macOS ARM64 won't work on Intel Macs
- Use `uname -m` to check architecture (arm64 vs x86_64)

### Linux
- Wheels built on Ubuntu work on most Linux distros
- Some packages (like psycopg2-binary) are very platform-specific
- Use Docker for consistent Linux wheel building

### Windows
- Not officially supported, but wheels can be built
- May need Visual C++ redistributables for some packages

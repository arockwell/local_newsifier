# Wheel Directory

This directory contains Python wheels for offline installation. Wheels are organized by Python version and platform to ensure compatibility.

**IMPORTANT:** All wheel files (*.whl) in this directory and its subdirectories should be committed to the repository to enable true offline installation.

## Directory Structure

```
wheels/
├── py312/                  # Cross-platform wheels for Python 3.12
├── py312-linux-x86_64/     # Platform-specific wheels for Python 3.12 on Linux x86_64
├── py312-linux-aarch64/    # Platform-specific wheels for Python 3.12 on Linux ARM64/aarch64
└── py312-macos-arm64/      # Platform-specific wheels for Python 3.12 on macOS ARM64
```

The directory structure includes both:
- Version-specific directories (py312) with cross-platform wheels
- Platform-specific directories (py312-macos-arm64, py312-linux-x86_64, etc.) with platform-specific wheels

Note: As of May 2024, we only maintain wheels for Python 3.12, as this is the primary version used in development and production.

## Usage

For offline installation, use the appropriate platform-specific directory if available, or fall back to the version-specific directory:

```bash
# For Python 3.12 on Linux x86_64
python3.12 -m pip install --no-index --find-links=wheels/py312-linux-x86_64 -r requirements.txt

# For Python 3.12 on Linux ARM64/aarch64
python3.12 -m pip install --no-index --find-links=wheels/py312-linux-aarch64 -r requirements.txt

# If platform-specific directory isn't available, fall back to version directory
python3.12 -m pip install --no-index --find-links=wheels/py312 -r requirements.txt
```

On platforms where pre-built wheels are available, no internet connection is required as all dependencies are available in the platform-specific directories.

## Compatibility

Wheels are both platform-specific and Python version-specific. Each subdirectory contains a `manifest.txt` file with information about the environment used to build the wheels, including:

- Python version
- Operating system type
- Architecture
- Date generated
- Key package versions

## Regenerating Wheels

If you need to update the wheel files (e.g., when project dependencies change):

```bash
# Use the Makefile command for the current platform
make build-wheels

# For Linux wheels (requires Docker)
make build-wheels-linux
```

This will download all required wheels for Python 3.12 with their dependencies to the appropriate platform-specific directory. The Makefile automatically detects your platform and Python version.

### Cross-Platform Support

To fully support offline installation across multiple platforms:

1. Build wheels on each target platform:
   ```bash
   # On macOS with arm64 (M1/M2)
   make build-wheels

   # On Linux with x86_64 (using Docker)
   make build-wheels-linux

   # On Windows (not yet implemented in Makefile)
   # Use the script directly: ./scripts/build_wheels.sh python3.12
   ```

2. Commit all platform-specific wheel directories to the repository.

## Version Control

After building wheels, make sure to commit them to the repository:

```bash
# Test the wheels first
make test-wheels

# Add all wheels to git
git add wheels/py*/

# Commit the wheels
git commit -m "Update wheels for offline installation"
```

This ensures that other users can install dependencies without internet access.

## Troubleshooting

If you encounter errors like:

```
ERROR: Could not find a version that satisfies the requirement sqlalchemy>=2.0.27
ERROR: No matching distribution found for sqlalchemy>=2.0.27
```

It could mean either:

1. The wheels for your specific Python version might be missing
2. The wheels for your specific platform might be missing

### Solutions:

1. Check for platform-specific wheel directory first:
   ```bash
   # Example: For Python 3.12 on Linux x86_64
   eza -la wheels/py312-linux-x86_64/  # or use 'ls -la' if eza not available
   ```

2. If missing, fall back to version-specific directory:
   ```bash
   eza -la wheels/py312/  # or use 'ls -la' if eza not available
   ```

3. If still missing, generate wheels for your specific Python version and platform:
   ```bash
   # For local platform
   make build-wheels

   # For Linux using Docker
   make build-wheels-linux
   ```

4. Test and commit the wheels for other users:
   ```bash
   make test-wheels
   git add wheels/py*/
   git commit -m "Add Python 3.12 wheels for [platform]"
   ```

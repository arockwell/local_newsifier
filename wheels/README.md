# Wheel Directory

This directory contains Python wheels for offline installation. Wheels are organized by Python version and platform to ensure compatibility.

**IMPORTANT:** All wheel files (*.whl) in this directory and its subdirectories should be committed to the repository to enable true offline installation.

## Directory Structure

```
wheels/
├── py310/                  # Cross-platform wheels for Python 3.10
├── py311/                  # Cross-platform wheels for Python 3.11
├── py312/                  # Cross-platform wheels for Python 3.12
├── py313/                  # Cross-platform wheels for Python 3.13
├── py310-macos-arm64/      # Platform-specific wheels for Python 3.10 on macOS arm64
├── py311-macos-arm64/      # Platform-specific wheels for Python 3.11 on macOS arm64
├── py312-macos-arm64/      # Platform-specific wheels for Python 3.12 on macOS arm64
├── py313-macos-arm64/      # Platform-specific wheels for Python 3.13 on macOS arm64
├── py310-linux-x64/        # Platform-specific wheels for Python 3.10 on Linux x64
└── ...                     # Other platform-specific directories
```

The directory structure includes both:
- Version-specific directories (py310, py311, etc.) with cross-platform wheels
- Platform-specific directories (py310-macos-arm64, py312-linux-x64, etc.) with platform-specific wheels

## Usage

For offline installation, use the appropriate platform-specific directory if available, or fall back to the version-specific directory:

```bash
# For Python 3.12 on Linux x64
python3.12 -m pip install --no-index --find-links=wheels/py312-linux-x64 -r requirements.txt

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
# For the current Python version on the current platform
./scripts/build_wheels.sh

# For a specific Python version on the current platform
./scripts/build_wheels.sh python3.12
./scripts/build_wheels.sh python3.13
```

This will download all required wheels for the specified Python version with their dependencies to the appropriate platform-specific directory.

### Cross-Platform Support

To fully support offline installation across multiple platforms:

1. Build wheels on each target platform:
   ```bash
   # On macOS with arm64 (M1/M2)
   ./scripts/build_wheels.sh python3.12
   
   # On Linux with x86_64 (using Docker)
   ./scripts/build_linux_wheels.sh 3.12
   
   # On Windows
   ./scripts/build_wheels.sh python3.12
   ```

2. Commit all platform-specific wheel directories to the repository.

## Version Control

After building wheels, make sure to commit them to the repository:

```bash
# Organize any wheels at the root level into version and platform directories
make organize-wheels

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
   # Example: For Python 3.12 on Linux x64
   ls -la wheels/py312-linux-x64/
   ```

2. If missing, fall back to version-specific directory:
   ```bash
   ls -la wheels/py312/
   ```

3. If still missing, generate wheels for your specific Python version and platform:
   ```bash
   # For local platform
   ./scripts/build_wheels.sh python3.12
   
   # For Linux using Docker
   ./scripts/build_linux_wheels.sh 3.12
   ```

4. Organize the wheels and commit them for other users:
   ```bash
   make organize-wheels
   git add wheels/py*/
   git commit -m "Add Python 3.12 wheels for Linux x64"
   ```
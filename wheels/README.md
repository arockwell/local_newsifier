# Wheel Directory

This directory contains Python wheels for offline installation. Wheels are organized by Python version to ensure compatibility.

## Directory Structure

```
wheels/
├── py310/     # Wheels for Python 3.10
├── py311/     # Wheels for Python 3.11
├── py312/     # Wheels for Python 3.12
└── py313/     # Wheels for Python 3.13
```

## Usage

For offline installation, use the appropriate Python version subdirectory:

```bash
# For Python 3.13
python3.13 -m pip install --no-index --find-links=wheels/py313 -r requirements.txt

# For Python 3.12
python3.12 -m pip install --no-index --find-links=wheels/py312 -r requirements.txt

# For Python 3.11
python3.11 -m pip install --no-index --find-links=wheels/py311 -r requirements.txt
```

No internet connection is required as all dependencies are available as wheels in the version-specific directories.

## Compatibility

Wheels are platform-specific and Python version-specific. Each subdirectory contains a `manifest.txt` file with information about the environment used to build the wheels.

## Regenerating Wheels

If you need to update the wheel files (e.g., when project dependencies change):

```bash
# For the current Python version
./scripts/build_wheels.sh

# For a specific Python version
./scripts/build_wheels.sh python3.12
./scripts/build_wheels.sh python3.13
```

This will download all required wheels for the specified Python version with their dependencies to the appropriate subdirectory.

## Troubleshooting

If you encounter errors like:

```
ERROR: Could not find a version that satisfies the requirement sqlalchemy>=2.0.27
ERROR: No matching distribution found for sqlalchemy>=2.0.27
```

It means the wheels for your specific Python version might be missing. Generate wheels for your Python version using the command above.
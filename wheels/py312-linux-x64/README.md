# Python 3.12 Linux x86_64 Wheels

This directory contains all the wheels needed for offline installation of Local Newsifier with Python 3.12 on Linux x86_64 systems.

## Installation Instructions

### Method 1: Using the Installation Helper Script

For the simplest installation, use the provided helper script:

```bash
# Navigate to the wheels directory
cd wheels/py312-linux-x64

# Make the script executable (if needed)
chmod +x install_helper.sh

# Install the project and all dependencies
./install_helper.sh
```

### Method 2: Using pip directly

You can also use pip directly with the `--no-index` and `--find-links` options:

```bash
# Navigate to the project root
cd /path/to/local_newsifier

# Install the project and all dependencies
pip install --no-index --find-links=wheels/py312-linux-x64 -e .
```

## Troubleshooting

If you encounter issues with specific wheel files having long filenames, use the installation helper script instead of directly invoking pip.

For any missing dependencies, you can run the included fix script:

```bash
# Navigate to the wheels directory
cd wheels/py312-linux-x64

# Make the script executable (if needed)
chmod +x fix_missing_deps.sh

# Run the fix script
./fix_missing_deps.sh
```

## Development Dependencies

This directory also includes wheels for development dependencies. To install them:

```bash
# Install the project with development dependencies
pip install --no-index --find-links=wheels/py312-linux-x64 -e ".[dev]"
```

## Verification

To verify that all required wheels are present:

```bash
# Navigate to the wheels directory
cd wheels/py312-linux-x64

# Make the script executable (if needed)
chmod +x verify_wheels.sh

# Run the verification script
./verify_wheels.sh
```
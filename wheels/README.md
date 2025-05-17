# Wheel Directory

This directory is used to store Python wheels for offline installation. 

## Usage

1. **Generate wheels** (requires internet connection):
   ```bash
   ./scripts/build_wheels.sh
   ```

2. **Install offline** (no internet connection needed):
   ```bash
   pip install --no-index --find-links=wheels -r requirements.txt
   ```

The `.gitignore` in this directory prevents wheel files from being committed to the repository to avoid bloating the repo size. However, the directory structure is preserved for easy offline installation.

## Supporting Offline Environments

For completely offline environments:
1. Run `./scripts/build_wheels.sh` on a machine with internet access
2. Copy the entire project including the generated wheels/ directory to the offline machine
3. Run the offline installation command
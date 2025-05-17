# Wheel Directory

This directory contains Python wheels for offline installation. All necessary wheel files are included in the repository, allowing for a truly offline installation experience.

## Usage

Simply run the offline installation command:
```bash
pip install --no-index --find-links=wheels -r requirements.txt
```

No internet connection is required as all dependencies are already available as wheels in this directory.

## Regenerating Wheels

If you need to update the wheel files (e.g., when project dependencies change):

```bash
./scripts/build_wheels.sh
```

This will download all required wheels with their dependencies to this directory.
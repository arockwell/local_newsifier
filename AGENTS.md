# AGENTS Instructions

This document helps Codex locate developer guides and explains how to work with offline wheels.

## Documentation Map

- Main guide: `claude.md`
- Module guides:
  - src/local_newsifier/api/CLAUDE.md
  - src/local_newsifier/cli/CLAUDE.md
  - src/local_newsifier/database/CLAUDE.md
  - src/local_newsifier/di/CLAUDE.md
  - src/local_newsifier/flows/CLAUDE.md
  - src/local_newsifier/models/CLAUDE.md
  - src/local_newsifier/services/CLAUDE.md
  - src/local_newsifier/tools/CLAUDE.md
- Additional docs: all Markdown files under `docs/`, plus `FastAPI-Injectable-Migration-Plan.md`, `README.md`, and `README_CLI.md`.

If a `CLAUDE.md` file is added or removed, update this list.

## Quick Setup

1. **Install dependencies offline first**:
   ```bash
   python -m pip install --no-index --find-links=wheels -r requirements.txt
   ```
   The development environment normally has no internet access. Use
   `make setup-poetry` only if you have network connectivity.
2. Install spaCy models (needed for NLP features): `make setup-spacy`
3. Run the test suite: `make test`

## Dependency Management with Wheels

### Installing Dependencies Offline

The project uses pre-built wheels for offline dependency installation. These wheels are organized by Python version and platform to ensure compatibility.

#### Installing Dependencies with Wheels

Once you have wheels available for your Python version and platform, you can install dependencies without internet access:

```bash
# For automatically detected Python version and platform
python -m pip install --no-index --find-links=wheels -r requirements.txt

# For a specific Python version and platform
python -m pip install --no-index --find-links=wheels/py312-linux-x64 -r requirements.txt
```

#### Building Wheels for Different Platforms

To build wheels for the current environment:
```bash
make build-wheels
```

To build wheels for Python 3.12 on Linux (x64 and arm64):
```bash
make build-linux-wheels-py312
```

This requires Docker and builds all dependencies, including platform-specific ones like psycopg2-binary.
After building wheels, run `make test-wheels` or
`./scripts/test_offline_install.sh <python>` to verify that all required runtime and development packages are present before running tests.

#### Organizing Existing Wheels

If you have wheels in the wrong directories, organize them by Python version and platform:
```bash
./scripts/organize_wheels.sh
```

#### Testing Offline Installation

Verify that the wheels installation works correctly:
```bash
./scripts/test_offline_install.sh python3.12
```

### Directory Structure

The wheels are organized by Python version and platform:
- `wheels/py312-linux-x64/`: Python 3.12 wheels for Linux x64
- `wheels/py312-linux-arm64/`: Python 3.12 wheels for Linux ARM64
- `wheels/py312-macos-arm64/`: Python 3.12 wheels for macOS ARM64
- `wheels/py312/`: Python 3.12 general wheels

### Important Notes

- Platform-specific wheels (like psycopg2-binary) require matching the target platform
- Pure Python wheels (with names ending in `-py3-none-any.whl`) work on any platform
- Always commit the wheels directory to the repository for true offline installation

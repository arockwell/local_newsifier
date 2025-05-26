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
- Test guides:
  - tests/CLAUDE.md
  - tests/api/CLAUDE.md
  - tests/crud/CLAUDE.md
  - tests/services/CLAUDE.md
- Additional docs: all Markdown files under `docs/`, plus `FastAPI-Injectable-Migration-Plan.md`, `README.md`, and `README_CLI.md`.

If a `CLAUDE.md` file is added or removed, update this list.

## Quick Setup

1. **Install dependencies using Poetry offline**:
   After building or copying wheels, run:
   ```bash
   make install-offline
   ```
   This will install all dependencies and set up the database.
2. Run the test suite from the Poetry environment: `make test`

### Faster Testing

You can run tests in parallel with pytest-xdist:

```bash
poetry run pytest -n auto -q
```

If parallel runs cause issues, run tests serially for debugging with `make test-serial`.

For detailed offline commands, see [`docs/python_setup.md`](docs/python_setup.md).

## Dependency Management with Wheels

### Installing Dependencies Offline

The project uses pre-built wheels for offline dependency installation. These wheels are organized by Python version and platform to ensure compatibility.

#### Installing Dependencies with Wheels

Once you have wheels available for your Python version and platform, you can install dependencies without internet access:

```bash
# Use the Makefile command for automatic platform detection
make install-offline

# Or manually for a specific Python version and platform
python -m pip install --no-index --find-links=wheels/py312-linux-x64 -r requirements.txt
```

#### Building Wheels for Different Platforms

To build wheels for the current environment:
```bash
make build-wheels
```

To build wheels for Linux platforms (requires Docker):
```bash
make build-wheels-linux
```

This builds all dependencies, including platform-specific ones like psycopg2-binary.
After building wheels, you can test the offline installation with:
```bash
make test-wheels  # or ./scripts/test_offline_install.sh
```

#### Testing Offline Installation

Verify that the wheels installation works correctly:
```bash
make test-wheels
```

### Dev Dependency Wheels

Development tools are defined in `[tool.poetry.group.dev.dependencies]` inside
`pyproject.toml`. Generate wheels for these packages so they live in the same
`wheels/py<version>-<platform>/` directory as the runtime wheels. Use
`./scripts/build_dev_wheels.sh` (or extend `scripts/build_wheels.sh`) to build
the dev wheels for Python 3.12 on Linux.

Before running the test suite, install these dev wheels. You can list the
packages explicitly:

```bash
pip install --no-index --find-links=wheels/py312-linux-x64 \
    pytest pytest-mock pytest-asyncio pre-commit black isort \
    flake8 flake8-docstrings pytest-profiling pytest-xdist
```

Alternatively, maintain a `requirements-dev.txt` file with the dev packages and
install it in the same way:

```bash
pip install --no-index --find-links=wheels/py312-linux-x64 -r requirements-dev.txt
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

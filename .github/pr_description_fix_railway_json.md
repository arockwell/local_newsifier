# Fix Railway Deployment Configuration with PYTHONPATH

## Description

This PR updates the Railway deployment configuration to use PYTHONPATH instead of explicitly installing the package with pip. The initial PR removed `pip install -e .` but led to `ModuleNotFoundError: No module named 'local_newsifier'` because of the project's src-layout structure.

## Problem

The project uses a src-layout structure (`packages = [{include = "local_newsifier", from = "src"}]` in pyproject.toml), which means:
- Code lives in `src/local_newsifier/`
- But Python expects to find it as just `local_newsifier/` somewhere in its search paths
- Previously, `pip install -e .` resolved this by creating links in site-packages

## Solution

Instead of relying on pip to install the package, we're using the PYTHONPATH environment variable to tell Python where to find the modules:

```
PYTHONPATH=$PYTHONPATH:src uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
```

This approach:
1. Preserves the src-layout structure (which is a Python best practice)
2. Avoids unnecessary package installation during deployment
3. Explicitly declares the module location in the start command
4. Works well with Nixpacks' build process

## Testing

This change should fix the ModuleNotFoundError while maintaining clean separation between project layout and deployment requirements.

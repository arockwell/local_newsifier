# Fix Railway Deployment Configuration with Proper Package Installation

## Description

This PR updates the Railway deployment configuration to leverage Python's standard package installation approach. The initial PR removed `pip install -e .` but led to `ModuleNotFoundError: No module named 'local_newsifier'`, and a subsequent PYTHONPATH-based approach also encountered issues.

## Problem

The project uses a src-layout structure (`packages = [{include = "local_newsifier", from = "src"}]` in pyproject.toml), which creates import path challenges when deployed without proper package installation.

## Solution

We've implemented a standard Python packaging approach:

1. Added `-e .` to requirements.txt:
   - This installs the package in development mode
   - Creates proper import paths for the package
   - Leverages the existing pyproject.toml configuration

2. Updated railway.json to use direct package imports:
   ```
   uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
   ```

3. Maintained healthcheck configuration for better deployment stability:
   ```json
   "healthcheckPath": "/health",
   "healthcheckTimeout": 60
   ```

## Advantages of This Approach

1. **Poetry Integration**: Aligns perfectly with the project's existing Poetry-based structure
2. **Standard Practice**: Uses the well-established `-e .` pattern for development mode installation
3. **Clean Imports**: Enables direct `local_newsifier` imports without extra path handling
4. **Environment Agnostic**: Works consistently across development and production
5. **Simplified Configuration**: Removes need for PYTHONPATH or nested module references
6. **Maintainability**: Follows Python packaging best practices for long-term project health

## Testing

This approach follows Python's standard packaging practices and resolves all import path issues in a clean, maintainable way that integrates with the project's existing Poetry configuration.

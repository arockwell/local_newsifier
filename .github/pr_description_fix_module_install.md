# Fix Railway Deployment with Package Installation

## Problem

After merging PR #48, we still encountered a module import error when deploying to Railway:

```
ModuleNotFoundError: No module named 'local_newsifier'
```

Despite changing the import paths in Procfile and railway.json, the application still can't find the module in the Railway environment.

## Solution

Add an explicit package installation step to both Procfile and railway.json:

```diff
- web: uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
+ web: pip install -e . && uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
```

This ensures that the package is properly installed in the deployment environment before the application starts.

## Why This Approach Works

1. The `pip install -e .` command installs the package in development mode
2. It ensures the package is available in the Python path
3. It works with the existing package configuration in pyproject.toml:
   ```toml
   packages = [{include = "local_newsifier", from = "src"}]
   ```
4. It avoids having to modify the application code to use different import paths

## Testing

This approach has been tested on Railway and resolves the module import error while maintaining the same functionality.

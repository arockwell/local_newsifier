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

## Additional Requirements for Railway

To fully deploy the application on Railway, you must:

1. **Add the PostgreSQL plugin** to your Railway project
   - This automatically provisions a database and sets up the DATABASE_URL environment variable

2. **Database Connection**
   - The application is configured to use the DATABASE_URL environment variable when available
   - This is handled automatically in src/local_newsifier/config/settings.py:
     ```python
     @computed_field
     def DATABASE_URL(self) -> str:
         """Get the database URL based on environment."""
         # Check if DATABASE_URL is provided directly (common in Railway and other cloud platforms)
         env_db_url = os.environ.get("DATABASE_URL")
         if env_db_url:
             return env_db_url
             
         # Otherwise construct from individual components
         return (
             f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
             f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
         )
     ```

## Testing

This approach resolves the module import error, and with the PostgreSQL plugin properly set up, the application can connect to the database in the Railway environment.

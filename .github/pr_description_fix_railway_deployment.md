# Fix SQLModel Parameter Binding and Railway Deployment Issues

## Problem

Two key issues were preventing proper deployment to Railway:

1. **SQLModel Parameter Binding Error**: The web interface was raising a TypeError because parameters were being passed incorrectly to SQLModel's Session.exec() method.

2. **Module Import Error**: The application couldn't start on Railway due to incorrect import paths in the deployment configuration.

## Solution

### 1. SQLModel Parameter Binding Fix

Changed the parameter binding approach in system.py:

```python
# From (incorrect)
columns = session.exec(column_query, {"table_name": table_name}).all()

# To (correct)
column_query = column_query.bindparams(table_name=table_name)
columns = session.exec(column_query).all()
```

This fixes the "TypeError: Session.exec() takes 2 positional arguments but 3 were given" error.

### 2. Railway Deployment Configuration

- Updated import paths in Procfile and railway.json:
  ```
  # From
  uvicorn src.local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
  
  # To
  uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
  ```

- Added dynamic templates directory detection in main.py:
  ```python
  # Get the templates directory path - works in both development and production
  if os.path.exists("src/local_newsifier/api/templates"):
      # Development environment
      templates_dir = "src/local_newsifier/api/templates"
  else:
      # Production environment - use package-relative path
      templates_dir = str(pathlib.Path(__file__).parent / "templates")
  ```

These changes align with the Poetry package configuration in pyproject.toml:
```toml
packages = [{include = "local_newsifier", from = "src"}]
```

## Tested Scenarios

- Local development: Web interface works correctly
- Database queries: Parameters are properly bound 
- Path resolution: Dynamic template directory detection works in both environments

## Memory Bank Updates

Updated all memory bank files to document:
- Recent changes and fixes
- Deployment configuration details
- Key technical decisions
- Potential issues to watch for

## Steps for Railway Deployment

1. Create Railway project and add PostgreSQL plugin
2. Configure environment variables (POSTGRES_USER, etc.)
3. Link GitHub repository
4. Deploy application
5. Monitor logs and performance

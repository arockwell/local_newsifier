# Active Context: Local Newsifier

## Current Focus
- Web interface functionality with correct database interaction
- Deployment configuration for Railway
- Database schema management with Alembic

## Recent Changes
- Fixed SQLModel parameter binding issue in system.py
  - Changed from `session.exec(query, params)` to `session.exec(query.bindparams(...))`
  - SQLModel's Session.exec() method takes only one parameter (the query itself)
  - Parameters must be bound to the query object before execution

- Fixed Railway deployment issues
  - Updated import paths in Procfile and railway.json from `src.local_newsifier` to `local_newsifier`
  - Modified templates directory path in main.py to work in both development and production
  - Implemented a path detection mechanism to handle different environments

- Fixed Celery PostgreSQL transport issue
  - Updated CELERY_BROKER_URL to use SQLAlchemy transport prefix: `sqla+postgresql://...`
  - Added kombu-sqlalchemy package instead of the non-existent celery-sqlalchemy-transport
  - Resolved KeyError: 'No such transport: postgresql' error during Celery startup

## Technical Details

### Web Interface Status
- The web application is now working correctly
- Database tables can be viewed and explored through the browser
- Table details can be viewed with proper SQL queries

### Deployment Configuration
- Railway.json is properly configured:
  ```json
  {
    "build": {
      "builder": "NIXPACKS"
    },
    "deploy": {
      "startCommand": "uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT",
      "restartPolicyType": "ON_FAILURE",
      "restartPolicyMaxRetries": 3
    }
  }
  ```

- Procfile is set up for web process:
  ```
  web: uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
  ```

- Templates directory path is dynamically determined based on environment:
  ```python
  # Get the templates directory path - works both in development and production
  if os.path.exists("src/local_newsifier/api/templates"):
      # Development environment
      templates_dir = "src/local_newsifier/api/templates"
  else:
      # Production environment - use package-relative path
      templates_dir = str(pathlib.Path(__file__).parent / "templates")
  ```

- Environment variables needed for deployment:
  - POSTGRES_USER
  - POSTGRES_PASSWORD
  - POSTGRES_HOST
  - POSTGRES_PORT
  - POSTGRES_DB

## Key Decisions

### Query Parameter Binding
We identified that SQLModel requires a different approach to parameter binding than what was initially implemented. The correct pattern is:

```python
# Original problematic code
columns = session.exec(column_query, {"table_name": table_name}).all()

# Fixed approach
column_query = column_query.bindparams(table_name=table_name)
columns = session.exec(column_query).all()
```

This change was made in the system.py router to fix the "Session.exec() takes 2 positional arguments but 3 were given" error.

### Deployment Path Correction
When deploying to Railway, we encountered a "ModuleNotFoundError: No module named 'local_newsifier'" error. This was due to a mismatch between the package configuration in pyproject.toml and the import paths in the deployment configuration:

```toml
# In pyproject.toml
packages = [{include = "local_newsifier", from = "src"}]
```

The proper way to reference the module in Procfile and railway.json is `local_newsifier.api.main:app`, not `src.local_newsifier.api.main:app`.

## Next Steps

### For Railway Deployment
1. Create a Railway project and add the PostgreSQL plugin
2. Configure the required environment variables
3. Link the GitHub repository to Railway using the main branch or the add-web-api branch
4. Deploy the application - Railway will automatically detect the configuration from railway.json and Procfile
5. Verify that the web interface works correctly in production
6. Monitor logs for any unexpected errors or issues

### Potential Issues to Watch For
1. Database connection issues - ensure environment variables are correctly set
2. Template rendering problems - verify paths are correctly resolved
3. Static file serving - may need additional configuration if static assets are added later

### For Further Development
1. Add more visualization options for trends and entity relationships
2. Improve entity resolution accuracy
3. Implement scheduled scraping and analysis
4. Add user authentication for admin functions

## Key Learnings
1. SQLModel has different parameter binding requirements compared to SQLAlchemy
2. Parameter binding needs to happen before passing the query to session.exec()
3. Railway deployment requires proper configuration of both railway.json and Procfile
4. Database connection depends on environment variables being correctly set

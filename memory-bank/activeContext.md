# Active Context: Local Newsifier

## Current Focus
- Web interface functionality with correct database interaction
- Deployment configuration for Railway
- Database schema management with Alembic
- SQLAlchemy session management in asynchronous tasks

## Recent Changes
- Fixed "No task function available" errors in CLI feed processing
  - Added `direct_process_article()` function to CLI command module to bypass Celery
  - Passed the function to `process_feed()` as task_queue_func parameter
  - Implemented synchronous article processing for CLI operations
  - Added a --no-process option to skip article processing if needed
  - Added detailed console output for article processing status

- Fixed circular dependency issue in RSS feed processing (NoneType error)
  - Added `register_article_service()` function to `rss_feed_service.py`
  - Updated `tasks.py` to register the initialized article_service with rss_feed_service
  - Resolved the 'NoneType' object has no attribute 'create_article_from_rss_entry' error
  - Prevents null reference when RSSFeedService falls back to importing article_service directly

- Fixed SQLAlchemy "Instance is not bound to a Session" error in RSS feed processing
  - Modified `ArticleService.create_article_from_rss_entry()` to return an ID instead of SQLModel object
  - Updated `fetch_rss_feeds` task to work with article IDs instead of objects
  - Updated tests to reflect these changes
  - Prevents session detachment issues when passing database objects between contexts

- Fixed SQLModel parameter binding issue in system.py
  - Changed from `session.exec(query, params)` to `session.exec(query.bindparams(...))`
  - SQLModel's Session.exec() method takes only one parameter (the query itself)
  - Parameters must be bound to the query object before execution

- Fixed Railway deployment issues
  - Updated import paths in Procfile and railway.json from `src.local_newsifier` to `local_newsifier`
  - Modified templates directory path in main.py to work in both development and production
  - Implemented a path detection mechanism to handle different environments

- Changed Celery broker from PostgreSQL to Redis
  - Switched CELERY_BROKER_URL and CELERY_RESULT_BACKEND to use Redis: `redis://localhost:6379/0`
  - Removed PostgreSQL-specific transport configuration (no longer needed)
  - Added redis package to dependencies
  - Simplified Celery configuration with natively supported broker

## Technical Details

### Web Interface Status
- The web application is now working correctly
- Database tables can be viewed and explored through the browser
- Table details can be viewed with proper SQL queries

### Deployment Configuration
- Railway.json is properly configured with separate process settings for web, worker, and beat:
  ```json
  {
    "deploy": {
      "restartPolicyType": "ON_FAILURE",
      "restartPolicyMaxRetries": 3,
      "processes": {
        "web": {
          "healthcheckPath": "/health",
          "healthcheckTimeout": 60,
          "command": "bash scripts/init_spacy_models.sh && bash scripts/init_alembic.sh && alembic upgrade head && python -m uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT"
        },
        "worker": {
          "healthcheckEnabled": false,
          "command": "bash scripts/init_spacy_models.sh && bash scripts/init_celery_worker.sh --concurrency=2"
        },
        "beat": {
          "healthcheckEnabled": false,
          "command": "bash scripts/init_spacy_models.sh && bash scripts/init_celery_beat.sh"
        }
      }
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
  - CELERY_BROKER_URL (Redis URL for production - need to provision Redis in Railway)
  - CELERY_RESULT_BACKEND (optional - defaults to broker URL)

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

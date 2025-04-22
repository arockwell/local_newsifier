# Technical Context: Local Newsifier

## Technology Stack

### Backend Technologies
- **Python**: Main programming language
- **FastAPI**: Web framework for the API and web interface
- **SQLModel**: SQL ORM for database interaction
- **PostgreSQL**: Database for persistent storage
- **Alembic**: Database migration tool for schema versioning
- **Celery**: Asynchronous task queue for background processing

### Frontend Technologies
- **Jinja2 Templates**: Server-side rendering for web interface
- **HTML/CSS**: Basic styling and structure
- **Bootstrap**: UI framework for responsive design

### Data Processing
- **Text Processing**: For entity extraction and analysis
- **Sentiment Analysis**: For determining article sentiment
- **Trend Analysis**: For identifying patterns and trends

## Development Environment
- **Poetry**: Dependency management
- **Pytest**: Testing framework
- **GitHub**: Version control

## Deployment
- **Railway**: Cloud platform for application deployment
- **Nixpacks**: Build system used by Railway
- **Uvicorn**: ASGI server for running the FastAPI application

## Database Schema
The database consists of several key tables:
- **articles**: Stores article data
- **entities**: Tracks extracted entities
- **canonical_entities**: Normalized entity references
- **analysis_results**: Stores analysis output

## Key Technical Insights

### SQLModel Parameter Binding
SQLModel's Session.exec() method only takes one parameter (the query itself). Parameters must be bound to the query object before execution using `.bindparams()`:

```python
# Incorrect approach - causes "TypeError: Session.exec() takes 2 positional arguments but 3 were given"
columns = session.exec(query, {"param": value}).all()

# Correct approach
query = query.bindparams(param=value)
columns = session.exec(query).all()
```

## Celery Integration

The Local Newsifier uses Celery for asynchronous task processing to handle resource-intensive operations without blocking the main application flow.

### Architecture
- **Celery Application**: Configured in `src/local_newsifier/celery_app.py`
- **Task Definitions**: Defined in `src/local_newsifier/tasks.py`
- **Message Broker**: PostgreSQL (same database as the application)
- **Result Backend**: PostgreSQL (same database as the application)
- **Task Scheduler**: Celery Beat for periodic tasks
- **Workers**: Celery workers that execute the tasks

### Key Tasks
1. **Process Article**: Asynchronously processes articles to extract entities and analyze context
   ```python
   from local_newsifier.tasks import process_article
   task = process_article.delay(article_id)
   ```

2. **Fetch RSS Feeds**: Fetches and processes articles from RSS feeds in the background
   ```python
   from local_newsifier.tasks import fetch_rss_feeds
   task = fetch_rss_feeds.delay(["https://example.com/feed1"])
   ```

3. **Analyze Entity Trends**: Performs trend analysis on entities over specified time periods
   ```python
   from local_newsifier.tasks import analyze_entity_trends
   task = analyze_entity_trends.delay(time_interval="day", days_back=7)
   ```

### Periodic Tasks
Celery Beat is used to schedule periodic tasks:
- Hourly RSS feed fetching
- Daily entity trend analysis

### Development
For local development, the Makefile provides several commands:
```bash
# Run Celery worker
make run-worker

# Run Celery Beat
make run-beat

# Run both worker and beat in separate processes
make run-all-celery
```

### Railway Deployment Configuration
The application is configured for Railway deployment using:
1. **railway.json**: Contains build and deployment settings for multi-process deployment
   ```json
   {
     "deploy": {
       "healthcheckPath": "/health",
       "healthcheckTimeout": 60,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 3,
       "processes": {
         "web": "bash scripts/init_alembic.sh && alembic upgrade head && python -m uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT",
         "worker": "bash scripts/init_celery_worker.sh --concurrency=2",
         "beat": "bash scripts/init_celery_beat.sh"
       }
     }
   }
   ```

2. **Procfile**: Specifies the web, worker, and beat processes
   ```
   web: bash scripts/init_alembic.sh && alembic upgrade head && python -m uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
   worker: bash scripts/init_celery_worker.sh --concurrency=2
   beat: bash scripts/init_celery_beat.sh
   ```

3. **Environment Variables**: Required for database connection
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - POSTGRES_HOST
   - POSTGRES_PORT
   - POSTGRES_DB

# Technical Context: Local Newsifier

## Technology Stack

### Backend Technologies
- **Python**: Main programming language
- **FastAPI**: Web framework for the API and web interface
- **SQLModel**: SQL ORM for database interaction
- **PostgreSQL**: Database for persistent storage
- **Alembic**: Database migration tool for schema versioning
- **Celery**: Asynchronous task queue for background processing
- **Redis**: Message broker and result backend for Celery
- **Apify Client**: Integration with Apify web scraping platform

### Frontend Technologies
- **Jinja2 Templates**: Server-side rendering for web interface
- **HTML/CSS**: Basic styling and structure
- **Bootstrap**: UI framework for responsive design

### Data Processing
- **Text Processing**: For entity extraction and analysis
- **Sentiment Analysis**: For determining article sentiment
- **Trend Analysis**: For identifying patterns and trends
- **spaCy**: NLP library for entity extraction and text processing

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
- **rss_feeds**: Stores RSS feed sources
- **feed_processing_logs**: Tracks RSS feed processing history
- **apify_source_configs**: Stores Apify scraper configurations
- **apify_jobs**: Tracks Apify scraping job runs
- **apify_dataset_items**: Stores raw data from Apify scraping jobs

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

### SQLAlchemy Session Management
SQLAlchemy requires careful handling of session lifecycles to avoid "Instance is not bound to a Session" errors:

1. **Session Scopes**: Objects are only usable within the session scope where they were retrieved/created:

```python
# Correct pattern - use objects within session scope
with SessionManager() as session:
    article = session.get(Article, article_id)
    # Use article within this block
    result = process_article_data(article)  # Pass data, not ORM objects
    return result
```

2. **Object Detachment**: When a session closes, objects become "detached" and accessing lazy-loaded attributes fails:

```python
# Problematic pattern that causes "Instance is not bound to a Session" errors
with SessionManager() as session:
    article = session.get(Article, article_id)
# Session closed here
article.entities  # ERROR! Accessing relationship after session closed
```

3. **Solutions**: Several approaches can solve this:
   - Return IDs instead of ORM objects from functions/methods
   - Eager load relationships with `selectinload` before session closes
   - Set `expire_on_commit=False` on sessions
   - Explicitly refresh objects in new sessions when needed

## Celery Integration

The Local Newsifier uses Celery for asynchronous task processing to handle resource-intensive operations without blocking the main application flow.

### Architecture
- **Celery Application**: Configured in `src/local_newsifier/celery_app.py`
- **Task Definitions**: Defined in `src/local_newsifier/tasks.py`
- **Message Broker**: Redis - efficient, in-memory data store optimized for messaging
- **Result Backend**: Redis - same instance used for storing task results
- **Task Scheduler**: Celery Beat for periodic tasks
- **Workers**: Celery workers that execute the tasks

### Critical Configuration
- **Redis Configuration**:
  - Default URL: `redis://localhost:6379/0`
  - Requires the `redis` package
  - Redis is natively supported by Celery without additional adapters
  - Same Redis instance can be used for both broker and result backend

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

4. **Process Apify Dataset**: Processes data from Apify web scraping jobs
   ```python
   from local_newsifier.tasks import process_apify_dataset
   task = process_apify_dataset.delay(job_id)
   ```

### Periodic Tasks
Celery Beat is used to schedule periodic tasks:
- Hourly RSS feed fetching
- Daily entity trend analysis
- Regular Apify actor runs based on configured schedules

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
   - REDIS_URL (for Celery broker and backend)
   - APIFY_TOKEN (for Apify web scraping integration)

## Apify Integration

The Local Newsifier integrates with the Apify web scraping platform to automate content collection from websites.

### Apify Components
- **ApifyService**: Service class for interacting with the Apify API
- **Apify Models**: SQLModel database models for storing Apify-related data
- **CLI Commands**: Command-line interface for Apify operations

### Apify Workflow
1. Configure scraping sources in the `apify_source_configs` table
2. Run Apify actors to scrape web content
3. Store the raw scraping results in the `apify_dataset_items` table
4. Process the raw data into articles and entities

### CLI Commands
```bash
# Test Apify API connection
poetry run python -m local_newsifier.cli.main apify test

# Run an Apify actor
poetry run python -m local_newsifier.cli.main apify run-actor apify/web-scraper --input input.json

# Get data from an Apify dataset
poetry run python -m local_newsifier.cli.main apify get-dataset DATASET_ID

# Scrape content from a URL
poetry run python -m local_newsifier.cli.main apify scrape-content https://example.com
```
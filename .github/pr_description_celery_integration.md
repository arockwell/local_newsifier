# Celery Integration with PostgreSQL for Asynchronous Tasks

This PR implements GitHub issue #59, adding Celery with PostgreSQL as both the message broker and result backend for handling asynchronous task processing in the Local Newsifier project.

## Overview

The implementation provides a robust asynchronous task processing system that enables:
- Processing resource-intensive operations in the background
- Scheduled periodic tasks (via Celery Beat)
- Task status tracking and result retrieval
- A web interface for task submission and monitoring

## Implementation Details

### New Files

- **Configuration**
  - `src/local_newsifier/celery_app.py`: Celery application configuration

- **Task Definitions**
  - `src/local_newsifier/tasks.py`: Core task implementations

- **API Endpoints**
  - `src/local_newsifier/api/routers/tasks.py`: API endpoints for task management
  - `src/local_newsifier/api/templates/tasks_dashboard.html`: Task dashboard UI

- **Testing & Demo**
  - `tests/tasks/test_tasks.py`: Unit tests for Celery tasks
  - `scripts/demo_celery_tasks.py`: Demo script for testing task submission

- **Documentation**
  - `docs/celery_integration.md`: Comprehensive documentation

### Modified Files

- **Configuration Updates**
  - `src/local_newsifier/config/settings.py`: Added Celery configuration settings
  - `requirements.txt`: Added Celery dependencies

- **API Integration**
  - `src/local_newsifier/api/main.py`: Integrated tasks router
  - `src/local_newsifier/api/dependencies.py`: Added templates support for tasks

- **Deployment Configuration**
  - `Procfile`: Added worker and beat processes
  - `railway.json`: Updated for multi-process deployment

## Key Features

### 1. Asynchronous Article Processing

Long-running article processing operations now run asynchronously:
```python
from local_newsifier.tasks import process_article
task = process_article.delay(article_id)
```

### 2. Automated RSS Feed Fetching

Periodic task for fetching new articles from RSS feeds:
```python
from local_newsifier.tasks import fetch_rss_feeds
task = fetch_rss_feeds.delay(["https://example.com/feed1"])
```

### 3. Background Trend Analysis

Resource-intensive trend analysis runs in the background:
```python
from local_newsifier.tasks import analyze_entity_trends
task = analyze_entity_trends.delay(time_interval="day", days_back=7)
```

### 4. Task Status Tracking

Easy task status checking:
```python
from celery.result import AsyncResult
from local_newsifier.celery_app import app as celery_app
result = AsyncResult(task_id, app=celery_app)
```

### 5. API Endpoints for Task Management

- `POST /tasks/process-article/{article_id}`: Process an article
- `POST /tasks/fetch-rss-feeds`: Fetch RSS feeds
- `POST /tasks/analyze-entity-trends`: Analyze entity trends
- `GET /tasks/status/{task_id}`: Check task status
- `GET /tasks/`: Task dashboard UI

## Architecture

PostgreSQL serves as both the message broker and result backend for Celery:
- Eliminates the need for Redis or RabbitMQ
- Simplifies deployment with just one database service
- Provides durable storage for task results
- Works seamlessly with the existing database connection settings

## Testing

### Running Tests

Run the unit tests with:
```bash
pytest tests/tasks/test_tasks.py
```

### Manual Testing

1. Run a Celery worker:
```bash
celery -A local_newsifier.celery_app worker --loglevel=info
```

2. Use the demo script:
```bash
python scripts/demo_celery_tasks.py --wait
```

3. Test via the API:
```bash
curl -X POST "http://localhost:8000/tasks/process-article/1"
```

## Deployment

The PR updates deployment configurations for Railway:
- Added worker and beat processes to Procfile
- Updated railway.json with multi-process configuration
- Configured for shared database connection across processes

## Documentation

Comprehensive documentation is provided in `docs/celery_integration.md`, covering:
- Architecture overview
- Configuration details
- Available tasks
- Task creation guide
- Testing instructions
- Deployment notes
- Troubleshooting tips

## Future Improvements

Potential future enhancements:
- Add task result archiving for database size management
- Implement more sophisticated monitoring with Flower
- Add task prioritization
- Support for task chaining and grouping

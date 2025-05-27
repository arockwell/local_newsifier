# Background Tasks Migration Guide

## Overview

This guide describes the new background task system that replaces Celery in the Local Newsifier project. The new system uses FastAPI Background Tasks for simple async operations and a lightweight scheduler for periodic tasks.

## Key Components

### 1. Synchronous Task Functions (`tasks_sync.py`)

All task logic has been moved to synchronous functions that can be called directly:

- `process_article_sync(article_id)` - Process a single article
- `fetch_rss_feeds_sync(feed_urls, process_articles)` - Fetch and process RSS feeds
- `cleanup_old_articles_sync(days)` - Clean up old articles (placeholder)
- `update_entity_profiles_sync()` - Update entity profiles (placeholder)

### 2. FastAPI Background Tasks (`/background-tasks/*`)

The new API endpoints allow submitting tasks for background processing:

```bash
# Process an article
curl -X POST http://localhost:8000/background-tasks/process-article/123

# Fetch RSS feeds
curl -X POST http://localhost:8000/background-tasks/fetch-feeds \
  -H "Content-Type: application/json" \
  -d '{"process_articles": true}'

# Check task status
curl http://localhost:8000/background-tasks/status/{task_id}

# List active tasks
curl http://localhost:8000/background-tasks/active
```

### 3. Simple Scheduler (`scheduler.py`)

A lightweight scheduler replaces Celery Beat for periodic tasks:

```python
# Default schedule (matches current Celery Beat config):
- Fetch RSS feeds every hour
- Clean up old articles daily at 2 AM
- Update entity profiles every 6 hours
```

Enable the scheduler by setting `ENABLE_SCHEDULER=true` in your environment.

## Migration Steps

### For Existing Code Using Celery

1. **Replace `.delay()` calls with API calls:**

```python
# Old (Celery)
from local_newsifier.tasks import process_article
process_article.delay(article_id)

# New (Background Tasks API)
import requests
response = requests.post(
    f"http://localhost:8000/background-tasks/process-article/{article_id}"
)
task_id = response.json()["task_id"]
```

2. **Or use sync functions directly:**

```python
# Direct synchronous call
from local_newsifier.tasks_sync import process_article_sync
result = process_article_sync(article_id)
```

3. **For FastAPI endpoints, use BackgroundTasks:**

```python
from fastapi import BackgroundTasks

@router.post("/process")
def process_endpoint(
    article_id: int,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_article_sync, article_id)
    return {"status": "processing"}
```

### Testing the New System

Use the CLI commands to test background task processing:

```bash
# Process a single article
nf test-background process-article 123

# Fetch feeds
nf test-background fetch-feeds --process-articles

# List active tasks
nf test-background list-active

# Check task status
nf test-background status {task_id}
```

## Configuration

### Environment Variables

- `ENABLE_SCHEDULER`: Set to `true` to enable the built-in scheduler
- `ARTICLE_PROCESSING_TIMEOUT`: Timeout for article processing (default: 600 seconds)
- `RSS_FEED_URLS`: Default RSS feeds to process (comma-separated)

### Deployment Changes

1. **Remove Celery processes from deployment:**
   - Remove `worker` process from `railway.json`
   - Remove `beat` process from `railway.json`
   - Remove Celery initialization scripts

2. **Update environment:**
   - Set `ENABLE_SCHEDULER=true` for production
   - Remove `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`
   - Redis is no longer required (unless used elsewhere)

## Benefits

1. **Simpler Architecture**: No separate worker processes or message broker
2. **Easier Debugging**: All code runs in the same process
3. **Lower Resource Usage**: No Redis/RabbitMQ required
4. **Native Python**: Uses standard library and FastAPI features

## Limitations

1. **Task Persistence**: Tasks are not persisted across restarts (can be added with Redis/DB)
2. **Scalability**: Limited to single process (can be enhanced with thread pools)
3. **Monitoring**: Basic task status tracking (can be enhanced)

## Future Enhancements

1. **Persistent Task Storage**: Store task status in database or Redis
2. **Thread Pool Executor**: For CPU-intensive tasks
3. **Task Priorities**: Add priority queue for task processing
4. **Retry Logic**: Automatic retry with exponential backoff
5. **Task Chaining**: Support for dependent tasks

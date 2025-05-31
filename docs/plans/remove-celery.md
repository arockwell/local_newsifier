# Plan: Remove Celery from Local Newsifier Stack

## Overview
This document outlines the plan to remove Celery from the Local Newsifier stack and replace it with FastAPI BackgroundTasks for all asynchronous processing needs.

## Current Celery Usage

### 1. Components Using Celery
- **Celery App**: `src/local_newsifier/celery_app.py` - Main Celery configuration
- **Task Definitions**: `src/local_newsifier/tasks.py` - Defines async tasks
- **API Integration**: `src/local_newsifier/api/routers/tasks.py` - Task submission endpoints
- **CLI Integration**: `src/local_newsifier/cli/commands/feeds.py` - Feed processing commands
- **Deployment**: Railway configuration includes worker and beat processes
- **Configuration**: Environment variables for broker/backend (Redis)

### 2. Current Tasks
1. **process_article**: Processes individual articles through the news pipeline
2. **fetch_rss_feeds**: Fetches and processes RSS feeds

### 3. Infrastructure Dependencies
- Redis as message broker and result backend
- Celery worker process for task execution
- Celery beat process for scheduled tasks

## Recommended Solution: FastAPI BackgroundTasks

### Why FastAPI BackgroundTasks?
**Pros:**
- Built into FastAPI, no additional dependencies
- Simple to implement and maintain
- Works well for the project's task requirements
- Integrates seamlessly with sync code
- No separate worker processes needed

**Limitations & Mitigations:**
- **Tasks don't survive restarts**: Acceptable for our use cases (article processing, feed fetching)
- **No built-in retry**: Can implement simple retry logic if needed
- **Not for long-running tasks**: Our tasks are typically short (< 1 minute)

### Implementation Pattern:
```python
from fastapi import BackgroundTasks

@router.post("/process-article/{article_id}")
def process_article_endpoint(
    article_id: int,
    background_tasks: BackgroundTasks,
    article_service: Annotated[ArticleService, Depends(get_article_service)]
):
    # Queue the task
    background_tasks.add_task(
        article_service.process_article_background,
        article_id
    )
    return {"status": "processing", "article_id": article_id}
```

### Service Method Pattern:
```python
class ArticleService:
    def process_article_background(self, article_id: int):
        """Background task for article processing."""
        try:
            # Process the article
            with self.session_factory() as session:
                article = self.article_crud.get(session, article_id)
                if article:
                    # Perform processing...
                    logger.info(f"Processed article {article_id}")
        except Exception as e:
            logger.error(f"Failed to process article {article_id}: {e}")
```

### Handling Scheduled Tasks

For scheduled tasks (replacing Celery Beat), we have several options:

1. **Simple Cron Jobs**: Use system cron to call API endpoints
   ```bash
   # crontab entry to fetch RSS feeds every hour
   0 * * * * curl -X POST http://localhost:8000/api/feeds/fetch-all
   ```

2. **FastAPI + APScheduler** (if more control needed):
   ```python
   from apscheduler.schedulers.background import BackgroundScheduler

   scheduler = BackgroundScheduler()

   @app.on_event("startup")
   def start_scheduler():
       scheduler.add_job(
           fetch_all_feeds,
           'interval',
           hours=1,
           id='fetch_feeds'
       )
       scheduler.start()
   ```

3. **Railway Cron Jobs**: Use Railway's built-in cron job support

## Migration Plan

### Phase 1: Assessment and Preparation
1. **Analyze Task Requirements**
   - Document average task duration
   - Identify which tasks need persistence
   - Determine retry requirements
   - Map scheduled task needs

2. **Create Migration Strategy**
   - Identify tasks that can use FastAPI BackgroundTasks
   - Identify tasks that need async processing
   - Plan for scheduled task replacement

### Phase 2: Implement FastAPI BackgroundTasks

#### 2.1 Convert Celery Tasks to Background Methods
```python
# Before (Celery task)
@app.task(bind=True, base=BaseTask)
def process_article(self, article_id: int) -> Dict:
    # Task implementation
    pass

# After (Service method for BackgroundTasks)
class ArticleService:
    def process_article_background(self, article_id: int) -> Dict:
        """Process article in background (sync)."""
        with self.session_factory() as session:
            # Implementation here
            pass
```

#### 2.2 Update API Endpoints
```python
# Before (using Celery)
@router.post("/process-article/{article_id}")
def process_article_endpoint(article_id: int):
    task = process_article.delay(article_id)
    return {"task_id": task.id}

# After (using BackgroundTasks)
@router.post("/process-article/{article_id}")
def process_article_endpoint(
    article_id: int,
    background_tasks: BackgroundTasks,
    article_service: Annotated[ArticleService, Depends(get_article_service)]
):
    background_tasks.add_task(
        article_service.process_article_background,
        article_id
    )
    return {"status": "processing", "article_id": article_id}
```

#### 2.3 Handle Scheduled Tasks
```python
# Create API endpoints for scheduled tasks
@router.post("/feeds/fetch-all")
def fetch_all_feeds(
    background_tasks: BackgroundTasks,
    feed_service: Annotated[FeedService, Depends(get_feed_service)]
):
    """Fetch all RSS feeds - can be called by cron/scheduler."""
    background_tasks.add_task(feed_service.fetch_all_feeds)
    return {"status": "fetching feeds"}
```

### Phase 3: Update Infrastructure

#### 3.1 Remove Celery Dependencies
```toml
# pyproject.toml - Remove these dependencies
# celery = "^5.3.4"
# redis = "^5.0.1"  # If only used for Celery
```

#### 3.2 Update Deployment Configuration
```json
{
  "deploy": {
    "processes": {
      "web": {
        "command": "... uvicorn local_newsifier.api.main:app ..."
      }
      // Remove worker and beat processes
    }
  }
}
```

#### 3.3 Update Environment Variables
Remove:
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

### Phase 4: Code Migration

#### 4.1 Update Task Implementations
```python
# Before (Celery task)
@app.task(bind=True, base=BaseTask)
def process_article(self, article_id: int) -> Dict:
    # Task implementation
    pass

# After (Async function)
async def process_article(article_id: int) -> Dict:
    async with get_async_session() as session:
        article_service = ArticleService(session)
        return await article_service.process_article(article_id)
```

### Phase 4: Update CLI Commands

Since the CLI is migrating to HTTP calls, it will simply call the API endpoints:

```python
# CLI command using HTTP client
def process_feeds():
    response = requests.post(f"{API_URL}/feeds/fetch-all")
    if response.ok:
        click.echo("Feed fetching initiated")
    else:
        click.echo(f"Error: {response.text}")
```

### Phase 5: Testing and Validation

1. **Update Tests**
   - Remove Celery-specific test fixtures
   - Update task tests to use async patterns
   - Test new task manager functionality

2. **Performance Testing**
   - Compare task execution times
   - Monitor memory usage
   - Test concurrent task handling

3. **Error Handling**
   - Implement retry logic where needed
   - Add proper error logging
   - Test failure scenarios

### Phase 6: Deployment

1. **Staged Rollout**
   - Deploy with both systems running
   - Gradually migrate tasks
   - Monitor for issues

2. **Cleanup**
   - Remove Celery configuration files
   - Remove Celery-specific scripts
   - Update documentation

## Implementation Timeline

- **Week 1**: Assessment and preparation
- **Week 2**: Implement async task manager and scheduler
- **Week 3**: Migrate simple tasks to BackgroundTasks
- **Week 4**: Migrate complex tasks to async implementation
- **Week 5**: Update tests and documentation
- **Week 6**: Deploy and monitor

## Benefits of Removing Celery

1. **Reduced Complexity**: No separate worker processes or message broker
2. **Fewer Dependencies**: Remove Celery and Redis dependencies
3. **Simplified Deployment**: Single web process handles everything
4. **Better Integration**: Native FastAPI patterns throughout
5. **Lower Resource Usage**: No Redis, no worker processes
6. **Easier Debugging**: All code runs in the same process

## Timeline

- **Week 1**: Implement BackgroundTasks for existing Celery tasks
- **Week 2**: Update deployment configuration and remove dependencies
- **Week 3**: Testing and monitoring
- **Week 4**: Documentation and cleanup

## Conclusion

FastAPI BackgroundTasks provides all the functionality needed for Local Newsifier's task processing requirements. This simpler architecture reduces operational complexity while maintaining all necessary features.

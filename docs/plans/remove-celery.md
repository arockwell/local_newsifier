# Plan: Remove Celery from Local Newsifier Stack

## Overview
This document outlines a plan to remove Celery from the Local Newsifier stack and replace it with alternative approaches for asynchronous task processing.

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

## Proposed Alternatives

### Option 1: FastAPI Background Tasks (Recommended for Simple Cases)
**Pros:**
- Built into FastAPI, no additional dependencies
- Simple to implement for short-running tasks
- Works well for fire-and-forget operations

**Cons:**
- Not suitable for long-running tasks
- No built-in retry mechanism
- Limited monitoring capabilities
- Tasks don't survive server restarts

**Implementation:**
```python
from fastapi import BackgroundTasks

@router.post("/process-article/{article_id}")
async def process_article_endpoint(
    article_id: int,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_article_sync, article_id)
    return {"status": "processing"}
```

### Option 2: Native Async with asyncio (Recommended)
**Pros:**
- No external dependencies
- Leverages Python's native async capabilities
- Good for I/O-bound operations
- Can use asyncio.create_task for concurrent operations

**Cons:**
- Tasks don't survive process restarts
- No built-in distribution across workers
- Need custom implementation for retries/scheduling

**Implementation:**
```python
import asyncio
from typing import Dict, Set

# In-memory task tracking
active_tasks: Dict[str, asyncio.Task] = {}

@router.post("/process-article/{article_id}")
async def process_article_endpoint(article_id: int):
    task_id = str(uuid.uuid4())
    task = asyncio.create_task(process_article_async(article_id))
    active_tasks[task_id] = task
    return {"task_id": task_id, "status": "processing"}
```

### Option 3: Lightweight Task Queue (e.g., Huey, RQ)
**Pros:**
- Simpler than Celery
- Still provides distributed task processing
- Built-in retry mechanisms

**Cons:**
- Still requires external dependency
- Still needs Redis or similar backend

### Option 4: Database-Backed Job Queue
**Pros:**
- No additional infrastructure (uses existing PostgreSQL)
- Tasks persist across restarts
- Can implement custom retry logic

**Cons:**
- More complex to implement
- Potential database load concerns
- Need to implement worker processes

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

### Phase 2: Implement Alternative Solutions

#### 2.1 Replace Simple Tasks with BackgroundTasks
```python
# Convert simple fire-and-forget tasks
from fastapi import BackgroundTasks

async def process_article_background(article_id: int):
    """Background task for article processing"""
    # Use async service methods
    async with get_async_session() as session:
        service = ArticleService(session)
        await service.process_article(article_id)

@router.post("/process-article/{article_id}")
async def process_article_endpoint(
    article_id: int,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_article_background, article_id)
    return {"status": "queued", "article_id": article_id}
```

#### 2.2 Implement Async Task Manager
```python
# src/local_newsifier/services/task_manager.py
import asyncio
import uuid
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskInfo:
    def __init__(self, task_id: str, name: str):
        self.id = task_id
        self.name = name
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None

class AsyncTaskManager:
    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def submit_task(self, name: str, func, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        task_info = TaskInfo(task_id, name)
        self._tasks[task_id] = task_info

        task = asyncio.create_task(self._run_task(task_id, func, *args, **kwargs))
        self._running_tasks[task_id] = task

        return task_id

    async def _run_task(self, task_id: str, func, *args, **kwargs):
        task_info = self._tasks[task_id]
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = datetime.utcnow()

        try:
            result = await func(*args, **kwargs)
            task_info.result = result
            task_info.status = TaskStatus.COMPLETED
        except Exception as e:
            task_info.error = str(e)
            task_info.status = TaskStatus.FAILED
        finally:
            task_info.completed_at = datetime.utcnow()
            self._running_tasks.pop(task_id, None)

    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)
```

#### 2.3 Replace Scheduled Tasks
```python
# src/local_newsifier/services/scheduler.py
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional

class AsyncScheduler:
    def __init__(self):
        self._scheduled_tasks = []
        self._running = False

    def schedule_periodic(
        self,
        func: Callable,
        interval: timedelta,
        name: str
    ):
        """Schedule a function to run periodically"""
        self._scheduled_tasks.append({
            'func': func,
            'interval': interval,
            'name': name,
            'next_run': datetime.utcnow()
        })

    async def start(self):
        """Start the scheduler"""
        self._running = True
        while self._running:
            now = datetime.utcnow()

            for task in self._scheduled_tasks:
                if now >= task['next_run']:
                    asyncio.create_task(task['func']())
                    task['next_run'] = now + task['interval']

            await asyncio.sleep(60)  # Check every minute

    def stop(self):
        """Stop the scheduler"""
        self._running = False

# Usage in main.py
scheduler = AsyncScheduler()

# Schedule RSS feed fetching
scheduler.schedule_periodic(
    fetch_rss_feeds_async,
    timedelta(hours=1),
    "fetch_rss_feeds"
)

# Start scheduler on app startup
@app.on_event("startup")
async def start_scheduler():
    asyncio.create_task(scheduler.start())
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

#### 4.2 Update API Endpoints
```python
# Before
@router.post("/process-article/{article_id}")
async def process_article_endpoint(article_id: int):
    task = process_article.delay(article_id)
    return {"task_id": task.id}

# After
@router.post("/process-article/{article_id}")
async def process_article_endpoint(
    article_id: int,
    task_manager: AsyncTaskManager = Depends(get_task_manager)
):
    task_id = await task_manager.submit_task(
        "process_article",
        process_article,
        article_id
    )
    return {"task_id": task_id}
```

#### 4.3 Update CLI Commands
```python
# Before
from local_newsifier.tasks import fetch_rss_feeds

def process_feeds():
    task = fetch_rss_feeds.delay()
    click.echo(f"Task {task.id} submitted")

# After
import asyncio

async def process_feeds_async():
    await fetch_rss_feeds()

def process_feeds():
    asyncio.run(process_feeds_async())
    click.echo("Feeds processed")
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

1. **Reduced Complexity**: No need for separate worker processes
2. **Fewer Dependencies**: Remove Celery and potentially Redis
3. **Simplified Deployment**: Single process deployment
4. **Better Integration**: Native FastAPI/async patterns
5. **Lower Resource Usage**: No separate broker infrastructure

## Risks and Mitigation

1. **Task Persistence**: Tasks won't survive crashes
   - Mitigation: Implement database-backed queue for critical tasks

2. **Scalability**: Can't distribute tasks across multiple workers
   - Mitigation: Use load balancer for API instances

3. **Monitoring**: Loss of Celery's built-in monitoring
   - Mitigation: Implement custom metrics and logging

## Conclusion

Removing Celery is feasible for Local Newsifier given its relatively simple task requirements. The combination of FastAPI BackgroundTasks for simple operations and a custom async task manager for more complex needs provides a good balance of simplicity and functionality. This approach eliminates infrastructure dependencies while maintaining the ability to process tasks asynchronously.

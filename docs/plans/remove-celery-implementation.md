# Remove Celery Implementation Progress

## Phase 1: Assessment of Current Celery Usage ✓ COMPLETED

### Inventory of Celery Tasks

Based on analysis of the codebase, here are all the Celery tasks currently in use:

#### 1. **process_article** (tasks.py:113-172)
- **Purpose**: Process a single article through the news pipeline and entity tracking
- **Type**: Background processing task
- **Dependencies**:
  - NewsPipelineFlow
  - EntityTrackingFlow
  - Article CRUD operations
- **Execution Pattern**: Triggered after new articles are created (e.g., from RSS feeds)
- **Retry Requirements**: None specified, but should handle transient failures
- **Current Usage**: Called with `.delay()` from `fetch_rss_feeds` task

#### 2. **fetch_rss_feeds** (tasks.py:174-257)
- **Purpose**: Fetch and process articles from multiple RSS feeds
- **Type**: Scheduled/periodic task (likely)
- **Dependencies**:
  - RSSParser
  - Article CRUD operations
  - Article Service
  - Triggers `process_article` for each new article
- **Execution Pattern**: Can be scheduled or triggered manually
- **Retry Requirements**: Should handle network failures gracefully
- **Current Usage**: Can process multiple feeds in batch

### Current Infrastructure

1. **Celery Configuration** (celery_app.py):
   - Uses Redis/PostgreSQL as broker and result backend
   - JSON serialization
   - 1-hour task time limit
   - Worker prefetch multiplier = 1

2. **Deployment Processes** (railway.json):
   - **web**: FastAPI application
   - **worker**: Celery worker with concurrency=2
   - **beat**: Celery beat scheduler (for periodic tasks)

3. **Task Base Class** (BaseTask):
   - Provides session management
   - Lazy loading of services via dependency injection
   - Automatic session cleanup

### Task Analysis

#### Tasks Suitable for FastAPI Background Tasks:
1. **process_article** - Individual article processing can be handled as background tasks
2. **fetch_rss_feeds** (when triggered manually) - Can be converted to endpoint with background processing

#### Tasks Requiring Scheduled Execution:
1. **fetch_rss_feeds** (periodic) - Needs a scheduler replacement for regular feed updates

#### Task Dependencies:
- `fetch_rss_feeds` → creates articles → triggers `process_article` for each
- Both tasks use database sessions and various services

### Resource Requirements

1. **Concurrency**: Currently limited to 2 workers
2. **Memory**: Processing articles involves NLP models (spaCy)
3. **Network**: RSS feed fetching requires external HTTP calls
4. **Database**: Heavy database usage for article and entity storage

## Next Steps

### Phase 2 Implementation Plan

1. **Create sync versions of tasks**:
   - `process_article_sync()` - Direct function call version
   - `fetch_rss_feeds_sync()` - Direct function call version

2. **Implement FastAPI Background Tasks**:
   - Create endpoints that trigger background processing
   - Add task status tracking mechanism

3. **Implement Simple Scheduler**:
   - Use Python's `schedule` library for periodic tasks
   - Run in separate thread within the FastAPI app

4. **Add Task Management Endpoints**:
   - GET /tasks/{task_id}/status
   - GET /tasks/active
   - POST /tasks/cancel/{task_id}

### Migration Strategy

1. **Parallel Implementation**:
   - Keep Celery tasks intact
   - Add new sync implementations alongside
   - Feature flag to switch between implementations

2. **Testing Plan**:
   - Unit tests for sync task functions
   - Integration tests for background task execution
   - Performance comparison tests

3. **Monitoring Requirements**:
   - Task execution logs
   - Task duration metrics
   - Failure tracking

## Implementation Timeline

- Week 1: Complete assessment and create sync task functions ✓ COMPLETED
- Week 2: Implement FastAPI background tasks and scheduler
- Week 3: Add task management and monitoring
- Week 4: Testing and gradual rollout
- Week 5: Complete migration and remove Celery
- Week 6: Documentation and optimization

## Phase 2: Implementation Progress

### Completed Tasks (Phase 2, Week 1)

1. **Created Sync Task Functions** (`tasks_sync.py`):
   - ✓ `process_article_sync()` - Synchronous version of article processing
   - ✓ `fetch_rss_feeds_sync()` - Synchronous RSS feed fetching
   - ✓ `cleanup_old_articles_sync()` - Placeholder for article cleanup
   - ✓ `update_entity_profiles_sync()` - Placeholder for entity profile updates

2. **Implemented Simple Scheduler** (`scheduler.py`):
   - ✓ TaskScheduler class using Python's `schedule` library
   - ✓ Background thread execution for periodic tasks
   - ✓ Default schedule configuration matching Celery Beat
   - ✓ Task management and monitoring capabilities

3. **Created FastAPI Background Tasks Router** (`api/routers/background_tasks.py`):
   - ✓ POST `/background-tasks/process-article/{article_id}` - Process single article
   - ✓ POST `/background-tasks/fetch-feeds` - Fetch RSS feeds
   - ✓ GET `/background-tasks/status/{task_id}` - Check task status
   - ✓ GET `/background-tasks/active` - List active tasks
   - ✓ GET `/background-tasks/all` - List all tasks
   - ✓ DELETE `/background-tasks/cleanup` - Clean up completed tasks

4. **Updated FastAPI Application**:
   - ✓ Added background_tasks router to main app
   - ✓ Integrated scheduler into app lifespan
   - ✓ Added ENABLE_SCHEDULER setting for optional scheduler activation

### Next Steps (Phase 2, Week 2)

1. **Implement Robust Task Storage**:
   - Replace in-memory task storage with Redis or database
   - Add task persistence and recovery

2. **Add Thread Pool Executor**:
   - Implement concurrent task processing for heavy workloads
   - Add configuration for worker pool size

3. **Create Migration Helpers**:
   - Feature flags to switch between Celery and new system
   - Compatibility layer for existing code

4. **Testing**:
   - Unit tests for sync tasks
   - Integration tests for background task execution
   - Performance comparison with Celery

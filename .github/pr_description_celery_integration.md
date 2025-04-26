# Implement Celery Integration for Asynchronous Task Processing

## Overview
This PR implements asynchronous task processing with Celery for the Local Newsifier project as specified in issue #59. This integration allows us to handle resource-intensive operations like article processing, entity extraction, and trend analysis without blocking the main application flow.

## Key Changes

### Core Celery Components
- Added Celery application configuration using PostgreSQL as both broker and result backend
- Created task definitions for common operations:
  - Article processing
  - RSS feed fetching (with periodic scheduling)
  - Entity trend analysis (with periodic scheduling)
- Implemented a base task class with common database session management

### API Integration
- Added new API router for task management with endpoints:
  - POST `/tasks/process-article/{article_id}` - Process article asynchronously
  - POST `/tasks/fetch-rss-feeds` - Fetch and process RSS feeds
  - POST `/tasks/analyze-entity-trends` - Analyze entity trends
  - GET `/tasks/status/{task_id}` - Check task status
  - DELETE `/tasks/cancel/{task_id}` - Cancel a running task
- Created an interactive task dashboard with real-time task status updates
- Updated API dependencies and main application to support Celery integration

### Deployment Configuration
- Updated Procfile and railway.json for multi-process deployment (web, worker, beat)
- Added init scripts for Celery worker and beat processes
- Created Makefile with commands for running Celery components locally

### Testing and Documentation
- Added comprehensive unit tests for Celery tasks
- Created a demo script for testing task submission and monitoring
- Added detailed documentation on Celery integration
- Updated memory bank with Celery technical context

## Benefits
- Better resource utilization
- Improved scalability
- Non-blocking user experience
- Ability to schedule periodic tasks like RSS feed fetching and trend analysis

## Testing Instructions
1. Install Redis or use the PostgreSQL broker (default configuration)
2. Run Celery worker: `make run-worker`
3. Run Celery Beat scheduler: `make run-beat`
4. Run the FastAPI application: `make run-api`
5. Visit the task dashboard at `/tasks/`
6. Submit various tasks and monitor their progress

## Related Issues
- Resolves #59: Implement Celery Integration for Asynchronous Task Processing

## Additional Notes
- Used PostgreSQL as both broker and result backend to simplify the architecture
- All long-running operations now have asynchronous task alternatives
- Added a browser-based task dashboard for easy task management
- Tasks can be scheduled periodically using Celery Beat

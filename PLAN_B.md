# PLAN B: Remove Celery and Implement Simple Task Processing

## Overview
Replace Celery with simpler alternatives that align with the sync architecture. This reduces infrastructure complexity and deployment requirements.

## Priority Tasks (4-6 weeks)

### Phase 1: Assess Current Celery Usage (Week 1)
1. **Inventory all Celery tasks**
   - Document each task in tasks.py
   - Identify task dependencies
   - Measure task execution patterns
   - Note scheduling requirements

2. **Analyze task requirements**
   - Which tasks need background processing?
   - Which can be converted to synchronous operations?
   - Which need scheduled execution?
   - What are retry requirements?

### Phase 2: Implement Replacement Solutions (Week 2-3)
1. **Convert simple tasks to FastAPI Background Tasks**
   ```python
   from fastapi import BackgroundTasks

   @router.post("/process-feed/{feed_id}")
   def process_feed(feed_id: int, background_tasks: BackgroundTasks):
       background_tasks.add_task(process_feed_sync, feed_id)
       return {"status": "processing"}
   ```

2. **Implement thread-based processing for heavy tasks**
   ```python
   from concurrent.futures import ThreadPoolExecutor

   executor = ThreadPoolExecutor(max_workers=4)

   def process_article_batch(article_ids: List[int]):
       futures = [executor.submit(process_article, id) for id in article_ids]
       return [f.result() for f in futures]
   ```

3. **Create simple scheduler for periodic tasks**
   ```python
   import schedule
   import threading

   def run_scheduled_tasks():
       schedule.every(1).hours.do(update_feeds)
       schedule.every(1).days.do(cleanup_old_articles)

       while True:
           schedule.run_pending()
           time.sleep(60)

   # Run in separate thread
   scheduler_thread = threading.Thread(target=run_scheduled_tasks)
   scheduler_thread.daemon = True
   scheduler_thread.start()
   ```

### Phase 3: Migration Implementation (Week 4-5)
1. **Update task processing**
   - Convert process_article_task to sync function
   - Convert analyze_entities_task to sync function
   - Convert update_feed_task to sync function
   - Implement proper error handling and retries

2. **Update API endpoints**
   - Modify endpoints to use new task processing
   - Add status tracking for background tasks
   - Implement task result retrieval

3. **Update deployment configuration**
   - Remove Celery worker from Procfile
   - Remove Celery beat from deployment
   - Update railway.json configuration
   - Remove Redis dependency (if only used for Celery)

### Phase 4: Testing and Monitoring (Week 6)
1. **Test all task replacements**
   - Unit tests for each converted task
   - Integration tests for task workflows
   - Performance tests for concurrent processing

2. **Implement monitoring**
   - Add logging for background tasks
   - Create task status endpoints
   - Monitor resource usage

3. **Documentation**
   - Update deployment guides
   - Document new task patterns
   - Create troubleshooting guide

## Benefits
- No Redis dependency
- No Celery broker/backend
- Simpler deployment (single process possible)
- Easier debugging and monitoring
- Native Python solutions

## Migration Strategy
1. Implement replacements alongside Celery
2. Gradually switch tasks to new system
3. Monitor for issues
4. Remove Celery once stable

## Success Criteria
- All tasks converted successfully
- No loss of functionality
- Improved or equal performance
- Simplified deployment
- Reduced infrastructure costs

# FastAPI Async/Sync Fix Implementation Plan

## Overview

This document outlines the plan to fix the async/sync context mixing issues causing application crashes. We have two main approaches, with Option 1 (Convert to Sync) being the recommended short-term fix.

## Option 1: Convert to Synchronous Endpoints (Recommended Short-term Fix)

### Why This Approach?
- Minimal code changes required
- Maintains existing service layer architecture
- Quick to implement and test
- Aligns with current database session patterns

### Implementation Steps

#### 1. Update System Router
```python
# src/local_newsifier/api/routers/system.py
# Change all async def to def

def health_check():  # Remove async
    return {"status": "healthy"}

def tables(  # Remove async
    session: Annotated[Session, Depends(get_session)]
):
    # Implementation remains the same
```

#### 2. Update Tasks Router
```python
# src/local_newsifier/api/routers/tasks.py
# Convert all endpoints from async to sync

def process_feeds(  # Remove async
    background_tasks: BackgroundTasks,
    feed_id: Optional[int] = None,
    article_service: Annotated[Any, Depends(get_article_service)],
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)]
):
    # Implementation remains the same
```

#### 3. Update Auth Router
```python
# src/local_newsifier/api/routers/auth.py
# Ensure consistency if any async endpoints exist
```

#### 4. Testing Required
- Unit tests for each endpoint
- Integration tests for API flows
- Load testing to ensure performance is acceptable
- Verify background tasks still function correctly

## Option 2: Full Async Migration (Long-term Solution)

### Implementation Steps

#### 1. Create Async Database Engine
```python
# src/local_newsifier/database/async_engine.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

async_engine = create_async_engine(
    database_url.replace("postgresql://", "postgresql+asyncpg://")
)
```

#### 2. Update Dependencies
```python
# src/local_newsifier/api/dependencies.py
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

#### 3. Create Async Service Providers
```python
async def get_article_service_async(
    session: Annotated[AsyncSession, Depends(get_async_session)]
):
    # Return async-compatible service
```

#### 4. Update CRUD Operations
- Convert all CRUD classes to support async operations
- Update query patterns to use `await session.execute()`
- Handle async context properly

## Recommended Approach

**Start with Option 1** for immediate stability:
1. Remove `async` from endpoint definitions
2. Test thoroughly
3. Deploy to fix crashes
4. Plan Option 2 migration separately

## Migration Timeline

### Phase 1: Immediate Fix (1-2 days)
- Implement Option 1
- Test all endpoints
- Deploy hotfix

### Phase 2: Async Migration Planning (1 week)
- Design async architecture
- Create migration plan
- Set up async testing framework

### Phase 3: Incremental Migration (2-4 weeks)
- Migrate one router at a time
- Maintain backward compatibility
- Comprehensive testing at each step

## Testing Strategy

### Before Deployment
```bash
# Run existing tests
make test

# Specific API tests
pytest tests/api/ -v

# Load testing
locust -f tests/load/api_load_test.py
```

### Monitoring After Fix
- Watch for any `contextmanager_in_threadpool` errors
- Monitor response times
- Check database connection pool usage
- Verify background tasks completion

## Rollback Plan

If issues arise after deployment:
1. Revert git commits
2. Redeploy previous version
3. Investigate specific failing endpoints
4. Apply targeted fixes

## Success Criteria

- No more async/sync context crashes
- All API endpoints respond successfully
- Background tasks process correctly
- Performance metrics remain acceptable
- Test suite passes completely

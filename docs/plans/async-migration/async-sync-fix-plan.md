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

## Option 2: Full Async Migration (DEPRECATED - DO NOT USE)

**⚠️ WARNING**: This option has been deprecated. The project is moving to sync-only implementations.

### Why This Option Was Rejected

1. **Production Crashes**: Mixing async/sync patterns caused severe production issues
2. **Complexity**: Async patterns add unnecessary complexity for minimal performance gain
3. **Maintenance**: Harder to debug and maintain async code
4. **Team Decision**: Project has decided to use sync-only patterns

### DO NOT IMPLEMENT THE FOLLOWING:
- Async database engines
- AsyncSession usage
- async/await patterns
- Async CRUD operations
- Async service providers

## Recommended Approach

**Use Option 1 (Sync-Only)** - This is the approved approach:
1. Remove `async` from endpoint definitions
2. Test thoroughly
3. Deploy to fix crashes
4. Continue with sync-only development

## Migration Timeline

### Phase 1: Immediate Fix (1-2 days)
- Implement Option 1 (sync-only)
- Test all endpoints
- Deploy hotfix

### Phase 2: Complete Sync Migration (1-2 weeks)
- Remove any remaining async patterns
- Update all services to sync-only
- Update documentation

### Phase 3: Maintain Sync Architecture (Ongoing)
- Ensure all new code is synchronous
- Regular code reviews to prevent async patterns
- Update developer guidelines

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

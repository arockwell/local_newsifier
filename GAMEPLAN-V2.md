# Gameplan V2: Fix Webhook Error & Migrate to FastAPI Native DI

## Objective
1. Fix the webhook async error by properly handling exceptions in sync code
2. Begin migration from fastapi-injectable to FastAPI's native dependency injection
3. Ensure all code remains sync-only (no async/await)

## Root Cause Analysis
The webhook error occurs because:
- HTTPException is raised inside a database session context manager
- FastAPI tries to clean up the sync generator in an async context
- The mismatch between sync code and async cleanup causes "generator didn't stop after throw()"

## Implementation Strategy

### Phase 1: Fix Immediate Webhook Error

#### Option A: Simple Session Provider (Preferred)
Replace the complex generator pattern with a simple dependency that returns a session:

```python
# In api/dependencies.py
def get_session() -> Session:
    """Get a database session using FastAPI's native DI."""
    engine = get_engine()
    if engine is None:
        raise HTTPException(status_code=500, detail="Database unavailable")

    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

#### Option B: Defer Exception Raising
Store errors and raise them after session cleanup:

```python
# In webhooks.py
def apify_webhook(...):
    error_to_raise = None

    # Process webhook
    result = webhook_service.handle_webhook(...)

    if result["status"] == "error":
        error_to_raise = HTTPException(400, detail=result["message"])

    # Session closes here

    if error_to_raise:
        raise error_to_raise
```

### Phase 2: Migrate to FastAPI Native DI

#### 1. Replace Injectable Providers with FastAPI Dependencies
Transform each injectable provider into a FastAPI dependency:

```python
# OLD: fastapi-injectable
@injectable(use_cache=False)
def get_article_service(...):
    return ArticleService(...)

# NEW: FastAPI native
def get_article_crud() -> CRUDArticle:
    return article  # singleton instance

def get_article_service(
    session: Annotated[Session, Depends(get_session)],
    article_crud: Annotated[CRUDArticle, Depends(get_article_crud)]
) -> ArticleService:
    return ArticleService(
        article_crud=article_crud,
        session_factory=lambda: session
    )
```

#### 2. Simplify Session Management
- Remove complex SessionManager and contextmanager patterns
- Use FastAPI's dependency injection for session lifecycle
- Keep everything sync (no AsyncSession)

#### 3. Update Endpoints
Replace injectable imports with native FastAPI dependencies:

```python
# OLD
from local_newsifier.di.providers import get_article_service

# NEW
from local_newsifier.api.dependencies import get_article_service

@router.get("/articles")
def list_articles(
    service: Annotated[ArticleService, Depends(get_article_service)]
):
    return service.get_all()
```

## Migration Order

1. **Fix webhook error first** (Option A or B)
2. **Create new dependencies.py** with FastAPI native dependencies
3. **Migrate one router at a time**:
   - Start with simple routers (system, auth)
   - Move to complex routers (tasks, webhooks)
4. **Update CLI to use new dependencies**
5. **Remove fastapi-injectable** once migration complete

## Benefits of This Approach

1. **Simpler**: FastAPI's native DI is well-documented and standard
2. **No Magic**: Clear dependency graph without @injectable decorators
3. **Better Errors**: FastAPI provides clear dependency resolution errors
4. **Sync-Only**: No risk of async/sync mismatches
5. **Testable**: Easy to override dependencies in tests

## Success Criteria

- [ ] Webhook returns 400 for validation errors (not 500)
- [ ] No "generator didn't stop after throw()" errors
- [ ] All endpoints use FastAPI native dependencies
- [ ] fastapi-injectable removed from requirements
- [ ] All tests pass
- [ ] Code is simpler and more maintainable

## Next Steps

1. Create a test that reproduces the webhook error
2. Implement Option A (simple session provider)
3. Verify the fix works
4. Start migrating providers one by one
5. Update documentation to reflect new patterns

# Async Migration Patterns and Best Practices

**⚠️ DEPRECATED**: This document is kept for historical reference only. The project uses sync-only patterns.

**IMPORTANT**: Do not use async patterns shown in this document. All new code must be synchronous.

## Common Patterns to Fix

### 1. Sync Session in Async Endpoint (Current Problem)

**Bad Pattern:**
```python
async def get_data(session: Session = Depends(get_session)):
    # This causes the crash - async function with sync session
    return session.query(Model).all()
```

**Good Pattern (RECOMMENDED - Sync Only):**
```python
def get_data(session: Session = Depends(get_session)):
    # Sync function with sync session - works fine
    return session.query(Model).all()
```

**Deprecated Pattern (DO NOT USE):**
```python
# DO NOT USE - Async patterns are deprecated
async def get_data(session: AsyncSession = Depends(get_async_session)):
    # This pattern is no longer supported
    result = await session.execute(select(Model))
    return result.scalars().all()
```

### 2. Context Manager Patterns

**Bad Pattern:**
```python
def get_service():
    with next(get_session()) as session:  # Sync context in dependency
        return Service(session)
```

**Good Pattern (RECOMMENDED - Sync Only):**
```python
def get_service(session: Session = Depends(get_session)):
    return Service(session)
```

**Deprecated Pattern (DO NOT USE):**
```python
# DO NOT USE - Async patterns are deprecated
async def get_service(session: AsyncSession = Depends(get_async_session)):
    return AsyncService(session)
```

### 3. Database Query Patterns

**Recommended Pattern (Sync Only):**
```python
def get_articles(session: Session):
    return session.exec(select(Article)).all()
```

**Deprecated Pattern (DO NOT USE):**
```python
# DO NOT USE - Async patterns are deprecated
async def get_articles(session: AsyncSession):
    result = await session.execute(select(Article))
    return result.scalars().all()
```

### 4. Transaction Patterns

**Recommended Pattern (Sync Only):**
```python
def create_with_transaction(session: Session, data: dict):
    with session.begin():
        obj = Model(**data)
        session.add(obj)
        session.flush()
        return obj
```

**Deprecated Pattern (DO NOT USE):**
```python
# DO NOT USE - Async patterns are deprecated
async def create_with_transaction(session: AsyncSession, data: dict):
    async with session.begin():
        obj = Model(**data)
        session.add(obj)
        await session.flush()
        return obj
```

## Service Layer Patterns

### Recommended Service Pattern (Sync Only)
```python
class ArticleService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_articles(self):
        with self.session_factory() as session:
            return session.exec(select(Article)).all()
```

### Deprecated Service Pattern (DO NOT USE)
```python
# DO NOT USE - Async patterns are deprecated
class AsyncArticleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_articles(self):
        result = await self.session.execute(select(Article))
        return result.scalars().all()
```

## Dependency Injection Patterns

### Recommended Pattern (Sync Only)
```python
@injectable(use_cache=False)
def get_article_crud(session: Session = Depends(get_session)):
    from local_newsifier.crud.article import CRUDArticle
    return CRUDArticle(Article)
```

### Deprecated Pattern (DO NOT USE)
```python
# DO NOT USE - Async patterns are deprecated
@injectable(use_cache=False)
async def get_article_crud_async(
    session: AsyncSession = Depends(get_async_session)
):
    from local_newsifier.crud.async_article import AsyncCRUDArticle
    return AsyncCRUDArticle(Article)
```

## Background Task Patterns

### Recommended Pattern (Sync Only)
```python
def process_data(
    background_tasks: BackgroundTasks,
    service: Service = Depends(get_service)
):
    # Add sync task
    background_tasks.add_task(sync_process_function, data)
    return {"status": "processing"}
```

### Deprecated Pattern (DO NOT USE)
```python
# DO NOT USE - Async patterns are deprecated
async def process_data(
    background_tasks: BackgroundTasks,
    service: AsyncService = Depends(get_async_service)
):
    # Add async task
    background_tasks.add_task(async_process_function, data)
    return {"status": "processing"}
```

## Common Pitfalls to Avoid

### 1. Mixing Async/Sync in Same Router
```python
# BAD - Don't mix in same router
router = APIRouter()

@router.get("/sync")
def sync_endpoint(): pass

@router.get("/async")
async def async_endpoint(): pass  # Confusing and error-prone
```

### 2. Forgetting await
```python
# BAD
async def get_data(session: AsyncSession):
    return session.execute(select(Model))  # Missing await!

# GOOD
async def get_data(session: AsyncSession):
    result = await session.execute(select(Model))
    return result.scalars().all()
```

### 3. Using Sync Libraries in Async Context
```python
# BAD
async def fetch_data():
    response = requests.get(url)  # Blocks event loop!

# GOOD
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
```

## Migration Checklist

- [ ] Identify all async endpoints
- [ ] Check their dependencies for sync patterns
- [ ] Decide on sync vs async approach per router
- [ ] Update dependencies consistently
- [ ] Update service layer if going async
- [ ] Update CRUD operations if going async
- [ ] Test thoroughly with concurrent requests
- [ ] Monitor for event loop blocking
- [ ] Update documentation
- [ ] Train team on chosen patterns

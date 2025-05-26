# Async Migration Plan for Local Newsifier

## Overview

This document outlines the comprehensive plan to migrate the Local Newsifier codebase from synchronous to fully asynchronous operations. The migration aims to improve performance, scalability, and resource utilization by leveraging Python's async/await capabilities throughout the application stack.

## Current State

The codebase is currently in a hybrid state:
- **Async**: FastAPI endpoints are defined as async functions
- **Sync**: All services, CRUD operations, tools, and database operations are synchronous
- **Problem**: Async endpoints call sync services, creating blocking operations and defeating the purpose of async

## Goals

1. **Full Async Stack**: Convert all I/O-bound operations to async
2. **Performance**: Improve response times and throughput
3. **Scalability**: Better handle concurrent requests and operations
4. **Resource Efficiency**: Reduce thread blocking and improve CPU utilization
5. **Maintainability**: Consistent async patterns throughout the codebase

## Migration Phases

### Phase 1: Foundation (Weeks 1-2)

#### 1.1 Database Layer
Convert the database layer to use async SQLAlchemy:

```python
# Current (sync)
from sqlmodel import Session, create_engine

engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session

# Target (async)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

async_engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
```

**Tasks:**
- [ ] Install async database drivers (asyncpg for PostgreSQL)
- [ ] Create async engine configuration
- [ ] Implement async session management
- [ ] Update database connection utilities
- [ ] Create migration utilities for gradual transition

#### 1.2 CRUD Base Class
Create async version of the CRUD base class:

```python
# New AsyncCRUDBase
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

ModelType = TypeVar("ModelType", bound=SQLModel)

class AsyncCRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
```

**Tasks:**
- [ ] Create AsyncCRUDBase class
- [ ] Implement all CRUD methods as async
- [ ] Add async query builders
- [ ] Create migration guide for CRUD classes

### Phase 2: External API Integration (Weeks 2-3)

#### 2.1 HTTP Client Migration
Replace `requests` with `httpx` for async HTTP calls:

```python
# Current (sync)
import requests

def fetch_content(url: str):
    response = requests.get(url)
    return response.text

# Target (async)
import httpx

async def fetch_content(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

**Tasks:**
- [ ] Replace requests with httpx in all services
- [ ] Update ApifyService to use async client
- [ ] Convert WebScraperTool to async
- [ ] Convert RSSParser to async
- [ ] Add connection pooling for HTTP clients

#### 2.2 Apify Integration
Convert ApifyService to fully async:

```python
class AsyncApifyService:
    def __init__(self):
        self.client = ApifyClientAsync()

    async def run_actor(self, actor_id: str, run_input: dict):
        actor = await self.client.actor(actor_id)
        run = await actor.call(run_input=run_input)
        return await run.wait_for_finish()

    async def get_dataset_items(self, dataset_id: str):
        dataset = await self.client.dataset(dataset_id)
        items = []
        async for item in dataset.iterate_items():
            items.append(item)
        return items
```

### Phase 3: Service Layer (Weeks 3-5)

#### 3.1 Service Migration Strategy
Convert services following this pattern:

```python
class ArticleService:
    # Keep sync methods for compatibility
    def process_article_sync(self, session: Session, url: str):
        # Existing sync implementation
        pass

    # Add async versions
    async def process_article(self, session: AsyncSession, url: str):
        # Async implementation
        article = await self._fetch_article_content(url)
        entities = await self._extract_entities(article.content)

        # Use async CRUD
        article_crud = AsyncArticleCRUD()
        saved_article = await article_crud.create(session, article)

        # Process entities concurrently
        entity_tasks = [
            self._process_entity(session, entity, saved_article.id)
            for entity in entities
        ]
        await asyncio.gather(*entity_tasks)

        return saved_article
```

**Migration Order:**
1. **ApifyService** - External API heavy
2. **RSSFeedService** - HTTP requests
3. **ArticleService** - Core business logic
4. **EntityService** - Database intensive
5. **AnalysisService** - Can leverage concurrent processing
6. **NewsPipelineService** - Orchestrates other services

#### 3.2 Dependency Injection Updates
Update FastAPI dependencies for async:

```python
# Current
def get_article_service(
    session: Annotated[Session, Depends(get_session)]
) -> ArticleService:
    return ArticleService(session)

# Target
async def get_article_service(
    session: Annotated[AsyncSession, Depends(get_async_session)]
) -> AsyncArticleService:
    return AsyncArticleService(session)
```

### Phase 4: Tools and Flows (Weeks 5-6)

#### 4.1 Async Tools
Convert I/O-bound tools:

```python
class AsyncWebScraperTool:
    async def scrape(self, url: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        # CPU-bound parsing can use thread pool
        loop = asyncio.get_event_loop()
        parsed = await loop.run_in_executor(
            None, self._parse_html, response.text
        )
        return parsed
```

**Priority Tools:**
- [ ] WebScraperTool (I/O bound)
- [ ] RSSParser (I/O bound)
- [ ] EntityTracker (Database queries)
- [ ] SentimentAnalyzer (Can remain sync or use thread pool)

#### 4.2 Async Flows
Update flows to use async services:

```python
class AsyncNewsPipelineFlow:
    async def process_article(self, url: str):
        async with get_async_session() as session:
            # Fetch and parse concurrently
            scraper = AsyncWebScraperTool()
            article_service = AsyncArticleService()

            content = await scraper.scrape(url)
            article = await article_service.process_article(
                session, url, content
            )

            # Run analysis concurrently
            analysis_tasks = [
                self._analyze_sentiment(session, article),
                self._extract_entities(session, article),
                self._detect_trends(session, article)
            ]

            results = await asyncio.gather(*analysis_tasks)
            return article, results
```

### Phase 5: Testing and Migration (Weeks 6-7)

#### 5.1 Testing Strategy
Create comprehensive async tests:

```python
@pytest.mark.asyncio
async def test_async_article_service():
    async with AsyncSessionLocal() as session:
        service = AsyncArticleService()
        article = await service.process_article(
            session, "https://example.com"
        )
        assert article is not None
```

**Testing Requirements:**
- [ ] Update test fixtures for async
- [ ] Create async test database sessions
- [ ] Mock async external calls
- [ ] Test concurrent operations
- [ ] Performance benchmarks

#### 5.2 Migration Utilities
Create helpers for gradual migration:

```python
def sync_to_async_adapter(sync_func):
    """Adapter to run sync functions in async context."""
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, sync_func, *args, **kwargs
        )
    return async_wrapper

class DualModeService:
    """Service that supports both sync and async operations."""

    def process_sync(self, session: Session, data: dict):
        # Sync implementation
        pass

    async def process_async(self, session: AsyncSession, data: dict):
        # Async implementation
        pass

    async def process(self, session, data: dict):
        """Auto-detect session type and use appropriate method."""
        if isinstance(session, AsyncSession):
            return await self.process_async(session, data)
        else:
            return await sync_to_async_adapter(self.process_sync)(
                session, data
            )
```

### Phase 6: Optimization and Cleanup (Week 8)

#### 6.1 Performance Optimization
- Implement connection pooling
- Add caching for frequently accessed data
- Optimize database queries
- Profile and identify bottlenecks

#### 6.2 Code Cleanup
- Remove sync versions after migration
- Update documentation
- Standardize error handling
- Update deployment configurations

## Implementation Guidelines

### Async Best Practices

1. **Use AsyncContextManager for Resources**
```python
class AsyncResourceManager:
    async def __aenter__(self):
        self.resource = await acquire_resource()
        return self.resource

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await release_resource(self.resource)
```

2. **Concurrent Operations with gather()**
```python
# Process multiple items concurrently
results = await asyncio.gather(
    *[process_item(item) for item in items],
    return_exceptions=True
)
```

3. **Avoid Blocking Operations**
```python
# Bad: Blocks the event loop
time.sleep(1)

# Good: Non-blocking
await asyncio.sleep(1)
```

4. **Handle CPU-Bound Operations**
```python
# Use thread pool for CPU-intensive tasks
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    None, cpu_intensive_function, data
)
```

### Error Handling

1. **Async Error Boundaries**
```python
async def safe_operation():
    try:
        return await risky_operation()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error: {e}")
        raise ServiceError("External service unavailable")
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        raise ServiceError("Operation timed out")
```

2. **Graceful Degradation**
```python
async def fetch_with_fallback(primary_url: str, fallback_url: str):
    try:
        return await fetch_from_primary(primary_url)
    except Exception:
        logger.warning("Primary source failed, trying fallback")
        return await fetch_from_fallback(fallback_url)
```

### Testing Async Code

1. **Use pytest-asyncio**
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

2. **Mock Async Dependencies**
```python
@pytest.mark.asyncio
async def test_with_mock():
    with patch('module.async_function', new_callable=AsyncMock) as mock:
        mock.return_value = "mocked"
        result = await function_under_test()
        assert result == "expected"
```

3. **Test Concurrent Behavior**
```python
@pytest.mark.asyncio
async def test_concurrent_operations():
    # Test that operations run concurrently
    start = time.time()
    await asyncio.gather(
        asyncio.sleep(1),
        asyncio.sleep(1),
        asyncio.sleep(1)
    )
    duration = time.time() - start
    assert duration < 1.5  # Should take ~1 second, not 3
```

## Migration Checklist

### Pre-Migration
- [ ] Set up async testing infrastructure
- [ ] Create performance benchmarks
- [ ] Document current sync interfaces
- [ ] Plan rollback strategy

### Database Layer
- [ ] Install async database drivers
- [ ] Create async engine and session management
- [ ] Implement AsyncCRUDBase
- [ ] Migrate CRUD classes
- [ ] Test database operations

### External APIs
- [ ] Replace requests with httpx
- [ ] Convert ApifyService
- [ ] Update webhook handlers
- [ ] Test external integrations

### Services
- [ ] Create async service base patterns
- [ ] Migrate services by priority
- [ ] Update dependency injection
- [ ] Test service interactions

### Tools and Flows
- [ ] Convert I/O-bound tools
- [ ] Update flow orchestration
- [ ] Test end-to-end workflows

### Testing and Deployment
- [ ] Update all tests for async
- [ ] Performance testing
- [ ] Update deployment configs
- [ ] Documentation updates

### Post-Migration
- [ ] Remove sync code
- [ ] Performance optimization
- [ ] Monitor production metrics
- [ ] Team training on async patterns

## Success Metrics

1. **Performance Improvements**
   - Response time reduction: Target 30-50% improvement
   - Throughput increase: Handle 3x more concurrent requests
   - Resource utilization: Lower CPU and memory usage

2. **Code Quality**
   - 100% async coverage for I/O operations
   - Consistent async patterns throughout
   - Comprehensive async test coverage

3. **Operational Benefits**
   - Better error handling and resilience
   - Improved monitoring and debugging
   - Easier scaling and deployment

## Risks and Mitigation

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Gradual migration with dual-mode support

2. **Risk**: Performance regression in CPU-bound operations
   - **Mitigation**: Use thread pools for CPU-intensive tasks

3. **Risk**: Complex debugging of async code
   - **Mitigation**: Comprehensive logging and monitoring

4. **Risk**: Team learning curve
   - **Mitigation**: Training sessions and documentation

## Progress Update

### Completed Tasks (Issue #721)

#### ✅ Phase 1: Foundation
- Created async database session management with `get_async_session()`
- Implemented proper async session lifecycle management
- Fixed critical bugs in session binding and query execution

#### ✅ Phase 2: Webhook Handler
- Successfully converted `/webhooks/apify` endpoint to fully async
- Implemented async `ApifyWebhookService` with proper error handling
- Created async CRUD operations for `ApifyWebhookRaw`
- Fixed timezone handling issues in models

#### ✅ Key Patterns Established

1. **Async Session Management**
```python
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

2. **Async CRUD Operations**
```python
async def create_async(self, session: AsyncSession, data: dict):
    obj = self.model(**data)
    session.add(obj)
    await session.flush()
    await session.refresh(obj)
    return obj
```

3. **Proper Error Handling**
```python
try:
    result = await service.process_webhook(webhook_data)
except HTTPException:
    raise  # Let FastAPI handle it
except Exception as e:
    logger.error(f"Webhook processing failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

4. **Async Service Pattern**
```python
class ApifyWebhookService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.crud = CRUDApifyWebhookRaw()

    async def process_webhook(self, data: dict):
        # All database operations use await
        webhook = await self.crud.create_async(self.session, data)
        return webhook
```

### Lessons Learned

1. **Session Management is Critical**: Async sessions must be properly managed with explicit commit/rollback/close operations
2. **Error Propagation**: HTTPException must be re-raised, not wrapped
3. **No Implicit Commits**: Unlike sync SQLAlchemy, async requires explicit `await session.commit()`
4. **Timezone Handling**: Use timezone-naive datetime in database, handle timezone conversion at API boundaries

### Next Steps

- Continue async migration for other services following established patterns
- Implement async versions of remaining CRUD operations
- Convert external API clients (Apify, HTTP requests) to async

## Timeline

- **Week 1-2**: Database layer and CRUD operations ✅ (Partially complete)
- **Week 2-3**: External API integrations (In progress)
- **Week 3-5**: Service layer migration
- **Week 5-6**: Tools and flows
- **Week 6-7**: Testing and migration
- **Week 8**: Optimization and cleanup

Total estimated time: 8 weeks for full migration

## Conclusion

This migration plan provides a structured approach to converting the Local Newsifier codebase to fully async operations. By following this plan, we can achieve significant performance improvements while maintaining code quality and system reliability. The phased approach allows for gradual migration with minimal risk to existing functionality.

The successful implementation of async webhook handling (Issue #721) has validated our approach and established solid patterns for the rest of the migration.

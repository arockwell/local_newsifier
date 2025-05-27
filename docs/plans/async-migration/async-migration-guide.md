# Async Migration Guide - Local Newsifier

**⚠️ DEPRECATED**: This guide is kept for historical reference only. The project has decided to move to sync-only implementations. All async patterns are deprecated and should not be used.

**IMPORTANT**: Do not follow the async migration patterns in this guide. Use sync patterns exclusively. See the main CLAUDE.md file for current development guidelines.

## Migration Options Overview

### Option 1: Full Async Architecture (DEPRECATED - DO NOT USE)
- **Status**: Deprecated due to production crashes from async/sync mixing
- **Issues**: Complex migration, event loop problems, difficult debugging
- **Decision**: Rejected in favor of sync-only approach

### Option 2: Full Sync Architecture (RECOMMENDED)
- **Pros**: Simpler code, easier to understand, no event loop issues, stable in production
- **Cons**: Slightly lower theoretical performance (negligible in practice)
- **Effort**: 2-3 weeks
- **Status**: This is the chosen approach for the project

### Option 3: Clear Separation
- **Pros**: Balanced approach, clear boundaries, moderate effort
- **Cons**: Two patterns to maintain, potential confusion
- **Effort**: 3-4 weeks

## Option 1: Full Async Migration (DEPRECATED - DO NOT USE)

**⚠️ WARNING**: This section is kept for historical reference only. Do not implement these patterns.

### Prerequisites

1. **Install async dependencies**
```bash
pip install asyncpg  # Async PostgreSQL driver
pip install sqlalchemy[asyncio]  # Async SQLAlchemy support
pip install aiofiles  # Async file operations
pip install httpx  # Async HTTP client
```

2. **Update requirements.txt**
```
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.23
aiofiles==23.2.1
httpx==0.27.0
```

### Step 1: Database Layer Migration

#### 1.1 Create Async Engine
```python
# src/local_newsifier/database/async_engine.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from local_newsifier.config.settings import get_settings

settings = get_settings()

# Convert sync URL to async URL
async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
async_engine = create_async_engine(
    async_url,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide async database session."""
    async with async_session_factory() as session:
        yield session

async def create_db_and_tables():
    """Create all tables asynchronously."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

#### 1.2 Update CRUD Base
```python
# src/local_newsifier/crud/async_base.py
from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)

class AsyncCRUDBase(Generic[ModelType]):
    """Base class for async CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Get an item by id asynchronously."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple items with pagination asynchronously."""
        result = await db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: ModelType) -> ModelType:
        """Create a new item asynchronously."""
        db.add(obj_in)
        await db.commit()
        await db.refresh(obj_in)
        return obj_in
```

### Step 2: Service Layer Migration

#### 2.1 Async Service Base
```python
# src/local_newsifier/services/async_base.py
from typing import AsyncContextManager, Callable
from sqlalchemy.ext.asyncio import AsyncSession

class AsyncServiceBase:
    """Base class for async services."""

    def __init__(self, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.session_factory = session_factory
```

#### 2.2 Migrate Article Service
```python
# src/local_newsifier/services/async_article_service.py
from datetime import datetime
from typing import Dict, Any
from fastapi_injectable import injectable

from local_newsifier.services.async_base import AsyncServiceBase
from local_newsifier.crud.async_article import AsyncArticleCRUD
from local_newsifier.models.article import Article

@injectable(use_cache=False)
class AsyncArticleService(AsyncServiceBase):
    """Async article service."""

    def __init__(self, article_crud: AsyncArticleCRUD, session_factory):
        super().__init__(session_factory)
        self.article_crud = article_crud

    async def process_article(
        self, url: str, content: str, title: str, published_at: datetime
    ) -> Dict[str, Any]:
        """Process an article asynchronously."""
        async with self.session_factory() as session:
            article_data = Article(
                url=url,
                title=title,
                content=content,
                published_at=published_at,
                status="analyzed",
                scraped_at=datetime.now()
            )

            article = await self.article_crud.create(session, obj_in=article_data)

            # Process entities asynchronously
            entities = await self.entity_service.process_article_entities(
                article_id=article.id,
                content=content,
                title=title,
                published_at=published_at
            )

            return {
                "article": article,
                "entities": entities
            }
```

### Step 3: API Layer Migration

#### 3.1 Update Providers
```python
# src/local_newsifier/di/async_providers.py
from typing import AsyncGenerator
from fastapi import Depends
from fastapi_injectable import injectable
from sqlalchemy.ext.asyncio import AsyncSession

from local_newsifier.database.async_engine import get_async_session

@injectable(use_cache=False)
async def get_async_article_service(
    session: AsyncSession = Depends(get_async_session)
):
    """Provide async article service."""
    from local_newsifier.services.async_article_service import AsyncArticleService
    from local_newsifier.crud.async_article import AsyncArticleCRUD

    return AsyncArticleService(
        article_crud=AsyncArticleCRUD(),
        session_factory=lambda: session
    )
```

#### 3.2 Update Endpoints
```python
# src/local_newsifier/api/main.py
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from local_newsifier.di.async_providers import get_async_session, get_async_article_service

@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    article_service = Depends(get_async_article_service)
):
    """Root endpoint with async database access."""
    # Now properly async
    articles = await article_service.get_recent_articles(
        start_date=start_date,
        end_date=end_date
    )

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "articles": articles}
    )
```

### Step 4: Testing Migration

#### 4.1 Async Test Fixtures
```python
# tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

@pytest_asyncio.fixture
async def async_engine():
    """Create async test engine."""
    engine = create_async_engine(
        "postgresql+asyncpg://test_user:test_pass@localhost/test_db",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create async test session."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session
```

#### 4.2 Async Tests
```python
# tests/services/test_async_article_service.py
import pytest

@pytest.mark.asyncio
async def test_process_article(async_session, async_article_service):
    """Test async article processing."""
    result = await async_article_service.process_article(
        url="https://example.com/article",
        content="Test content",
        title="Test Article",
        published_at=datetime.now()
    )

    assert result["article"].id is not None
    assert len(result["entities"]) > 0
```

### Step 5: Celery Tasks Migration

#### 5.1 Async Task Wrapper
```python
# src/local_newsifier/tasks/async_tasks.py
import asyncio
from celery import Task

class AsyncTask(Task):
    """Celery task that runs async functions."""

    def run(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_run(*args, **kwargs))
        finally:
            loop.close()

    async def async_run(self, *args, **kwargs):
        raise NotImplementedError()

@app.task(base=AsyncTask, bind=True)
class ProcessArticleTask(AsyncTask):
    async def async_run(self, article_id: int):
        async with get_async_session() as session:
            service = AsyncArticleService(session)
            return await service.process_article_by_id(article_id)
```

## Option 2: Full Sync Migration

### Step 1: Remove Async from Endpoints

```python
# src/local_newsifier/api/main.py
# Change all async def to def
@app.get("/", response_class=HTMLResponse)
def root(  # Remove async
    request: Request,
    session: Session = Depends(get_session),
    templates: Jinja2Templates = Depends(get_templates)
):
    """Synchronous root endpoint."""
    articles = article_crud.get_by_date_range(
        session, start_date=start_date, end_date=end_date
    )
    return templates.TemplateResponse("index.html", {...})
```

### Step 2: Remove fastapi-injectable

```python
# Remove @injectable decorators
class ArticleService:  # No decorator
    def __init__(self, article_crud, session_factory):
        self.article_crud = article_crud
        self.session_factory = session_factory
```

### Step 3: Simplify Dependency Injection

```python
# src/local_newsifier/api/dependencies.py
def get_article_service(session: Session = Depends(get_session)):
    """Simple sync dependency."""
    return ArticleService(
        article_crud=article_crud,
        session_factory=lambda: session
    )
```

## Option 3: Clear Separation

### Sync Endpoints for Database
```python
@app.get("/articles", response_model=List[Article])
def get_articles(  # Sync for database
    session: Session = Depends(get_session)
):
    return article_crud.get_multi(session)
```

### Async Endpoints for External I/O
```python
@app.post("/scrape")
async def scrape_url(  # Async for external API
    url: str,
    http_client: httpx.AsyncClient = Depends(get_http_client)
):
    response = await http_client.get(url)
    return {"content": response.text}
```

## Migration Checklist

### Phase 1: Preparation
- [ ] Choose migration strategy
- [ ] Set up development branch
- [ ] Install required dependencies
- [ ] Create migration documentation

### Phase 2: Infrastructure
- [ ] Create async/sync database layer
- [ ] Update configuration
- [ ] Set up test infrastructure
- [ ] Create compatibility layer

### Phase 3: Component Migration
- [ ] Migrate CRUD operations
- [ ] Migrate services
- [ ] Migrate API endpoints
- [ ] Migrate background tasks

### Phase 4: Testing
- [ ] Update unit tests
- [ ] Update integration tests
- [ ] Remove CI skip decorators
- [ ] Ensure all tests pass

### Phase 5: Cleanup
- [ ] Remove old sync/async code
- [ ] Remove event loop fixtures
- [ ] Remove conditional decorators
- [ ] Update documentation

### Phase 6: Deployment
- [ ] Test in staging environment
- [ ] Performance benchmarking
- [ ] Gradual production rollout
- [ ] Monitor for issues

## Common Pitfalls to Avoid

1. **Don't mix async and sync database operations**
2. **Don't use blocking I/O in async functions**
3. **Don't create custom event loop management**
4. **Don't use conditional decorators**
5. **Don't skip tests instead of fixing issues**

## Success Criteria

- All tests pass in CI without skips
- No event loop errors
- Consistent async or sync patterns throughout
- Clear documentation on patterns to use
- Performance improvement (for async) or simplification (for sync)

## Resources

- [FastAPI Async Documentation](https://fastapi.tiangolo.com/async/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Python asyncio Best Practices](https://docs.python.org/3/library/asyncio-task.html)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)

# FastAPI Endpoint Migration Guide

This guide details how to migrate FastAPI endpoints from FastAPI-Injectable to native FastAPI dependencies.

## Current vs Target Patterns

### Current Pattern (FastAPI-Injectable)

```python
# In api/routers/articles.py
from typing import Annotated
from fastapi import APIRouter, Depends
from local_newsifier.di.providers import get_article_service, get_session
from local_newsifier.services.article_service import ArticleService
from sqlmodel import Session

router = APIRouter()

@router.get("/articles/{article_id}")
async def get_article(
    article_id: int,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[Session, Depends(get_session)]
):
    # Sync service with session factory
    return article_service.get_article(article_id)
```

### Target Pattern (Native FastAPI + Async)

```python
# In api/routers/articles.py
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from local_newsifier.api.dependencies import get_article_service, get_session
from local_newsifier.services.article_service import ArticleService

router = APIRouter()

@router.get("/articles/{article_id}")
async def get_article(
    article_id: int,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    # Async service with explicit session
    return await article_service.get_article(session, article_id)
```

## Migration Steps

### Step 1: Create New Dependencies Module

Create `api/dependencies.py` to centralize all dependency functions:

```python
# api/dependencies.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from local_newsifier.config.settings import get_settings
from local_newsifier.crud.article import ArticleCRUD
from local_newsifier.services.article_service import ArticleService

# Database setup
settings = get_settings()
async_engine = create_async_engine(settings.async_database_url)
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Core dependencies
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session."""
    async with AsyncSessionLocal() as session:
        yield session

# CRUD dependencies
def get_article_crud() -> ArticleCRUD:
    """Provide article CRUD."""
    return ArticleCRUD()

# Service dependencies
def get_article_service() -> ArticleService:
    """Provide article service."""
    return ArticleService(article_crud=get_article_crud())
```

### Step 2: Update Endpoint Signatures

Update all endpoints to use async sessions and services:

```python
# Before
@router.post("/articles")
async def create_article(
    article_data: ArticleCreate,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[Session, Depends(get_session)]
):
    return article_service.create_article(article_data.dict())

# After
@router.post("/articles")
async def create_article(
    article_data: ArticleCreate,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    return await article_service.create_article(session, article_data.dict())
```

### Step 3: Handle Background Tasks

Convert background tasks to use async patterns:

```python
# Before
from fastapi import BackgroundTasks

@router.post("/articles/process")
async def process_article_background(
    url: str,
    background_tasks: BackgroundTasks,
    article_service: Annotated[ArticleService, Depends(get_article_service)]
):
    background_tasks.add_task(article_service.process_url, url)
    return {"message": "Processing started"}

# After
@router.post("/articles/process")
async def process_article_background(
    url: str,
    background_tasks: BackgroundTasks,
    article_service: Annotated[ArticleService, Depends(get_article_service)]
):
    # Create async wrapper for background task
    async def process_async():
        async with AsyncSessionLocal() as session:
            await article_service.process_url(session, url)

    background_tasks.add_task(process_async)
    return {"message": "Processing started"}
```

### Step 4: Update Error Handling

Implement proper async error handling:

```python
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

@router.post("/articles")
async def create_article(
    article_data: ArticleCreate,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    try:
        article = await article_service.create_article(session, article_data.dict())
        await session.commit()
        return article
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Article already exists")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

## Common Endpoint Patterns

### 1. CRUD Endpoints

```python
@router.get("/articles", response_model=List[ArticleResponse])
async def list_articles(
    skip: int = 0,
    limit: int = 100,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    return await article_service.list_articles(session, skip=skip, limit=limit)

@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    article = await article_service.get_article(session, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_update: ArticleUpdate,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    article = await article_service.update_article(
        session, article_id, article_update.dict(exclude_unset=True)
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    await session.commit()
    return article

@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: int,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    success = await article_service.delete_article(session, article_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article not found")
    await session.commit()
    return {"message": "Article deleted"}
```

### 2. Complex Operations

```python
@router.post("/articles/analyze")
async def analyze_articles(
    analysis_request: AnalysisRequest,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    entity_service: Annotated[EntityService, Depends(get_entity_service)],
    analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    # Fetch articles
    articles = await article_service.get_articles_by_date_range(
        session,
        start_date=analysis_request.start_date,
        end_date=analysis_request.end_date
    )

    # Process concurrently
    analysis_tasks = []
    for article in articles:
        task = asyncio.create_task(
            analysis_service.analyze_article(session, article)
        )
        analysis_tasks.append(task)

    # Wait for all analyses
    results = await asyncio.gather(*analysis_tasks)

    # Aggregate results
    summary = await analysis_service.aggregate_results(session, results)

    return {
        "articles_analyzed": len(articles),
        "summary": summary
    }
```

### 3. Streaming Responses

```python
from fastapi.responses import StreamingResponse
import asyncio

@router.get("/articles/export")
async def export_articles(
    format: str = "csv",
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    async def generate():
        # Stream header
        if format == "csv":
            yield "id,title,url,created_at\n"

        # Stream articles in batches
        offset = 0
        batch_size = 100

        while True:
            articles = await article_service.list_articles(
                session, skip=offset, limit=batch_size
            )

            if not articles:
                break

            for article in articles:
                if format == "csv":
                    yield f"{article.id},{article.title},{article.url},{article.created_at}\n"
                else:
                    yield json.dumps(article.dict()) + "\n"

            offset += batch_size

            # Prevent blocking the event loop
            await asyncio.sleep(0)

    media_type = "text/csv" if format == "csv" else "application/json"
    return StreamingResponse(generate(), media_type=media_type)
```

### 4. WebSocket Endpoints

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/articles")
async def websocket_articles(
    websocket: WebSocket,
    article_service: Annotated[ArticleService, Depends(get_article_service)]
):
    await websocket.accept()

    # Create dedicated session for WebSocket connection
    async with AsyncSessionLocal() as session:
        try:
            while True:
                # Receive message
                data = await websocket.receive_json()

                if data["action"] == "subscribe":
                    # Send real-time updates
                    async for article in article_service.watch_new_articles(session):
                        await websocket.send_json({
                            "type": "new_article",
                            "data": article.dict()
                        })

        except WebSocketDisconnect:
            pass
```

## Dependency Injection Patterns

### 1. Shared Dependencies

```python
# Common dependencies used across endpoints
class CommonDependencies:
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        current_user: Annotated[User, Depends(get_current_user)]
    ):
        self.session = session
        self.current_user = current_user

@router.post("/articles")
async def create_article(
    article_data: ArticleCreate,
    deps: Annotated[CommonDependencies, Depends()],
    article_service: Annotated[ArticleService, Depends(get_article_service)]
):
    # Use deps.session and deps.current_user
    article_data.user_id = deps.current_user.id
    return await article_service.create_article(deps.session, article_data.dict())
```

### 2. Configuration Dependencies

```python
from functools import lru_cache
from local_newsifier.config.settings import Settings

@lru_cache()
def get_settings() -> Settings:
    return Settings()

@router.get("/config/limits")
async def get_limits(
    settings: Annotated[Settings, Depends(get_settings)]
):
    return {
        "max_articles_per_request": settings.max_articles_per_request,
        "rate_limit": settings.api_rate_limit
    }
```

### 3. Optional Dependencies

```python
from typing import Optional

async def get_optional_cache() -> Optional[Cache]:
    """Provide cache if available."""
    if settings.cache_enabled:
        return Cache()
    return None

@router.get("/articles/{article_id}")
async def get_article(
    article_id: int,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    cache: Annotated[Optional[Cache], Depends(get_optional_cache)]
):
    # Check cache first if available
    if cache:
        cached = await cache.get(f"article:{article_id}")
        if cached:
            return cached

    # Fetch from database
    article = await article_service.get_article(session, article_id)

    # Cache result if available
    if cache and article:
        await cache.set(f"article:{article_id}", article)

    return article
```

## Testing Migrated Endpoints

### 1. Basic Endpoint Test

```python
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_get_article(async_client: AsyncClient, mock_article_service):
    # Setup mock
    mock_article = {"id": 1, "title": "Test Article"}
    mock_article_service.get_article = AsyncMock(return_value=mock_article)

    # Make request
    response = await async_client.get("/articles/1")

    # Verify
    assert response.status_code == 200
    assert response.json() == mock_article
    mock_article_service.get_article.assert_called_once()
```

### 2. Dependency Override Test

```python
from fastapi.testclient import TestClient

def test_with_override(app, test_db_session):
    # Override dependencies
    async def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session

    # Test with overridden dependency
    with TestClient(app) as client:
        response = client.post("/articles", json={"title": "Test"})
        assert response.status_code == 201
```

### 3. Integration Test

```python
@pytest.mark.asyncio
async def test_article_flow_integration(async_client: AsyncClient):
    # Create article
    create_response = await async_client.post(
        "/articles",
        json={"title": "Integration Test", "url": "http://example.com"}
    )
    assert create_response.status_code == 201
    article_id = create_response.json()["id"]

    # Get article
    get_response = await async_client.get(f"/articles/{article_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Integration Test"

    # Update article
    update_response = await async_client.put(
        f"/articles/{article_id}",
        json={"title": "Updated Title"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Title"

    # Delete article
    delete_response = await async_client.delete(f"/articles/{article_id}")
    assert delete_response.status_code == 200

    # Verify deletion
    get_deleted = await async_client.get(f"/articles/{article_id}")
    assert get_deleted.status_code == 404
```

## Migration Checklist

For each router file:

- [ ] Create or update `api/dependencies.py` with required dependencies
- [ ] Replace sync Session with AsyncSession imports
- [ ] Update all endpoint signatures to use async sessions
- [ ] Convert endpoint functions to properly await async operations
- [ ] Update error handling for async context
- [ ] Handle transaction management (commit/rollback)
- [ ] Update background task handling
- [ ] Remove old provider imports from `di/providers.py`
- [ ] Update tests to use async patterns
- [ ] Test all endpoints thoroughly

## Common Issues and Solutions

### 1. Forgotten Await
**Problem**: Forgetting to await async operations.
```python
# Wrong
article = article_service.get_article(session, id)  # Returns coroutine!

# Correct
article = await article_service.get_article(session, id)
```

### 2. Session Management
**Problem**: Session closed before response serialization.
```python
# Solution: Ensure data is loaded before session closes
article = await article_service.get_article(session, id)
# Force loading of lazy relationships if needed
await session.refresh(article)
```

### 3. Concurrent Modifications
**Problem**: Multiple concurrent requests modifying same data.
```python
# Solution: Use proper transaction isolation
async with session.begin():
    # All operations in this block are atomic
    article = await article_service.get_article(session, id)
    article.view_count += 1
    await session.commit()
```

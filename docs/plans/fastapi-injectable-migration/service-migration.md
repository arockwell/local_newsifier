# Service Migration Guide

This guide details how to migrate services away from FastAPI-Injectable as part of the async conversion.

## Migration Pattern

### Current Pattern (FastAPI-Injectable)

```python
# In di/providers.py
@injectable(use_cache=False)
def get_article_service(
    article_crud: Annotated[ArticleCRUD, Depends(get_article_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    from local_newsifier.services.article_service import ArticleService
    return ArticleService(
        article_crud=article_crud,
        session_factory=lambda: session
    )

# In services/article_service.py
class ArticleService:
    def __init__(self, article_crud, session_factory):
        self.article_crud = article_crud
        self.session_factory = session_factory

    def process_article(self, url: str):
        with self.session_factory() as session:
            # Sync processing
            article = self.article_crud.get_by_url(session, url)
            return article
```

### Target Pattern (Async + Direct DI)

```python
# In services/article_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

class ArticleService:
    """Async article service with explicit dependencies."""

    def __init__(self, article_crud: ArticleCRUD):
        self.article_crud = article_crud

    async def process_article(self, session: AsyncSession, url: str):
        # Async processing - session passed explicitly
        article = await self.article_crud.get_by_url(session, url)
        return article

# In api/dependencies.py (NEW FILE)
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from local_newsifier.crud.article import ArticleCRUD
from local_newsifier.database.engine import get_async_session
from local_newsifier.services.article_service import ArticleService

# Simple dependency functions
async def get_article_crud() -> ArticleCRUD:
    """Get article CRUD instance."""
    return ArticleCRUD()

async def get_article_service(
    article_crud: Annotated[ArticleCRUD, Depends(get_article_crud)]
) -> ArticleService:
    """Get article service instance."""
    return ArticleService(article_crud=article_crud)
```

## Step-by-Step Migration Process

### Step 1: Identify Service Dependencies

For each service, catalog its dependencies:

```python
# Example: ArticleService dependencies
dependencies = {
    "ArticleService": {
        "crud": ["ArticleCRUD"],
        "tools": ["WebScraperTool", "EntityExtractor"],
        "other_services": ["EntityService"]
    }
}
```

### Step 2: Remove Session Factory Pattern

Replace session factory with explicit session parameters:

```python
# Before
class ArticleService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_article(self, id: int):
        with self.session_factory() as session:
            return self.crud.get(session, id)

# After
class ArticleService:
    async def get_article(self, session: AsyncSession, id: int):
        return await self.crud.get(session, id)
```

### Step 3: Convert to Async

Update all I/O-bound methods to async:

```python
# Before
def fetch_and_process(self, url: str):
    content = self.scraper.scrape(url)
    entities = self.entity_extractor.extract(content)
    return self.process_entities(entities)

# After
async def fetch_and_process(self, session: AsyncSession, url: str):
    # Concurrent I/O operations
    content, existing_article = await asyncio.gather(
        self.scraper.scrape(url),
        self.crud.get_by_url(session, url)
    )

    if existing_article:
        return existing_article

    entities = await self.entity_extractor.extract(content)
    return await self.process_entities(session, entities)
```

### Step 4: Update Service Initialization

Remove DI decorators and simplify initialization:

```python
# Before
@injectable(use_cache=False)
class EntityService:
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        session: Annotated[Session, Depends(get_session)]
    ):
        self.entity_crud = entity_crud
        self.session = session

# After
class EntityService:
    def __init__(self, entity_crud: EntityCRUD):
        self.entity_crud = entity_crud

    async def process_entity(self, session: AsyncSession, entity_data: dict):
        # Process with explicit session
        return await self.entity_crud.create(session, entity_data)
```

### Step 5: Create FastAPI Dependencies

Move dependency creation to `api/dependencies.py`:

```python
# api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

# Import all required components
from local_newsifier.database.engine import get_async_session
from local_newsifier.crud import (
    ArticleCRUD, EntityCRUD, AnalysisResultCRUD
)
from local_newsifier.services import (
    ArticleService, EntityService, AnalysisService
)
from local_newsifier.tools import (
    WebScraperTool, EntityExtractor, SentimentAnalyzer
)

# Database session
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# CRUD dependencies
async def get_article_crud() -> ArticleCRUD:
    return ArticleCRUD()

async def get_entity_crud() -> EntityCRUD:
    return EntityCRUD()

# Tool dependencies
async def get_web_scraper() -> WebScraperTool:
    return WebScraperTool()

async def get_entity_extractor() -> EntityExtractor:
    return EntityExtractor()

# Service dependencies with explicit injection
async def get_article_service(
    article_crud: Annotated[ArticleCRUD, Depends(get_article_crud)],
    web_scraper: Annotated[WebScraperTool, Depends(get_web_scraper)]
) -> ArticleService:
    return ArticleService(
        article_crud=article_crud,
        web_scraper=web_scraper
    )

async def get_entity_service(
    entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
    entity_extractor: Annotated[EntityExtractor, Depends(get_entity_extractor)]
) -> EntityService:
    return EntityService(
        entity_crud=entity_crud,
        entity_extractor=entity_extractor
    )
```

## Service Categories and Migration Priority

### 1. External API Services (High Priority)
These benefit most from async conversion:

- **ApifyService**: Heavy HTTP I/O
- **RSSFeedService**: Multiple HTTP requests
- **WebScraperTool**: Network-bound operations

```python
# Example: ApifyService migration
class ApifyService:
    def __init__(self, api_token: str):
        self.client = httpx.AsyncClient(
            base_url="https://api.apify.com/v2",
            headers={"Authorization": f"Bearer {api_token}"}
        )

    async def run_actor(self, actor_id: str, input_data: dict):
        response = await self.client.post(
            f"/acts/{actor_id}/runs",
            json=input_data
        )
        return response.json()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
```

### 2. Database-Heavy Services (Medium Priority)
Benefit from concurrent queries:

- **ArticleService**: Complex queries and relationships
- **EntityService**: Many related queries
- **AnalysisService**: Aggregation queries

### 3. Computation Services (Low Priority)
Can remain sync or use thread pools:

- **SentimentAnalyzer**: CPU-bound NLP processing
- **TrendAnalyzer**: Statistical computations
- **EntityResolver**: Algorithm-heavy processing

```python
# Example: Hybrid approach for CPU-bound service
class SentimentAnalyzer:
    async def analyze_async(self, text: str) -> float:
        # Run CPU-bound operation in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._analyze_sync, text
        )

    def _analyze_sync(self, text: str) -> float:
        # CPU-intensive sentiment analysis
        return self.model.predict(text)
```

## Common Patterns

### 1. Service Composition
```python
class NewsPipelineService:
    def __init__(
        self,
        article_service: ArticleService,
        entity_service: EntityService,
        analysis_service: AnalysisService
    ):
        self.article_service = article_service
        self.entity_service = entity_service
        self.analysis_service = analysis_service

    async def process_article(self, session: AsyncSession, url: str):
        # Compose multiple services
        article = await self.article_service.fetch_and_save(session, url)

        # Concurrent processing
        entities_task = self.entity_service.extract_entities(session, article)
        analysis_task = self.analysis_service.analyze_sentiment(session, article)

        entities, analysis = await asyncio.gather(entities_task, analysis_task)

        return {
            "article": article,
            "entities": entities,
            "analysis": analysis
        }
```

### 2. Batch Processing
```python
class BatchProcessingService:
    async def process_batch(self, session: AsyncSession, items: List[dict]):
        # Process items concurrently with semaphore for rate limiting
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent operations

        async def process_with_limit(item):
            async with semaphore:
                return await self.process_item(session, item)

        results = await asyncio.gather(
            *[process_with_limit(item) for item in items],
            return_exceptions=True
        )

        # Handle results and exceptions
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]

        return {"successful": successful, "failed": failed}
```

### 3. Resource Management
```python
class ResourceManagedService:
    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    async def fetch_data(self, url: str):
        client = await self._get_client()
        response = await client.get(url)
        return response.json()

    async def cleanup(self):
        if self._client:
            await self._client.aclose()
            self._client = None
```

## Testing Migrated Services

### 1. Unit Tests
```python
# test_article_service.py
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_article_service():
    # Mock dependencies
    mock_crud = Mock()
    mock_crud.get_by_url = AsyncMock(return_value=None)
    mock_crud.create = AsyncMock(return_value={"id": 1, "url": "test"})

    # Create service
    service = ArticleService(article_crud=mock_crud)

    # Test with mock session
    mock_session = Mock()
    result = await service.process_article(mock_session, "http://example.com")

    assert result["id"] == 1
    mock_crud.create.assert_called_once()
```

### 2. Integration Tests
```python
@pytest.mark.asyncio
async def test_article_service_integration(async_session):
    # Use real dependencies
    article_crud = ArticleCRUD()
    service = ArticleService(article_crud=article_crud)

    # Test with real session
    result = await service.process_article(
        async_session,
        "http://example.com"
    )

    # Verify in database
    saved = await article_crud.get(async_session, result.id)
    assert saved.url == "http://example.com"
```

## Migration Checklist

For each service:

- [ ] Remove `@injectable` decorator
- [ ] Remove session factory pattern
- [ ] Convert methods to async where appropriate
- [ ] Update method signatures to accept session parameter
- [ ] Create simple constructor without DI magic
- [ ] Update all service calls to include session
- [ ] Create FastAPI dependency function
- [ ] Update tests to use async patterns
- [ ] Remove old provider function from `di/providers.py`
- [ ] Update documentation

## Common Pitfalls and Solutions

### 1. Circular Dependencies
**Problem**: Services depend on each other circularly.
**Solution**: Use dependency injection at method level or redesign to break cycle.

### 2. Session Lifecycle
**Problem**: Session closed before async operation completes.
**Solution**: Ensure session is kept alive for entire operation scope.

### 3. Mixed Sync/Async
**Problem**: Calling sync code from async context.
**Solution**: Use `run_in_executor` for unavoidable sync operations.

### 4. Resource Leaks
**Problem**: HTTP clients or connections not closed.
**Solution**: Use context managers or explicit cleanup methods.

# Dependency Injection Guide

## Overview

Local Newsifier uses the `fastapi-injectable` framework for dependency injection. This guide covers architecture, usage patterns, examples, and best practices.

## Table of Contents
- [Architecture](#architecture)
- [Core Concepts](#core-concepts)
- [Provider Functions](#provider-functions)
- [Injectable Classes](#injectable-classes)
- [Usage in FastAPI](#usage-in-fastapi)
- [Usage in CLI](#usage-in-cli)
- [Testing](#testing)
- [Anti-Patterns](#anti-patterns)
- [Migration Guide](#migration-guide)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Architecture

The dependency injection system follows this workflow:

1. **Provider Functions** define how to create instances
2. **FastAPI Depends** resolves dependencies at runtime
3. **Injectable Classes** can be auto-injected
4. **Testing Utilities** allow easy mocking

### Key Design Decisions

- **No Caching**: All providers use `use_cache=False` to ensure fresh instances
- **Lazy Loading**: Dependencies are imported inside provider functions to avoid circular imports
- **Session Scope**: Database sessions are request-scoped, not shared between requests
- **Explicit Dependencies**: All dependencies must be explicitly declared
- **Sync-Only**: All code is synchronous - no async/await patterns

## Core Concepts

### Provider Functions

Provider functions are decorated with `@injectable` and define how to create instances:

```python
from typing import Annotated
from fastapi import Depends
from injectable import injectable

@injectable(use_cache=False)
def get_article_service(
    session: Annotated[Session, Depends(get_session)],
    article_crud: Annotated[Any, Depends(get_article_crud)]
) -> ArticleService:
    from local_newsifier.services.article_service import ArticleService

    return ArticleService(
        article_crud=article_crud,
        session_factory=lambda: session
    )
```

**Important**: Always use `use_cache=False` to prevent instance reuse across requests.

### Injectable Classes

Classes can be made auto-injectable for simpler cases:

```python
from injectable import injectable, Autowired
from typing import Annotated

@injectable
class MyService:
    def __init__(
        self,
        session: Annotated[Session, Autowired(get_session)],
        crud: Annotated[ArticleCRUD, Autowired(get_article_crud)]
    ):
        self.session = session
        self.crud = crud
```

## Sync-Only Architecture

> **IMPORTANT**: This project uses ONLY synchronous patterns. No async/await code is allowed.

### Why Sync-Only?

1. **Simplicity**: Easier to understand and debug
2. **Compatibility**: Works seamlessly with all tools and libraries
3. **Testing**: Simpler test setup without async fixtures
4. **Error Handling**: More straightforward exception handling

### Sync-Only Rules

1. **All FastAPI routes must be synchronous**:
```python
# CORRECT - Sync route
@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}

# WRONG - Async route
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}
```

2. **Use synchronous HTTP clients**:
```python
# CORRECT - Sync HTTP client
import requests
response = requests.get(url)

# WRONG - Async HTTP client
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

3. **Database operations are synchronous**:
```python
# CORRECT - Sync database operations
with self.session_factory() as session:
    result = session.exec(query).all()

# WRONG - Async database operations
async with self.session_factory() as session:
    result = await session.execute(query)
```

## Provider Functions

### Database Session Provider

```python
@injectable(use_cache=False)
def get_session():
    from local_newsifier.database.engine import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### CRUD Providers

```python
@injectable(use_cache=False)
def get_article_crud():
    from local_newsifier.crud.article import ArticleCRUD
    return ArticleCRUD()
```

### Service Providers

Services coordinate between CRUD operations and business logic:

```python
@injectable(use_cache=False)
def get_entity_service(
    session: Annotated[Session, Depends(get_session)],
    entity_crud: Annotated[Any, Depends(get_entity_crud)],
    entity_extractor: Annotated[Any, Depends(get_entity_extractor)]
) -> EntityService:
    from local_newsifier.services.entity_service import EntityService

    return EntityService(
        session_factory=lambda: session,
        entity_crud=entity_crud,
        entity_extractor=entity_extractor
    )
```

### Tool Providers

Tools for NLP processing, web scraping, etc.:

```python
@injectable(use_cache=False)
def get_sentiment_analyzer():
    from local_newsifier.tools.sentiment_analyzer import SentimentAnalyzer
    return SentimentAnalyzer()

@injectable(use_cache=False)
def get_web_scraper():
    from local_newsifier.tools.web_scraper import WebScraper
    return WebScraper()
```

## Usage in FastAPI

### Basic Endpoint

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from local_newsifier.di.providers import get_article_service

router = APIRouter()

@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    service: Annotated[ArticleService, Depends(get_article_service)]
):
    article = service.get(article_id)
    if not article:
        raise HTTPException(status_code=404)
    return article
```

### With Multiple Dependencies

```python
@router.post("/articles/{article_id}/analyze")
def analyze_article(
    article_id: int,
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    entity_service: Annotated[EntityService, Depends(get_entity_service)],
    sentiment_analyzer: Annotated[SentimentAnalyzer, Depends(get_sentiment_analyzer)]
):
    article = article_service.get(article_id)
    entities = entity_service.extract_entities(article.content)
    sentiment = sentiment_analyzer.analyze(article.content)

    return {
        "entities": entities,
        "sentiment": sentiment
    }
```

## Usage in CLI

### Click Command with Injection

```python
import click
from injectable import injectable_factory
from local_newsifier.di.providers import get_entity_service

@click.command()
@click.argument('text')
def analyze_entities(text: str):
    """Extract entities from text"""
    with injectable_factory():
        entity_service = get_entity_service()
        entities = entity_service.extract_entities(text)

        for entity in entities:
            click.echo(f"{entity.text} ({entity.type})")
```

### Using Injectable Context Manager

```python
from injectable import injectable_factory

def process_feeds():
    with injectable_factory():
        feed_service = get_feed_service()
        feeds = feed_service.get_all()

        for feed in feeds:
            feed_service.process(feed.id)
```

## Testing

### Basic Test with Mocked Dependencies

```python
import pytest
from unittest.mock import Mock
from injectable import injectable_factory, clear_injectables

@pytest.fixture(autouse=True)
def reset_injection():
    clear_injectables()
    yield
    clear_injectables()

def test_article_service():
    # Create mocks
    mock_crud = Mock()
    mock_crud.get.return_value = {"id": 1, "title": "Test"}

    # Register mocks
    with injectable_factory() as factory:
        factory.register(get_article_crud, mock_crud)

        # Test the service
        service = get_article_service()
        result = service.get(1)

        assert result["title"] == "Test"
        mock_crud.get.assert_called_once_with(1)
```

### Testing FastAPI Endpoints

```python
from fastapi.testclient import TestClient
from local_newsifier.api.main import app

def test_get_article(mock_article_service):
    mock_article_service.get.return_value = {
        "id": 1,
        "title": "Test Article"
    }

    with injectable_factory() as factory:
        factory.register(get_article_service, mock_article_service)

        client = TestClient(app)
        response = client.get("/articles/1")

        assert response.status_code == 200
        assert response.json()["title"] == "Test Article"
```

### Test Utilities

```python
from local_newsifier.tests.conftest_injectable import mock_providers, create_mock_with_spec

@pytest.fixture
def mock_deps():
    return mock_providers()

def test_with_utilities(mock_deps):
    # All providers are automatically mocked
    service = get_article_service()

    # Configure specific behavior
    mock_deps[get_article_crud].get.return_value = {"id": 1}

    result = service.get(1)
    assert result["id"] == 1
```

## Anti-Patterns

### 1. Global Instantiation
**Wrong:**
```python
# DON'T DO THIS
analyzer = SentimentAnalyzer()  # Global instance

@injectable(use_cache=False)
def get_sentiment_analyzer():
    return analyzer  # Returns same instance every time
```

**Correct:**
```python
@injectable(use_cache=False)
def get_sentiment_analyzer():
    from local_newsifier.tools.sentiment_analyzer import SentimentAnalyzer
    return SentimentAnalyzer()  # Fresh instance each time
```

### 2. Using Cached Providers
**Wrong:**
```python
@injectable(use_cache=True)  # DON'T USE CACHE
def get_service():
    return MyService()
```

**Correct:**
```python
@injectable(use_cache=False)  # Always use False
def get_service():
    return MyService()
```

### 3. Circular Dependencies
**Wrong:**
```python
# service_a.py
from .service_b import ServiceB  # Circular import!

# service_b.py
from .service_a import ServiceA  # Circular import!
```

**Correct:**
```python
# Use lazy imports in providers
@injectable(use_cache=False)
def get_service_a(service_b: Annotated[Any, Depends(get_service_b)]):
    from .service_a import ServiceA  # Import inside function
    return ServiceA(service_b)
```

### 4. Sharing Database Sessions
**Wrong:**
```python
shared_session = SessionLocal()  # DON'T SHARE SESSIONS

@injectable(use_cache=False)
def get_session():
    return shared_session
```

**Correct:**
```python
@injectable(use_cache=False)
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 5. Hardcoding Dependencies
**Wrong:**
```python
class MyService:
    def __init__(self):
        self.db = SessionLocal()  # Hardcoded dependency
        self.crud = ArticleCRUD()  # Hardcoded dependency
```

**Correct:**
```python
class MyService:
    def __init__(self, session_factory, crud):
        self.session_factory = session_factory
        self.crud = crud
```

## Migration Guide

### From Custom Container to fastapi-injectable

1. **Update Imports**
```python
# Old
from local_newsifier.container import container

# New
from local_newsifier.di.providers import get_article_service
```

2. **Update Service Access**
```python
# Old
service = container.article_service()

# New (in endpoints)
service: Annotated[ArticleService, Depends(get_article_service)]

# New (in CLI/scripts)
with injectable_factory():
    service = get_article_service()
```

3. **Update Tests**
```python
# Old
container.article_service = Mock()

# New
with injectable_factory() as factory:
    factory.register(get_article_service, mock_service)
```

## Examples

### Complete Service Example

```python
from typing import Annotated, Any
from fastapi import Depends
from injectable import injectable
from sqlmodel import Session

from local_newsifier.di.providers import get_session, get_article_crud

@injectable(use_cache=False)
def get_article_service(
    session: Annotated[Session, Depends(get_session)],
    article_crud: Annotated[Any, Depends(get_article_crud)]
):
    from local_newsifier.services.article_service import ArticleService

    return ArticleService(
        session_factory=lambda: session,
        article_crud=article_crud
    )

# Service implementation
class ArticleService:
    def __init__(self, session_factory, article_crud):
        self.session_factory = session_factory
        self.article_crud = article_crud

    def get_by_url(self, url: str):
        with self.session_factory() as session:
            return self.article_crud.get_by_url(session, url)

    def create(self, data: dict):
        with self.session_factory() as session:
            article = self.article_crud.create(session, data)
            session.commit()
            return article.id
```

### Complete Test Example

```python
import pytest
from unittest.mock import Mock, MagicMock
from injectable import injectable_factory, clear_injectables

from local_newsifier.di.providers import (
    get_article_service,
    get_article_crud,
    get_session
)

@pytest.fixture(autouse=True)
def reset_injection():
    clear_injectables()
    yield
    clear_injectables()

def test_article_service_create():
    # Create mocks
    mock_session = MagicMock()
    mock_crud = Mock()
    mock_article = Mock(id=123)
    mock_crud.create.return_value = mock_article

    with injectable_factory() as factory:
        # Register mocks
        factory.register(get_session, mock_session)
        factory.register(get_article_crud, mock_crud)

        # Get service and test
        service = get_article_service()
        result = service.create({"title": "Test"})

        # Verify
        assert result == 123
        mock_crud.create.assert_called_once()
        mock_session.commit.assert_called_once()
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Use lazy imports inside provider functions
   - Check for circular dependencies

2. **Session Errors**
   - Ensure sessions are properly closed
   - Don't pass SQLModel objects between sessions
   - Return IDs instead of objects

3. **Testing Issues**
   - Always call `clear_injectables()` in test setup/teardown
   - Register mocks before using providers
   - Use `injectable_factory()` context manager

4. **Injection Not Working**
   - Verify provider is decorated with `@injectable`
   - Check that `use_cache=False` is set
   - Ensure dependencies use `Depends()` in type annotations

### Debug Tips

```python
# Check registered providers
from injectable import get_injectables
print(list(get_injectables().keys()))

# Verify provider output
with injectable_factory():
    service = get_article_service()
    print(type(service))  # Should be ArticleService
```

## See Also

- [Testing Guide](testing_guide.md) - Comprehensive testing patterns
- [Anti-Patterns Reference](../dependency_injection_antipatterns.md) - Detailed anti-pattern guide
- [Examples](../examples/injectable_examples.md) - Code examples for all patterns

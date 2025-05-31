# Dependency Injection Guide

## Overview

Local Newsifier uses a hybrid dependency injection approach:
- **API**: Native FastAPI dependency injection (`Depends`)
- **CLI**: fastapi-injectable framework (being migrated to HTTP calls)

This guide covers the current state and best practices for both systems.

## Table of Contents
- [Current State](#current-state)
- [FastAPI Native DI (API)](#fastapi-native-di-api)
- [Injectable Pattern (CLI)](#injectable-pattern-cli)
- [Common Patterns](#common-patterns)
- [Testing](#testing)
- [Migration Status](#migration-status)
- [Best Practices](#best-practices)
- [Anti-Patterns](#anti-patterns)

## Current State

### API Layer
The API uses FastAPI's native dependency injection:
```python
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

def get_article(
    article_id: int,
    session: Annotated[Session, Depends(get_session)],
    service: Annotated[ArticleService, Depends(get_article_service)]
):
    return service.get(session, article_id)
```

### CLI Layer
The CLI currently uses fastapi-injectable but is being migrated to make HTTP calls to the API:
```python
from injectable import injectable_factory
from local_newsifier.di.providers import get_article_service

with injectable_factory():
    service = get_article_service()
    article = service.get(article_id)
```

## FastAPI Native DI (API)

### Basic Dependencies

Dependencies are defined in `src/local_newsifier/api/dependencies.py`:

```python
from typing import Generator
from sqlmodel import Session
from local_newsifier.database.engine import get_engine

def get_session() -> Generator[Session, None, None]:
    """Provide database session for requests."""
    engine = get_engine()
    with Session(engine) as session:
        yield session

def get_article_crud() -> CRUDArticle:
    """Provide article CRUD operations."""
    return CRUDArticle()

def get_article_service(
    session: Annotated[Session, Depends(get_session)],
    crud: Annotated[CRUDArticle, Depends(get_article_crud)]
) -> ArticleService:
    """Provide article service with dependencies."""
    return ArticleService(
        article_crud=crud,
        session_factory=lambda: session
    )
```

### Using Dependencies in Routes

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    service: Annotated[ArticleService, Depends(get_article_service)]
) -> ArticleResponse:
    """Get article by ID."""
    article = service.get(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.post("/articles")
def create_article(
    data: ArticleCreate,
    service: Annotated[ArticleService, Depends(get_article_service)]
) -> ArticleResponse:
    """Create new article."""
    return service.create(data.model_dump())
```

### Webhook Handler Example

```python
@router.post("/webhooks/apify", status_code=202)
def apify_webhook(
    webhook_data: ApifyWebhook,
    webhook_service: Annotated[ApifyWebhookService, Depends(get_apify_webhook_service)]
) -> dict:
    """Handle Apify webhooks synchronously."""
    result = webhook_service.handle_webhook(webhook_data)
    return {
        "status": "accepted",
        "actor_id": result.get("actor_id"),
        "dataset_id": result.get("dataset_id")
    }
```

## Injectable Pattern (CLI)

### Provider Functions

Provider functions are defined in `src/local_newsifier/di/providers.py`:

```python
from injectable import injectable
from typing import Annotated, Any
from fastapi import Depends

@injectable(use_cache=False)
def get_session():
    """Provide database session."""
    from local_newsifier.database.engine import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@injectable(use_cache=False)
def get_article_service(
    session: Annotated[Session, Depends(get_session)],
    article_crud: Annotated[Any, Depends(get_article_crud)]
):
    """Provide article service with dependencies."""
    from local_newsifier.services.article_service import ArticleService

    return ArticleService(
        session_factory=lambda: session,
        article_crud=article_crud
    )
```

**Important**: Always use `use_cache=False` to ensure fresh instances.

### Using Injectable in CLI

```python
import click
from injectable import injectable_factory
from local_newsifier.di.providers import get_article_service

@click.command()
@click.argument('article_id', type=int)
def get_article(article_id: int):
    """Get article by ID."""
    with injectable_factory():
        service = get_article_service()
        article = service.get(article_id)

        if article:
            click.echo(f"Title: {article.title}")
            click.echo(f"URL: {article.url}")
        else:
            click.echo(f"Article {article_id} not found")
```

## Common Patterns

### Service Pattern

Services coordinate business logic and should accept dependencies via constructor:

```python
class ArticleService:
    def __init__(self, article_crud: CRUDArticle, session_factory: Callable):
        self.article_crud = article_crud
        self.session_factory = session_factory

    def get(self, article_id: int) -> Optional[Article]:
        with self.session_factory() as session:
            return self.article_crud.get(session, article_id)

    def create(self, data: dict) -> Article:
        with self.session_factory() as session:
            article = self.article_crud.create(session, data)
            session.commit()
            session.refresh(article)
            return article
```

### Session Management

Always use session factories to avoid session lifecycle issues:

```python
# Good - session factory
def process_articles(self, session_factory: Callable):
    with session_factory() as session:
        articles = session.query(Article).all()
        for article in articles:
            # Process article
            pass

# Bad - passing session directly
def process_articles(self, session: Session):  # Don't do this
    articles = session.query(Article).all()  # Session might be closed
```

### Return IDs, Not Objects

To avoid "Instance is not bound to a Session" errors:

```python
# Good - return ID
def create_article(self, data: dict) -> int:
    with self.session_factory() as session:
        article = self.article_crud.create(session, data)
        session.commit()
        return article.id  # Return ID

# Bad - return SQLModel object
def create_article(self, data: dict) -> Article:
    with self.session_factory() as session:
        article = self.article_crud.create(session, data)
        session.commit()
        return article  # Object not bound to session!
```

## Testing

### Testing FastAPI Endpoints

```python
from fastapi.testclient import TestClient
from unittest.mock import Mock

def test_get_article(app):
    # Mock dependencies
    mock_service = Mock()
    mock_service.get.return_value = Article(id=1, title="Test")

    # Override dependency
    app.dependency_overrides[get_article_service] = lambda: mock_service

    # Test endpoint
    client = TestClient(app)
    response = client.get("/articles/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Test"

    # Clean up
    app.dependency_overrides.clear()
```

### Testing Injectable Components

```python
import pytest
from injectable import injectable_factory, clear_injectables
from unittest.mock import Mock

@pytest.fixture(autouse=True)
def reset_injection():
    """Reset injection container for each test."""
    clear_injectables()
    yield
    clear_injectables()

def test_cli_command():
    # Create mocks
    mock_crud = Mock()
    mock_crud.get.return_value = Article(id=1, title="Test")

    # Register mocks
    with injectable_factory() as factory:
        factory.register(get_article_crud, mock_crud)
        factory.register(get_session, Mock())

        # Test command
        runner = CliRunner()
        result = runner.invoke(cli, ["articles", "get", "1"])

        assert result.exit_code == 0
        assert "Test" in result.output
```

## Migration Status

The project is transitioning away from fastapi-injectable in the CLI:

### Current Architecture
- API: ✅ Native FastAPI DI
- CLI: ⚠️ fastapi-injectable (being migrated)
- Tests: 🔄 Mixed patterns

### Target Architecture
- API: ✅ Native FastAPI DI
- CLI: 🎯 HTTP calls to API
- Tests: 🎯 Unified testing approach

### Migration Progress
- [x] API endpoints use native DI
- [x] Database dependencies defined
- [x] Service dependencies defined
- [ ] CLI commands migrated to HTTP client
- [ ] Remove fastapi-injectable dependency

## Best Practices

### 1. Sync-Only Code
All code must be synchronous:
```python
# Good - sync function
def get_articles(session: Session) -> List[Article]:
    return session.query(Article).all()

# Bad - async function
async def get_articles(session: AsyncSession) -> List[Article]:
    return await session.query(Article).all()
```

### 2. Lazy Imports
Import dependencies inside provider functions to avoid circular imports:
```python
@injectable(use_cache=False)
def get_article_service(...):
    # Import here, not at module level
    from local_newsifier.services.article_service import ArticleService
    return ArticleService(...)
```

### 3. Explicit Dependencies
Always declare dependencies explicitly:
```python
# Good - explicit dependencies
def __init__(self, crud: CRUDArticle, session_factory: Callable):
    self.crud = crud
    self.session_factory = session_factory

# Bad - hidden dependencies
def __init__(self):
    self.crud = CRUDArticle()  # Hidden dependency
    self.session = SessionLocal()  # Hidden dependency
```

### 4. No Caching
Never cache dependency instances:
```python
# Good - fresh instance each time
@injectable(use_cache=False)
def get_service():
    return MyService()

# Bad - cached instance
@injectable(use_cache=True)  # Don't do this
def get_service():
    return MyService()
```

## Anti-Patterns

### 1. Global Instances
```python
# Bad - global instance
parser = RSSParser()  # Global state

@injectable(use_cache=False)
def get_parser():
    return parser  # Returns same instance

# Good - fresh instance
@injectable(use_cache=False)
def get_parser():
    return RSSParser()  # New instance each time
```

### 2. Shared Sessions
```python
# Bad - shared session
shared_session = SessionLocal()

def get_data():
    return shared_session.query(Article).all()

# Good - session factory
def get_data(session_factory):
    with session_factory() as session:
        return session.query(Article).all()
```

### 3. Mixing Patterns
```python
# Bad - inconsistent access
# File 1
from local_newsifier.services import ArticleService
service = ArticleService()  # Direct instantiation

# File 2
from local_newsifier.di.providers import get_article_service
service = get_article_service()  # DI pattern

# Good - consistent DI usage everywhere
from local_newsifier.di.providers import get_article_service
service = get_article_service()
```

### 4. Import-Time Initialization
```python
# Bad - runs at import time
database = Database()  # Connects at import
model = load_model()   # Loads at import

# Good - lazy initialization
def get_database():
    return Database()  # Connects when needed

def get_model():
    return load_model()  # Loads when needed
```

## Troubleshooting

### Common Issues

1. **"Instance is not bound to a Session"**
   - Return IDs instead of SQLModel objects
   - Use session factories, not direct sessions

2. **Circular Import Errors**
   - Use lazy imports inside provider functions
   - Check dependency graph for cycles

3. **Session Already Closed**
   - Ensure proper session lifecycle management
   - Use context managers (`with session:`)

4. **Injection Not Working**
   - Verify `@injectable` decorator is present
   - Check `use_cache=False` is set
   - Ensure `injectable_factory()` context is active

### Debug Tips

```python
# Check registered providers
from injectable import get_injectables
print(list(get_injectables().keys()))

# Verify dependency resolution
with injectable_factory():
    service = get_article_service()
    print(type(service))  # Should be ArticleService
```

## See Also

- [Testing Guide](testing_guide.md) - Testing patterns for DI
- [CLI Usage Guide](cli_usage.md) - CLI commands and patterns
- [Error Handling Guide](error_handling.md) - Error handling patterns

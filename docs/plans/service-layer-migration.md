# Service Layer Migration Plan

## Overview

This document outlines the migration strategy for updating service classes to work with the new FastAPI-based CLI architecture, removing dependency injection decorators and updating method signatures.

## Key Changes

### 1. Remove @injectable Decorators
All service classes will have the `@injectable` decorator removed, transitioning to standard Python classes.

### 2. Update Constructor Patterns
Services will accept optional session factories to maintain backward compatibility while supporting new patterns.

### 3. Sync-Only Implementation
All services will use synchronous patterns only. The project is moving away from async implementations to simplify the codebase and improve maintainability.

## Migration Examples

### Before (Injectable Pattern)
```python
from fastapi_injectable import injectable
from typing import Annotated
from fastapi import Depends

@injectable
class ArticleService:
    def __init__(
        self,
        article_crud: Annotated[ArticleCRUD, Depends(get_article_crud)],
        session: Annotated[Session, Depends(get_session)]
    ):
        self.article_crud = article_crud
        self.session = session

    def process_article(self, url: str):
        # Uses injected session
        return self.article_crud.create(self.session, url=url)
```

### After (Sync-Only Pattern)
```python
from typing import Optional
from sqlmodel import Session

class ArticleService:
    def __init__(self, session_factory=None):
        # Make session_factory optional for flexibility
        self.session_factory = session_factory

    # All methods are synchronous and accept session as parameter
    def process_article(self, session: Session, url: str):
        from crud.article import ArticleCRUD
        article_crud = ArticleCRUD()
        return article_crud.create(session, url=url)

    def process_article_with_content(self, session: Session, url: str, content: Optional[str]):
        """Process article with optional content."""
        # Business logic here
        pass

# FastAPI dependency function
def get_article_service() -> ArticleService:
    return ArticleService()
```

## Service Categories

### 1. Core Services
Services that handle primary business logic:
- `ArticleService`
- `EntityService`
- `AnalysisService`
- `OpinionService`

**Migration Priority**: High

### 2. Integration Services
Services that interact with external systems:
- `ApifyService`
- `NewsAPIService`
- `ScraperService`

**Migration Priority**: Medium

### 3. Utility Services
Helper services with minimal dependencies:
- `ReportService`
- `ExportService`
- `NotificationService`

**Migration Priority**: Low

## Migration Steps

### Step 1: Update Service Class
1. Remove `@injectable` decorator
2. Update constructor to accept optional parameters
3. Remove dependency injection annotations

### Step 2: Add Session Parameters
1. Update all methods to accept `session` parameter
2. Remove references to `self.session`
3. Update method signatures consistently

### Step 3: Ensure Sync-Only Implementation
1. Remove any existing async methods
2. Convert async operations to sync equivalents
3. Use synchronous libraries and clients

### Step 4: Update FastAPI Dependencies
1. Create simple factory functions
2. Remove complex dependency chains
3. Update router imports

### Step 5: Update Tests
1. Pass session explicitly in tests
2. Remove dependency injection mocks
3. Simplify test fixtures

## Common Patterns

### Pattern 1: Simple Service
```python
class SimpleService:
    def operation(self, session: Session, param: str):
        # Direct implementation
        pass

def get_simple_service() -> SimpleService:
    return SimpleService()
```

### Pattern 2: Service with Dependencies
```python
class ComplexService:
    def __init__(self, config=None):
        self.config = config or load_default_config()

    def operation(self, session: Session, param: str):
        # Use self.config and session
        pass

def get_complex_service() -> ComplexService:
    config = load_config()
    return ComplexService(config)
```

### Pattern 3: External API Service
```python
import requests

class ExternalAPIService:
    def fetch_data(self, session: Session, param: str):
        # Use synchronous HTTP client
        response = requests.get(f"https://api.example.com/{param}")
        response.raise_for_status()
        return response.json()

    def process_external_data(self, session: Session, data: dict):
        # Process data synchronously
        pass
```

## Testing Considerations

### Before
```python
@pytest.fixture
def mock_article_service(mock_session):
    with patch("get_article_crud") as mock_crud:
        service = ArticleService()
        yield service
```

### After
```python
@pytest.fixture
def article_service():
    return ArticleService()

def test_process_article(article_service, db_session):
    result = article_service.process_article(db_session, "https://example.com")
    assert result is not None
```

## Rollback Strategy

If issues arise during migration:

1. **Dual Support Period**
   - Keep both patterns working temporarily
   - Use feature flags to switch between them

2. **Gradual Migration**
   - Migrate one service at a time
   - Test thoroughly before proceeding

3. **Compatibility Layer**
   - Create adapter classes if needed
   - Maintain API compatibility

## Success Metrics

- All services migrated without functionality loss
- Test coverage maintained or improved
- No performance degradation
- Simplified dependency management
- Easier debugging and maintenance

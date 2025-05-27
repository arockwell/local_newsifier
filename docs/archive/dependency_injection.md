# Dependency Injection Guide

Local Newsifier uses **fastapi-injectable** as its dependency injection framework. All dependencies are exposed through provider functions defined in `local_newsifier.di.providers` and injected with FastAPI's `Depends()` syntax.

## Provider Functions

Provider functions are decorated with `@injectable(use_cache=False)` to ensure a new instance is created on each injection. This avoids state leakage between requests.

```python
from typing import Generator
from fastapi_injectable import injectable
from sqlmodel import Session

@injectable(use_cache=False)
def get_session() -> Generator[Session, None, None]:
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()
```

## Injectable Classes

Use the `@injectable` decorator on classes to declare constructor dependencies with `Annotated` and `Depends`.

```python
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable

@injectable(use_cache=False)
class ArticleService:
    def __init__(self, session: Annotated[Session, Depends(get_session)]):
        self.session = session
```

## Usage in FastAPI Endpoints

```python
@app.get("/articles/{article_id}")
async def get_article(
    article_id: int,
    service: Annotated[ArticleService, Depends()]
):
    return service.fetch(article_id)
```

## Testing Providers

Tests can override provider functions using `monkeypatch`:

```python
@pytest.fixture
def patch_session(monkeypatch):
    mock_session = MagicMock()
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_session",
        lambda: mock_session
    )
    return mock_session
```

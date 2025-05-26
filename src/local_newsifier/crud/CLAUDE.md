# Local Newsifier CRUD Guide

## Overview
The CRUD (Create, Read, Update, Delete) module provides database access patterns for all models in the system. It includes both synchronous and asynchronous implementations to support different use cases.

## Architecture

### Base Classes
- **CRUDBase**: Synchronous base class for standard CRUD operations
- **AsyncCRUDBase**: Asynchronous base class for async CRUD operations
- Both provide generic implementations of common database operations

### Model-Specific CRUD Classes
Each model has its own CRUD class that extends the base:
- `CRUDArticle` / `AsyncCRUDArticle` - Article operations
- `CRUDEntity` - Entity operations
- `CRUDRSSFeed` - RSS feed operations
- `CRUDApifySourceConfig` - Apify source configuration
- And more...

## Synchronous CRUD Patterns

### Basic Operations

```python
from local_newsifier.crud.article import article as article_crud
from local_newsifier.models.article import Article

# Get by ID
article = article_crud.get(db=session, id=1)

# Get multiple with pagination
articles = article_crud.get_multi(db=session, skip=0, limit=10)

# Create
new_article = Article(
    title="Breaking News",
    content="Article content...",
    url="https://example.com/article"
)
created = article_crud.create(db=session, obj_in=new_article)

# Update
updated = article_crud.update(
    db=session,
    db_obj=article,
    obj_in={"title": "Updated Title"}
)

# Delete
article_crud.remove(db=session, id=1)
```

### Custom Query Methods

CRUD classes often include model-specific queries:

```python
class CRUDArticle(CRUDBase[Article]):
    def get_by_url(self, db: Session, url: str) -> Optional[Article]:
        """Get article by URL."""
        return db.exec(
            select(Article).where(Article.url == url)
        ).first()

    def get_by_date_range(
        self, db: Session, start_date: datetime, end_date: datetime
    ) -> List[Article]:
        """Get articles within date range."""
        return db.exec(
            select(Article)
            .where(Article.created_at >= start_date)
            .where(Article.created_at <= end_date)
            .order_by(Article.created_at.desc())
        ).all()
```

## Asynchronous CRUD Patterns

The async CRUD classes provide the same functionality but with async/await syntax:

### Async Base Class

```python
from local_newsifier.crud.async_base import AsyncCRUDBase
from sqlalchemy.ext.asyncio import AsyncSession

class AsyncCRUDBase(Generic[ModelType]):
    async def get(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        """Get a single record by ID asynchronously."""
        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, obj_in: ModelType) -> ModelType:
        """Create a new record asynchronously."""
        session.add(obj_in)
        await session.flush()  # Ensure ID is generated
        await session.refresh(obj_in)  # Load relationships
        return obj_in
```

### Using Async CRUD

```python
from local_newsifier.crud.async_article import async_article
from local_newsifier.database.async_engine import get_async_session

async def process_article_async(article_id: int):
    async with get_async_session() as session:
        # Get article
        article = await async_article.get(session, article_id)

        # Update article
        updated = await async_article.update(
            session,
            db_obj=article,
            obj_in={"processed": True}
        )

        await session.commit()
        return updated.id
```

### Async Query Patterns

Async CRUD uses SQLAlchemy's async query syntax:

```python
class AsyncCRUDArticle(AsyncCRUDBase[Article]):
    async def get_by_url(self, session: AsyncSession, url: str) -> Optional[Article]:
        """Get article by URL asynchronously."""
        result = await session.execute(
            select(Article).where(Article.url == url)
        )
        return result.scalar_one_or_none()

    async def count_by_source(self, session: AsyncSession, source_id: str) -> int:
        """Count articles by source asynchronously."""
        result = await session.execute(
            select(func.count(Article.id)).where(Article.source_id == source_id)
        )
        return result.scalar()
```

## When to Use Sync vs Async CRUD

### Use Synchronous CRUD When:
- Working in CLI commands
- Processing with Celery background tasks
- Simple sequential operations
- Legacy code that doesn't support async

### Use Asynchronous CRUD When:
- Handling FastAPI web requests
- Processing webhooks
- Concurrent database operations
- I/O-bound operations that benefit from concurrency

## Best Practices

### Session Management
- Always use sessions provided by dependency injection
- Don't create sessions directly in CRUD classes
- Let the caller manage transaction boundaries

### Error Handling
```python
from sqlalchemy.exc import IntegrityError

try:
    article = article_crud.create(db=session, obj_in=new_article)
    session.commit()
except IntegrityError as e:
    session.rollback()
    if "unique constraint" in str(e):
        # Handle duplicate
        raise ValueError("Article with this URL already exists")
    raise
```

### Query Optimization
- Use `selectinload()` for eager loading relationships
- Add indexes for frequently queried fields
- Use pagination for large result sets
- Consider query result caching for expensive operations

### Return Values
- Return model instances from CRUD operations
- Let services handle conversion to dicts/IDs
- This allows for relationship access when needed

### Testing CRUD Operations
```python
def test_crud_article_create(db_session):
    # Create test data
    article_data = Article(
        title="Test Article",
        content="Test content",
        url="https://test.com/article"
    )

    # Test create
    created = article_crud.create(db=db_session, obj_in=article_data)
    assert created.id is not None
    assert created.title == "Test Article"

    # Verify in database
    fetched = article_crud.get(db=db_session, id=created.id)
    assert fetched.title == "Test Article"
```

## Common Patterns

### Bulk Operations
```python
def create_many(self, db: Session, obj_in_list: List[ModelType]) -> List[ModelType]:
    """Create multiple records efficiently."""
    db.add_all(obj_in_list)
    db.flush()
    return obj_in_list
```

### Soft Deletes
```python
def soft_delete(self, db: Session, id: int) -> Optional[ModelType]:
    """Mark record as deleted without removing from database."""
    obj = self.get(db=db, id=id)
    if obj:
        obj.deleted_at = datetime.now(UTC)
        db.add(obj)
        db.flush()
    return obj
```

### Query Builders
```python
def build_filter_query(self, **filters):
    """Build query with dynamic filters."""
    query = select(self.model)

    if filters.get("title"):
        query = query.where(self.model.title.contains(filters["title"]))

    if filters.get("created_after"):
        query = query.where(self.model.created_at >= filters["created_after"])

    return query
```

## Migration to Async

When migrating from sync to async CRUD:

1. Create async version alongside sync version
2. Update method signatures with `async def`
3. Replace `session.exec()` with `await session.execute()`
4. Use `scalar_one_or_none()` instead of `.first()`
5. Add `await` to all database operations
6. Update callers to use async/await

Example migration:
```python
# Sync version
def get_by_url(self, db: Session, url: str) -> Optional[Article]:
    return db.exec(select(Article).where(Article.url == url)).first()

# Async version
async def get_by_url(self, session: AsyncSession, url: str) -> Optional[Article]:
    result = await session.execute(select(Article).where(Article.url == url))
    return result.scalar_one_or_none()
```

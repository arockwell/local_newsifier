# CRUDArticle Simplification Guide

## Overview

The custom `create()` method in CRUDArticle has been removed by moving the timestamp logic to the model's field definition. This eliminates redundant code and follows SQLModel best practices.

## Changes Made

### Before: Custom create() in CRUD

```python
class CRUDArticle(CRUDBase[Article]):
    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], Article]) -> Article:
        # Handle dict or model instance
        if isinstance(obj_in, dict):
            article_data = obj_in
        else:
            article_data = obj_in.model_dump(exclude_unset=True)

        # Add scraped_at if not provided
        if "scraped_at" not in article_data or article_data["scraped_at"] is None:
            article_data["scraped_at"] = datetime.now(timezone.utc)

        db_article = Article(**article_data)
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return db_article
```

### After: Default in Model

```python
# In models/article.py
class Article(SQLModel, table=True):
    # Other fields...
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
```

Now CRUDArticle inherits the standard `create()` method from CRUDBase, which handles everything correctly.

## Benefits

1. **Less code** - Removed 25 lines of custom logic
2. **Single source of truth** - Default timestamp logic in model definition
3. **Consistency** - All timestamp fields use same pattern
4. **Simpler testing** - Don't need to test custom create logic

## Migration Notes

### For New Code

No changes needed - the scraped_at field will be automatically set when creating articles:

```python
article = article_crud.create(session, obj_in={
    "title": "News Title",
    "content": "Content",
    "url": "https://example.com",
    "source": "Example",
    "published_at": datetime.now(),
    "status": "new"
    # scraped_at is automatically set
})
```

### For Existing Code

If you were explicitly setting scraped_at, you can continue to do so (it will override the default):

```python
article = article_crud.create(session, obj_in={
    "title": "News Title",
    "content": "Content",
    "url": "https://example.com",
    "source": "Example",
    "published_at": datetime.now(),
    "status": "new",
    "scraped_at": custom_timestamp  # Still works
})
```

## Pattern to Follow

This same pattern can be applied to other timestamp fields:

```python
class MyModel(SQLModel, table=True):
    # Automatic timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC).replace(tzinfo=None)}
    )
```

## Database Migration

No database migration needed - this is a code-only change. The database schema remains the same.

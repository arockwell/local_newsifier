# CRUD Testing Guide

This guide covers testing patterns for CRUD (Create, Read, Update, Delete) operations in Local Newsifier.

## CRUD Test Structure

All CRUD tests should use a real SQLite in-memory database:
```python
def test_crud_operation(session, sample_article_data):
    # Arrange - Create CRUD instance
    crud = ArticleCRUD()

    # Act - Perform CRUD operation
    article = crud.create(session, sample_article_data)

    # Assert - Verify database state
    assert article.id is not None
    assert article.title == sample_article_data["title"]

    # Verify in database
    db_article = session.get(Article, article.id)
    assert db_article is not None
```

## Testing Create Operations

### Basic Create
```python
def test_create_article(session, sample_article_data):
    crud = ArticleCRUD()

    # Create article
    article = crud.create(session, sample_article_data)

    # Verify all fields
    assert article.id is not None
    assert article.title == sample_article_data["title"]
    assert article.content == sample_article_data["content"]
    assert article.url == sample_article_data["url"]
    assert article.published_at is not None
```

### Create with Relationships
```python
def test_create_with_relationships(session, sample_article_data):
    crud = ArticleCRUD()
    entity_crud = EntityCRUD()

    # Create article
    article = crud.create(session, sample_article_data)

    # Create related entities
    entity_data = {
        "name": "Test Entity",
        "type": "PERSON",
        "article_id": article.id
    }
    entity = entity_crud.create(session, entity_data)

    # Verify relationship
    session.refresh(article)
    assert len(article.entities) == 1
    assert article.entities[0].name == "Test Entity"
```

### Create with Validation
```python
def test_create_validates_required_fields(session):
    crud = ArticleCRUD()

    # Missing required field
    invalid_data = {
        "content": "Content without title"
    }

    with pytest.raises(ValueError, match="title is required"):
        crud.create(session, invalid_data)
```

## Testing Read Operations

### Get by ID
```python
def test_get_by_id(session, create_article):
    crud = ArticleCRUD()

    # Get existing article
    article = crud.get(session, create_article.id)
    assert article is not None
    assert article.id == create_article.id

    # Get non-existent article
    article = crud.get(session, 999)
    assert article is None
```

### Get All with Pagination
```python
def test_get_all_paginated(session, create_multiple_articles):
    crud = ArticleCRUD()

    # Get first page
    articles = crud.get_all(session, skip=0, limit=2)
    assert len(articles) == 2

    # Get second page
    articles = crud.get_all(session, skip=2, limit=2)
    assert len(articles) == 2

    # Get all
    all_articles = crud.get_all(session)
    assert len(all_articles) == 5  # Assuming 5 articles created
```

### Get with Filters
```python
def test_get_with_filters(session, create_multiple_articles):
    crud = ArticleCRUD()

    # Filter by date range
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    articles = crud.get_by_date_range(session, start_date, end_date)
    assert all(start_date <= a.published_at <= end_date for a in articles)

    # Filter by keyword
    articles = crud.search(session, query="important")
    assert all("important" in a.title.lower() for a in articles)
```

### Get with Joins
```python
def test_get_with_relationships(session, create_article_with_entities):
    crud = ArticleCRUD()

    # Get article with entities loaded
    article = crud.get_with_entities(session, create_article_with_entities.id)

    assert article is not None
    assert len(article.entities) > 0
    # Entities should be loaded (no additional query)
    assert all(e.name is not None for e in article.entities)
```

## Testing Update Operations

### Basic Update
```python
def test_update_article(session, create_article):
    crud = ArticleCRUD()

    # Update article
    update_data = {"title": "Updated Title"}
    updated = crud.update(session, create_article.id, update_data)

    # Verify update
    assert updated.title == "Updated Title"
    assert updated.content == create_article.content  # Unchanged

    # Verify in database
    db_article = session.get(Article, create_article.id)
    assert db_article.title == "Updated Title"
```

### Partial Update
```python
def test_partial_update(session, create_article):
    crud = ArticleCRUD()

    # Update only specific fields
    original_content = create_article.content
    update_data = {
        "title": "New Title",
        "processed": True
    }

    updated = crud.update(session, create_article.id, update_data)

    assert updated.title == "New Title"
    assert updated.processed is True
    assert updated.content == original_content  # Unchanged
```

### Update Non-existent
```python
def test_update_non_existent(session):
    crud = ArticleCRUD()

    update_data = {"title": "Updated"}
    updated = crud.update(session, 999, update_data)

    assert updated is None
```

## Testing Delete Operations

### Basic Delete
```python
def test_delete_article(session, create_article):
    crud = ArticleCRUD()
    article_id = create_article.id

    # Delete article
    success = crud.delete(session, article_id)
    assert success is True

    # Verify deleted
    article = session.get(Article, article_id)
    assert article is None
```

### Delete with Cascade
```python
def test_delete_cascade(session, create_article_with_entities):
    crud = ArticleCRUD()
    article_id = create_article_with_entities.id
    entity_ids = [e.id for e in create_article_with_entities.entities]

    # Delete article (should cascade to entities)
    crud.delete(session, article_id)

    # Verify article deleted
    assert session.get(Article, article_id) is None

    # Verify entities deleted (if cascade configured)
    for entity_id in entity_ids:
        assert session.get(Entity, entity_id) is None
```

### Delete Non-existent
```python
def test_delete_non_existent(session):
    crud = ArticleCRUD()

    success = crud.delete(session, 999)
    assert success is False
```

## Testing Custom CRUD Methods

### Duplicate Detection
```python
def test_find_duplicates(session, create_multiple_articles):
    crud = ArticleCRUD()

    # Create duplicate
    duplicate_data = {
        "title": create_multiple_articles[0].title,
        "content": "Different content",
        "url": "http://different.url"
    }
    crud.create(session, duplicate_data)

    # Find duplicates
    duplicates = crud.find_duplicates(session)

    assert len(duplicates) > 0
    assert any(d.title == duplicate_data["title"] for d in duplicates)
```

### Bulk Operations
```python
def test_bulk_create(session):
    crud = ArticleCRUD()

    # Prepare bulk data
    articles_data = [
        {"title": f"Article {i}", "content": f"Content {i}", "url": f"http://example.com/{i}"}
        for i in range(10)
    ]

    # Bulk create
    created = crud.bulk_create(session, articles_data)

    assert len(created) == 10
    assert all(a.id is not None for a in created)
```

### Complex Queries
```python
def test_complex_query(session, create_articles_with_entities):
    crud = ArticleCRUD()

    # Get articles with specific entity type
    articles = crud.get_by_entity_type(session, "PERSON")

    assert len(articles) > 0
    assert all(
        any(e.type == "PERSON" for e in article.entities)
        for article in articles
    )
```

## Testing Transactions

### Rollback on Error
```python
def test_transaction_rollback(session):
    crud = ArticleCRUD()

    try:
        # Start transaction
        article = crud.create(session, {"title": "Test", "content": "Content", "url": "http://test.com"})

        # Simulate error
        raise ValueError("Simulated error")

    except ValueError:
        session.rollback()

    # Verify nothing was saved
    articles = crud.get_all(session)
    assert len(articles) == 0
```

## Testing Edge Cases

### Unicode and Special Characters
```python
def test_unicode_handling(session):
    crud = ArticleCRUD()

    # Create with unicode
    data = {
        "title": "Article with émojis 🎉 and ñoñ-ASCII",
        "content": "Content with special chars: €£¥",
        "url": "http://example.com/unicode"
    }

    article = crud.create(session, data)

    # Verify stored correctly
    retrieved = crud.get(session, article.id)
    assert retrieved.title == data["title"]
    assert retrieved.content == data["content"]
```

### Large Data
```python
def test_large_content(session):
    crud = ArticleCRUD()

    # Create with large content
    large_content = "x" * 10000  # 10KB of content
    data = {
        "title": "Large Article",
        "content": large_content,
        "url": "http://example.com/large"
    }

    article = crud.create(session, data)
    assert len(article.content) == 10000
```

## Best Practices

1. **Use real database for CRUD tests** - SQLite in-memory is fast and realistic
2. **Test all CRUD operations** - Create, Read, Update, Delete
3. **Test edge cases** - Empty results, None values, invalid data
4. **Test relationships** - Verify foreign keys and cascades work
5. **Use fixtures for test data** - Consistent, reusable test data
6. **Clean up after tests** - Use function-scoped sessions
7. **Test constraints** - Unique constraints, required fields
8. **Verify database state** - Don't just check return values

## Common Fixtures

```python
@pytest.fixture
def sample_article_data():
    return {
        "title": "Test Article",
        "content": "Test content",
        "url": "http://example.com/test",
        "source": "test",
        "published_at": datetime.now()
    }

@pytest.fixture
def create_article(session, sample_article_data):
    crud = ArticleCRUD()
    return crud.create(session, sample_article_data)

@pytest.fixture
def create_multiple_articles(session):
    crud = ArticleCRUD()
    articles = []
    for i in range(5):
        data = {
            "title": f"Article {i}",
            "content": f"Content {i}",
            "url": f"http://example.com/{i}"
        }
        articles.append(crud.create(session, data))
    return articles
```

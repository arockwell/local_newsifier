# Enhanced Testing Framework Guide

This guide provides a comprehensive explanation of the testing infrastructure implemented for issue #86: "Enhance Testing Infrastructure and Framework".

## Table of Contents

1. [Key Components](#key-components)
2. [Setting Up Test Database](#setting-up-test-database)
3. [Creating Test Data](#creating-test-data)
4. [Mocking Services](#mocking-services)
5. [Verifying Database State](#verifying-database-state)
6. [Testing API Endpoints](#testing-api-endpoints)
7. [Managing Environment Variables](#managing-environment-variables)
8. [Best Practices](#best-practices)
9. [Migration Guide](#migration-guide)

## Key Components

The enhanced testing infrastructure includes several key components:

- **Database Session Fixtures**: Transaction-based session management for test isolation
- **Model Factories**: Factory-based test data generation 
- **Mock Service Factories**: Standardized service mocking
- **Database Verification**: Helpers for verifying database state
- **API Testing Utilities**: Tools for testing API endpoints
- **Environment Management**: Utilities for managing environment variables

These components are available in their respective modules under `tests/utils/`.

## Setting Up Test Database

### Database Session Fixtures

The framework provides several database session fixtures with different scopes:

```python
def test_something(db_function_session):
    # Function-scoped session, will be rolled back after each test

def test_module_level(db_module_session):
    # Module-scoped session, shared across all tests in the module

def test_class_level(db_class_session):
    # Class-scoped session, shared across all tests in the class
```

The framework automatically determines the test database URL based on the following precedence:

1. `TEST_DATABASE_URL` environment variable
2. PostgreSQL configuration for Cursor instances
3. In-memory SQLite as a fallback

### Transaction Isolation

Each test runs in its own transaction, which is rolled back after the test. This ensures that tests don't interfere with each other:

```python
def test_create_entity(db_function_session):
    entity = CanonicalEntity(name="Test Entity")
    db_function_session.add(entity)
    db_function_session.commit()
    
    # Changes are visible within this test
    assert entity.id is not None
    
    # After test completes, transaction is rolled back automatically
    # and changes are not visible to other tests
```

## Creating Test Data

### Model Factories

The framework uses the factory_boy and Faker libraries to generate realistic test data:

```python
from tests.utils.factories import ArticleFactory, EntityFactory

# Create an instance but don't save it to the database
article = ArticleFactory.build()

# Create and save to the database
ArticleFactory._meta.sqlalchemy_session = db_function_session
db_article = ArticleFactory.create(title="Custom Title")

# Create multiple instances
articles = ArticleFactory.create_batch(5)

# Create instance with related entities
article = ArticleFactory.create()
entities = EntityFactory.create_batch(3, article=article)
```

### Factory Utilities

The framework provides utility functions for creating more complex test data scenarios:

```python
from tests.utils.factories import create_article_batch, create_related_entities

# Create a batch of articles
articles = create_article_batch(db_function_session, count=3)

# Create related entities with relationships
entities, relationships = create_related_entities(db_function_session, count=4)
```

### Pre-populated Database

For tests that need a standard set of test data, use the `populated_db` fixture:

```python
def test_with_standard_data(populated_db):
    # Access the database session
    session = populated_db["session"]
    
    # Access standard test data
    articles = populated_db["articles"]
    entities = populated_db["entities"]
    canonical_entities = populated_db["canonical_entities"]
    relationships = populated_db["relationships"]
    
    # Use the data for testing
    result = some_function_that_needs_data(articles[0])
    assert result is not None
```

## Mocking Services

### Mock Service Factories

The framework provides factories for creating mock service instances:

```python
from tests.utils.mocks import (
    create_mock_rss_service, create_mock_entity_service,
    create_mock_article_service, create_mock_analysis_service
)

# Create a mock RSS service with default behaviors
rss_service = create_mock_rss_service()

# Create a mock with custom behaviors
entity_service = create_mock_entity_service(
    extract_entities=[{"id": 1, "text": "Entity 1"}],
    get_entity={"id": 1, "name": "Entity 1"},
)

# Create a mock with a callable behavior
def dynamic_behavior(article_id, **kwargs):
    return {"id": article_id, "title": f"Article {article_id}"}

article_service = create_mock_article_service(
    get_article=dynamic_behavior
)
```

### Mock Fixtures

The framework provides fixtures for common mock services:

```python
def test_with_mock_services(mock_rss_service, mock_entity_service):
    # Configure behaviors
    mock_rss_service.fetch_feed.return_value = {"items": []}
    mock_entity_service.extract_entities.return_value = [{"id": 1, "text": "Entity 1"}]
    
    # Use the mocks
    result = some_function_that_uses_services(mock_rss_service, mock_entity_service)
    
    # Verify interactions
    mock_rss_service.fetch_feed.assert_called_once()
    assert mock_entity_service.extract_entities.call_count == 2
```

### Service Patching

For tests that need to patch services at the module level:

```python
from tests.utils.mocks import ServicePatcher

def test_with_patched_services(service_patcher):
    # Create mock instances
    mock_rss = create_mock_rss_service()
    mock_entity = create_mock_entity_service()
    
    # Patch the services
    with service_patcher.patch_rss_service(mock_rss):
        with service_patcher.patch_entity_service(mock_entity):
            # Code that uses the services will now use the mocks
            result = function_that_imports_services()
            
            # Verify interactions
            assert mock_rss.fetch_feed.called
```

## Verifying Database State

### Database Verifier

The framework provides a `DatabaseVerifier` class for checking database state:

```python
def test_database_operations(db_function_session, db_verifier):
    # Perform operations
    article = ArticleFactory.build()
    db_function_session.add(article)
    db_function_session.commit()
    
    # Verify record exists
    db_verifier.assert_exists(Article, id=article.id, title=article.title)
    
    # Verify record count
    db_verifier.assert_count(Article, 1)
    
    # Verify field values
    record = db_verifier.find_one(Article, id=article.id)
    db_verifier.assert_fields(record, {
        "title": article.title,
        "status": article.status
    })
    
    # Verify record count changes
    def create_more_articles():
        ArticleFactory._meta.sqlalchemy_session = db_function_session
        ArticleFactory.create_batch(3)
    
    db_verifier.assert_record_count_changed(Article, create_more_articles, 3)
```

### Model Tester

For comprehensive model testing:

```python
def test_model_operations(db_function_session, model_tester):
    # Create a model tester for the Article model
    article_tester = model_tester(Article, db_function_session)
    
    # Test CRUD operations
    create_data = ArticleFactory.build_dict()
    update_data = {"title": "Updated Title", "status": "analyzed"}
    
    # This will test create, get, update, and delete operations
    article_tester.assert_crud_operations(create_data, update_data)
```

## Testing API Endpoints

### API Testing Utilities

The framework provides utilities for testing API endpoints:

```python
def test_api_endpoints(api_client, api_helper, auth_token):
    # Simple GET request
    response = api_client.get("/api/articles")
    assert response.status_code == 200
    
    # GET with helper for assertions
    data = api_helper.get("/api/articles", expected_status=200)
    assert len(data["items"]) > 0
    
    # POST with authentication
    new_article = ArticleFactory.build_dict()
    result = api_helper.post(
        "/api/articles", 
        data=new_article,
        auth_token=auth_token,
        expected_status=201
    )
    assert result["id"] is not None
    
    # Test pagination structure
    data = api_helper.get("/api/articles")
    api_helper.assert_paginated_response(data, expected_item_count=10)
```

## Managing Environment Variables

### Environment Manager

The framework provides utilities for managing environment variables:

```python
def test_with_clean_environment(clean_environment):
    # Test runs with app-related environment variables cleared
    
def test_with_test_database(test_db_environment):
    # Test runs with database environment variables set to test values
    
def test_with_specific_variables(with_env_vars):
    # Temporarily set specific variables
    with with_env_vars({"API_KEY": "test_key", "DEBUG": "true"}):
        # Code that uses these environment variables
        pass
    # Variables are restored to original values
```

## Best Practices

1. **Use Factories**: Use the model factories for creating test data, rather than manually instantiating models.

2. **Transaction Isolation**: Leverage transaction-based isolation to keep tests independent.

3. **Proper Verification**: Use the database verifier to check database state, rather than making multiple assertions.

4. **Mock Services**: Use the mock service factories to create standardized mocks.

5. **Environment Management**: Use the environment management utilities to ensure environment variables don't interfere between tests.

6. **Test Cleanup**: The framework automatically handles cleanup, but be mindful of external resources that may need explicit cleanup.

7. **Test Independence**: Each test should be independent and not rely on state from other tests.

## Migration Guide

### Migrating Existing Tests

For existing tests, the following changes are recommended:

1. Replace `db_session` with `db_function_session` for better isolation.

2. Replace manual model creation with factory-based creation:

   **Before**:
   ```python
   article = Article(
       title="Test Article",
       content="This is a test article.",
       url="https://example.com/test-article",
       source="test_source",
       published_at=datetime.now(timezone.utc),
       status="new",
       scraped_at=datetime.now(timezone.utc),
   )
   db_session.add(article)
   db_session.commit()
   ```

   **After**:
   ```python
   ArticleFactory._meta.sqlalchemy_session = db_function_session
   article = ArticleFactory.create(
       title="Test Article",
       content="This is a test article."
   )
   ```

3. Replace manual verification with verifier-based checks:

   **Before**:
   ```python
   statement = select(Article).where(Article.id == article.id)
   result = db_session.exec(statement).first()
   assert result is not None
   assert result.title == "Test Article"
   ```

   **After**:
   ```python
   db_verifier.assert_exists(Article, id=article.id, title="Test Article")
   ```

4. Replace manual mock creation with mock factories:

   **Before**:
   ```python
   mock_service = MagicMock()
   mock_service.fetch_feed.return_value = {"items": []}
   ```

   **After**:
   ```python
   mock_service = create_mock_rss_service(fetch_feed={"items": []})
   ```

### Example Refactored Test

See `tests/crud/test_article_refactored.py` for a complete example of a refactored test module that uses the new testing infrastructure.

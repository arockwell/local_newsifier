# Error Handling Migration Guide

## Overview

The `@handle_database` decorator pattern is being replaced with a unified `database_operation` context manager to reduce code duplication and provide more consistent error handling.

## Migration Examples

### Before: Using @handle_database decorator

```python
from local_newsifier.errors import handle_database

class ArticleService:
    @handle_database
    def process_article(self, url: str, content: str) -> Dict[str, Any]:
        """Process an article."""
        with self.session_factory() as session:
            # Database operations
            article = self.article_crud.create(session, obj_in=article_data)
            session.commit()
            return {"article_id": article.id}
```

### After: Using database_operation context manager

```python
from local_newsifier.database import database_operation

class ArticleService:
    def process_article(self, url: str, content: str) -> Dict[str, Any]:
        """Process an article."""
        with self.session_factory() as session:
            with database_operation(session, "process article"):
                # Database operations
                article = self.article_crud.create(session, obj_in=article_data)
                session.commit()
                return {"article_id": article.id}
```

## Benefits

1. **More granular error context** - Each operation can have its own descriptive name
2. **Composable** - Can use multiple context managers in one method
3. **Explicit** - Clear where error handling is applied
4. **Testable** - Easier to mock and test error scenarios

## Common Patterns

### Single Operation

```python
# Before
@handle_database
def get_user(self, user_id: int):
    with self.session_factory() as session:
        return session.get(User, user_id)

# After
def get_user(self, user_id: int):
    with self.session_factory() as session:
        with database_operation(session, f"get user {user_id}"):
            return session.get(User, user_id)
```

### Multiple Operations

```python
# Before - entire method wrapped
@handle_database
def complex_operation(self):
    with self.session_factory() as session:
        user = session.get(User, user_id)
        article = session.get(Article, article_id)
        # If either fails, same generic error

# After - each operation can have specific handling
def complex_operation(self):
    with self.session_factory() as session:
        with database_operation(session, "fetch user"):
            user = session.get(User, user_id)

        with database_operation(session, "fetch article"):
            article = session.get(Article, article_id)
```

### Nested Operations

```python
def process_batch(self, items):
    with self.session_factory() as session:
        for item in items:
            with database_operation(session, f"process item {item.id}"):
                # Process individual item
                # Errors include specific item context
```

## Error Messages

The context manager provides better error messages:

- **Before**: "Database error in process_article"
- **After**: "Database constraint violation during create article from RSS"

## Migration Checklist

1. [ ] Remove `@handle_database` decorator
2. [ ] Import `database_operation` from `local_newsifier.database`
3. [ ] Wrap database operations with context manager
4. [ ] Provide descriptive operation names
5. [ ] Test error scenarios

## Advanced Usage

### Without Session

For validation or other operations that might fail:

```python
with database_operation(operation_name="validate input"):
    validate_user_input(data)
```

### Custom Error Handling

You can still catch specific errors:

```python
try:
    with database_operation(session, "create user"):
        user = create_user(data)
except ServiceError as e:
    if e.error_type == "integrity":
        # Handle duplicate user
        pass
    else:
        raise
```

# Database Error Handling

This guide explains how to use the streamlined error handling framework with database operations.

## Overview

The error handling framework has been extended to support database operations without requiring any additional modules or classes. Database-specific error types and messages have been added to the existing error handling system.

## Error Types

When using the database error handling, you get access to these database-specific error types:

| Type | Description | Transient | Exit Code |
|------|-------------|-----------|-----------|
| `connection` | Database connection issues | Yes | 10 |
| `integrity` | Constraint violations | No | 11 |
| `not_found` | Record not found | No | 8 |
| `multiple` | Multiple records found | No | 12 |
| `validation` | Invalid database request | No | 7 |
| `timeout` | Query timeout | Yes | 3 |
| `transaction` | Transaction errors | Yes | 13 |

## Using Database Error Handling

### CRUD Operations

Simply use the `handle_database` decorator on your database methods:

```python
from local_newsifier.errors import handle_database

class UserCRUD(CRUDBase[User]):
    """User CRUD operations with error handling."""
    
    @handle_database
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get a user by email with error handling."""
        return db.exec(select(self.model).where(self.model.email == email)).first()
    
    @handle_database
    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], User]) -> User:
        """Create a new user with error handling."""
        return super().create(db, obj_in=obj_in)
```

### Service Methods

Use the same decorator in your service methods:

```python
class UserService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    @handle_database
    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID with error handling."""
        with self.session_factory() as session:
            user = session.exec(select(User).where(User.id == user_id)).one()
            return user
```

### CLI Commands

For CLI commands that interact with the database:

```python
@click.command()
@handle_database_cli
def count_users():
    """Count users with CLI error handling."""
    with session_factory() as session:
        count = session.exec(select(func.count()).select_from(User)).one()
        click.echo(f"Total users: {count}")
```

## Error Messages

When database errors occur, users will see helpful error messages:

```
database.integrity: Unique constraint violation: duplicate key value violates unique constraint
Hint: Database constraint violation. The operation violates database rules.
```

```
database.not_found: Record not found in the database
Hint: Requested record not found in the database.
```

## Automatic Error Classification

The system automatically classifies SQLAlchemy and other database errors into appropriate error types:

1. **IntegrityError** → `integrity`
2. **NoResultFound** → `not_found`
3. **MultipleResultsFound** → `multiple`
4. **DisconnectionError** → `connection`
5. **TimeoutError** → `timeout`
6. **DataError/InvalidRequestError** → `validation`
7. **DatabaseError** → `transaction`

## Implementation Example

Here's a complete example of using database error handling in a CRUD class:

```python
from typing import Optional, List, Dict, Any, Union
from sqlmodel import Session, select
from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.user import User
from local_newsifier.errors import handle_database

class UserCRUD(CRUDBase[User]):
    """User CRUD operations with error handling."""
    
    @handle_database
    def get(self, db: Session, id: int) -> Optional[User]:
        """Get a user by ID with error handling."""
        return super().get(db, id)
    
    @handle_database
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get a user by email with error handling."""
        return db.exec(select(self.model).where(self.model.email == email)).first()
    
    @handle_database
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Get multiple users with error handling."""
        return super().get_multi(db, skip=skip, limit=limit)
    
    @handle_database
    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], User]) -> User:
        """Create a new user with error handling."""
        return super().create(db, obj_in=obj_in)
    
    @handle_database
    def update(self, db: Session, *, db_obj: User, obj_in: Union[Dict[str, Any], User]) -> User:
        """Update a user with error handling."""
        return super().update(db, db_obj=db_obj, obj_in=obj_in)
    
    @handle_database
    def remove(self, db: Session, *, id: int) -> Optional[User]:
        """Remove a user with error handling."""
        return super().remove(db, id=id)

# Create an instance
user_crud = UserCRUD(User)
```

## Handling Errors

When using these decorated methods, you can catch and handle `ServiceError`:

```python
from local_newsifier.errors import ServiceError

try:
    user = user_crud.get_by_email(db, email="nonexistent@example.com")
    if user is None:
        # Handle not found case
        pass
except ServiceError as e:
    if e.error_type == "integrity":
        # Handle integrity error
        print(f"Constraint violation: {e}")
    elif e.error_type == "connection":
        # Handle connection error
        print(f"Database connection error: {e}")
    else:
        # Handle other errors
        print(f"Database error: {e}")
```

## Benefits Over Traditional Approach

This approach is much more streamlined than traditional error handling:

### Traditional Approach (20+ lines per method)

```python
def get_by_email(self, db: Session, email: str) -> Optional[User]:
    try:
        return db.exec(select(User).where(User.email == email)).first()
    except SQLAlchemyError as e:
        if isinstance(e, IntegrityError):
            logger.error(f"Integrity error: {e}")
            raise ValueError(f"Database integrity error: {e}")
        elif isinstance(e, OperationalError):
            logger.error(f"Database operational error: {e}")
            raise RuntimeError(f"Database connection error: {e}")
        # ... many more error checks
        else:
            logger.error(f"Database error: {e}")
            raise RuntimeError(f"Unexpected database error: {e}")
```

### Streamlined Approach (2 lines)

```python
@handle_database
def get_by_email(self, db: Session, email: str) -> Optional[User]:
    return db.exec(select(User).where(User.email == email)).first()
```
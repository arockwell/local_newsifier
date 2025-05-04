# Database Error Handling

This guide explains how to use the streamlined error handling framework with database operations.

## Core Concepts

The database error handling system extends the general error handling framework with database-specific functionality:

1. **Database-Specific ServiceError**: Database exceptions are converted to `ServiceError` instances with `service="database"` and appropriate error types
2. **CRUD Integration**: Ready-to-use CRUD base class with error handling
3. **Automatic Classification**: Common SQLAlchemy and database errors are classified into meaningful error types

## Error Types

Common database error types:

| Type | Description | Transient | Example |
|------|-------------|-----------|---------|
| `connection` | Database connection issues | Yes | Connection refused, pool timeout |
| `timeout` | Query timeout | Yes | Statement timeout |
| `integrity` | Constraint violations | No | Unique constraint, foreign key constraint |
| `not_found` | Record not found | No | NoResultFound exception |
| `multiple` | Multiple records found | No | MultipleResultsFound exception |
| `validation` | Invalid request | No | Invalid column, data type error |
| `transaction` | Transaction errors | Sometimes | Deadlock, serialization failure |
| `unknown` | Unclassified errors | No | Unexpected database errors |

## Using Error Handling

### Method Decorator

```python
from local_newsifier.errors import handle_database

class UserService:
    @handle_database()
    def get_user_by_email(self, email: str) -> User:
        """Get user by email with error handling."""
        with self.session_factory() as session:
            result = session.exec(
                select(User).where(User.email == email)
            ).first()
            if not result:
                raise ValueError(f"User with email {email} not found")
            return result
```

### Error-Handled CRUD Base

```python
from local_newsifier.crud.error_handled import ErrorHandledCRUDBase
from local_newsifier.models import User

class UserCRUD(ErrorHandledCRUDBase[User]):
    """User CRUD operations with error handling."""
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get a user by email."""
        user = db.exec(
            select(self.model).where(self.model.email == email)
        ).first()
        return user

# Or use the helper function
from local_newsifier.crud.error_handled import create_error_handled_crud_model
from local_newsifier.models import User

user_crud = create_error_handled_crud_model(User)
```

### CLI Commands

```python
from local_newsifier.errors import handle_database_cli
import click

@click.command()
@handle_database_cli
def count_users():
    """Count users with CLI error handling."""
    with session_factory() as session:
        count = session.exec(select(func.count()).select_from(User)).one()
        click.echo(f"Total users: {count}")
```

## Error Examples

### Unique Constraint Violation

```
database.integrity: Unique constraint violation: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "users_email_key"
Hint: Database constraint violation. The operation violates database rules.
```

### Connection Error

```
database.connection: Database connection error: (psycopg2.OperationalError) could not connect to server: Connection refused
Hint: Could not connect to the database. Check database connection settings.
```

### Record Not Found

```
database.not_found: Record not found in the database
Hint: Requested record not found in the database.
```

## Benefits Over Traditional Approach

### Traditional Approach (Error Handling Scattered in Multiple Places)

```python
def get_user(self, id: int) -> User:
    try:
        user = self.session.exec(select(User).where(User.id == id)).one()
        return user
    except NoResultFound:
        logger.error(f"User {id} not found")
        raise ValueError(f"User {id} not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise RuntimeError(f"Failed to fetch user: {e}")
```

### Streamlined Approach (Consistent Pattern)

```python
@handle_database()
def get_user(self, id: int) -> User:
    return self.session.exec(select(User).where(User.id == id)).one()
```

## Implementation Details

1. **Error Classification**: SQLAlchemy exceptions are mapped to appropriate error types
2. **Retry Handling**: Transient errors like connection issues are automatically retried
3. **Context Collection**: Function info, arguments, query details are captured
4. **Error Normalization**: Different database errors are presented consistently
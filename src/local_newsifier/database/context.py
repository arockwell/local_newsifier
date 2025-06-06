"""Database operation context manager for unified error handling."""

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session

from local_newsifier.errors import ServiceError


@contextmanager
def database_operation(
    session: Optional[Session] = None, operation_name: str = "database operation"
) -> Generator[Optional[Session], None, None]:
    """Context manager for database operations with unified error handling.

    This replaces the need for @handle_database decorators and duplicate
    error handling code in services.

    Args:
        session: Optional existing session to use
        operation_name: Name of the operation for error messages

    Yields:
        The database session (if provided)

    Raises:
        ServiceError: With appropriate classification for database errors

    Example:
        ```python
        # With existing session
        with database_operation(session, "fetch user"):
            user = session.get(User, user_id)

        # Without session (for non-db operations that might fail)
        with database_operation(operation_name="validate input"):
            validate_user_input(data)
        ```
    """
    try:
        yield session
    except IntegrityError as e:
        # Handle constraint violations
        if "duplicate key" in str(e).lower():
            raise ServiceError(
                "database", "integrity", f"Duplicate key error during {operation_name}", original=e
            )
        elif "foreign key" in str(e).lower():
            raise ServiceError(
                "database",
                "integrity",
                f"Foreign key constraint error during {operation_name}",
                original=e,
            )
        else:
            raise ServiceError(
                "database",
                "integrity",
                f"Database constraint violation during {operation_name}",
                original=e,
            )
    except OperationalError as e:
        # Handle connection/operational errors
        if "connection" in str(e).lower():
            raise ServiceError(
                "database",
                "connection",
                f"Database connection error during {operation_name}",
                original=e,
            )
        elif "timeout" in str(e).lower():
            raise ServiceError(
                "database", "timeout", f"Database timeout during {operation_name}", original=e
            )
        else:
            raise ServiceError(
                "database",
                "operational",
                f"Database operational error during {operation_name}",
                original=e,
            )
    except Exception as e:
        # Handle any other database-related errors
        if "not found" in str(e).lower():
            raise ServiceError(
                "database", "not_found", f"Resource not found during {operation_name}", original=e
            )
        else:
            # Re-raise if it's already a ServiceError
            if isinstance(e, ServiceError):
                raise
            # Otherwise wrap it
            raise ServiceError(
                "database", "unknown", f"Unexpected error during {operation_name}", original=e
            )

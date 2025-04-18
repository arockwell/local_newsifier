"""Database engine and session management using SQLModel."""

from contextlib import contextmanager
from typing import Generator, Optional, Callable, TypeVar, Any

from sqlmodel import create_engine, Session, SQLModel

from local_newsifier.config.settings import get_settings

# Type variables for the with_session decorator
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


def get_engine(url: Optional[str] = None):
    """Get SQLModel engine.

    Args:
        url: Database URL (if None, uses settings)

    Returns:
        SQLModel engine
    """
    settings = get_settings()
    url = url or str(settings.DATABASE_URL)

    # Only add application_name for PostgreSQL
    connect_args = {}
    if url.startswith("postgresql:"):
        connect_args = {"application_name": "local_newsifier"}
        
    return create_engine(
        url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        connect_args=connect_args,
        echo=settings.DB_ECHO,
    )


def get_session() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        Database session
    """
    engine = get_engine()
    with Session(engine) as session:
        yield session


@contextmanager
def transaction(session: Session):
    """Transaction context manager.

    Args:
        session: Database session

    Yields:
        None

    Raises:
        Exception: Any exception that occurs during the transaction
    """
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise


def create_db_and_tables(engine=None):
    """Create all tables in the database.

    Args:
        engine: SQLModel engine (if None, creates one)
    """
    if engine is None:
        engine = get_engine()

    # Using SQLModel's metadata to create tables
    SQLModel.metadata.create_all(engine)


class SessionManager:
    """Session manager for database operations."""

    def __init__(self):
        """Initialize the session manager."""
        self.session = None

    def __enter__(self):
        """Enter the context manager.

        Returns:
            Session: Database session
        """
        engine = get_engine()
        self.session = Session(engine)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()


def with_session(func: F) -> F:
    """Add session management to database functions.

    This decorator ensures that a database session is available to the
    decorated function. If a session is provided as a keyword argument,
    it is used directly. Otherwise, a new session is created and managed
    for the duration of the function call.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    def wrapper(*args, session: Optional[Session] = None, **kwargs):
        """Execute function with session management.

        Args:
            session: SQLModel session
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the decorated function
        """
        if session is not None:
            return func(*args, session=session, **kwargs)

        with SessionManager() as new_session:
            return func(*args, session=new_session, **kwargs)

    return wrapper
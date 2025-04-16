"""Database engine and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.config.settings import get_settings
from local_newsifier.models.database.base import Base


def get_engine(url: str = None):
    """Get SQLAlchemy engine.

    Args:
        url: Database URL (if None, uses settings)

    Returns:
        SQLAlchemy engine
    """
    settings = get_settings()
    url = url or str(settings.DATABASE_URL)
    
    return create_engine(
        url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        # Connect args for handling disconnects
        connect_args={"application_name": "local_newsifier"},
    )


def create_session_factory(engine=None):
    """Create a session factory.

    Args:
        engine: SQLAlchemy engine (if None, creates one)

    Returns:
        Session factory
    """
    if engine is None:
        engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        Database session
    """
    SessionLocal = create_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


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
        engine: SQLAlchemy engine (if None, creates one)
    """
    if engine is None:
        engine = get_engine()
    
    Base.metadata.create_all(engine)
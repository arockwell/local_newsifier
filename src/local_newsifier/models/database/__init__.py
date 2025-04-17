"""Database models package - pure SQLModel implementation."""

from typing import Any, Callable, Generator, Protocol
from contextlib import contextmanager

from sqlmodel import SQLModel, create_engine, Session

from local_newsifier.models.database.base import TableBase
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult

# Define a Protocol for engine to avoid SQLAlchemy imports
class EngineProtocol(Protocol):
    """Protocol for database engine."""
    def connect(self) -> Any: ...
    def dispose(self) -> None: ...

# Re-export all models
__all__ = [
    "SQLModel",
    "TableBase",
    "Article",
    "Entity",
    "AnalysisResult",
    "create_db_and_tables",
    "get_engine",
    "get_session",
    "get_session_context",
    "init_db"
]

def get_engine(db_url: str) -> EngineProtocol:
    """Get a database engine.
    
    Args:
        db_url: Database URL
        
    Returns:
        SQLModel engine instance
    """
    return create_engine(
        db_url,
        echo=False,
        connect_args={"application_name": "local_newsifier"}
    )

def create_db_and_tables(db_url: str) -> EngineProtocol:
    """Initialize the database engine and create tables.
    
    Args:
        db_url: Database URL
        
    Returns:
        SQLModel engine instance
    """
    engine = get_engine(db_url)
    SQLModel.metadata.create_all(engine)
    return engine

def get_session(engine: EngineProtocol) -> Callable[[], Session]:
    """Get a session factory function.
    
    Args:
        engine: SQLModel engine instance
        
    Returns:
        Function that creates a new session
    """
    def create_session() -> Session:
        return Session(engine)
    
    return create_session

@contextmanager
def get_session_context(engine: EngineProtocol) -> Generator[Session, None, None]:
    """Create a session context that handles commits and rollbacks.
    
    Args:
        engine: SQLModel engine instance
        
    Yields:
        Database session
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(db_url: str) -> EngineProtocol:
    """Initialize the database and create tables.
    
    This is an alias for create_db_and_tables for compatibility.
    
    Args:
        db_url: Database URL
        
    Returns:
        SQLModel engine instance
    """
    return create_db_and_tables(db_url)
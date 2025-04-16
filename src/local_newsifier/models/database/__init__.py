"""Database models package."""

from sqlmodel import SQLModel, create_engine, Session, sessionmaker
from typing import Protocol, Any, Generator

from local_newsifier.models.database.base import TableBase, SchemaBase
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
    "SchemaBase", 
    "Article",
    "Entity",
    "AnalysisResult",
    "init_db",
    "get_session",
    "EngineProtocol"
]

def init_db(db_url: str) -> EngineProtocol:
    """Initialize the database engine.
    
    Args:
        db_url: Database URL
        
    Returns:
        SQLModel engine instance
    """
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)
    return engine

def get_session(engine: EngineProtocol) -> sessionmaker:
    """Get a session factory for the database.
    
    Args:
        engine: SQLModel engine instance
        
    Returns:
        Session factory
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
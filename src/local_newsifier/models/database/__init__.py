"""Database models package."""

from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine, Session

from local_newsifier.models.database.base import TableBase, SchemaBase
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult

# Re-export all models
__all__ = [
    "SQLModel",
    "TableBase",
    "SchemaBase", 
    "Article",
    "Entity",
    "AnalysisResult",
    "init_db",
    "get_session"
]

def init_db(db_url: str) -> Engine:
    """Initialize the database engine.
    
    Args:
        db_url: Database URL
        
    Returns:
        SQLAlchemy engine instance
    """
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)
    return engine

def get_session(engine: Engine) -> sessionmaker:
    """Get a session factory for the database.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        Session factory
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
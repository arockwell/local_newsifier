"""Database models package."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database.base import Base, SQLModel
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResultDB

# Re-export all models
__all__ = [
    "Base",
    "SQLModel",
    "Article",
    "Entity",
    "AnalysisResultDB",  # To be converted to SQLModel in next phase
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
    Base.metadata.create_all(engine)
    return engine

def get_session(engine: Engine) -> sessionmaker:
    """Get a session factory for the database.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        Session factory
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""Database models package."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database.base import Base
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.database.analysis_result import AnalysisResultDB

# Import Pydantic models from a separate file to avoid circular imports
from local_newsifier.models.database.pydantic_models import (
    Article, ArticleCreate, ArticleBase,
    Entity, EntityCreate, EntityBase,
    AnalysisResult, AnalysisResultCreate, AnalysisResultBase
)

# Re-export all models
__all__ = [
    "Base",
    "ArticleDB", "Article", "ArticleCreate", "ArticleBase",
    "EntityDB", "Entity", "EntityCreate", "EntityBase",
    "AnalysisResultDB", "AnalysisResult", "AnalysisResultCreate", "AnalysisResultBase"
]

def init_db(db_url: str) -> Engine:
    """Initialize the database and create tables.

    Args:
        db_url: Database connection URL

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
    return sessionmaker(bind=engine)
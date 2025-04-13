"""Database models package."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database.base import BaseModel as Base
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity


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
    """Create a session factory for database operations.

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        SQLAlchemy session factory
    """
    return sessionmaker(bind=engine)


__all__ = ["Base", "Article", "Entity", "init_db", "get_session"]
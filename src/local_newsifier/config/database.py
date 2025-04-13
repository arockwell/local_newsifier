"""Database connection management."""

from typing import Any
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database import Base, init_db
from local_newsifier.config.settings import get_settings


def get_database() -> Any:
    """Get a database engine instance.
    
    Returns:
        SQLAlchemy engine instance
    """
    settings = get_settings()
    return init_db(settings.get_database_url())


def get_db_session() -> sessionmaker:
    """Get a database session factory.
    
    Returns:
        SQLAlchemy session factory
    """
    engine = get_database()
    return sessionmaker(bind=engine)
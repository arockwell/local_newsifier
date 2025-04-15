"""Database initialization utilities."""

from sqlmodel import SQLModel, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


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
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
#!/usr/bin/env python3
"""Script to initialize the database and create all necessary tables."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.local_newsifier.config.database import DatabaseSettings
from src.local_newsifier.models.database import Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def init_db():
    """Initialize the database."""
    settings = DatabaseSettings()
    engine = create_engine(str(settings.DATABASE_URL))
    
    # Drop all tables in the correct order
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return session


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!") 
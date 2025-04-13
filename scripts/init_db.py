#!/usr/bin/env python3
"""Script to initialize the database and create all necessary tables."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.local_newsifier.config.database import get_database
from src.local_newsifier.models.database import Base
from sqlalchemy import text

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database and create all tables."""
    try:
        # Get database engine
        engine = get_database()
        
        # Drop all existing tables with CASCADE
        logger.info("Dropping existing tables...")
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
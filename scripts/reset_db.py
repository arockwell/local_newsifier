#!/usr/bin/env python3
"""Script to completely drop and recreate the database."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from local_newsifier.config.settings import settings
from sqlmodel import SQLModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def confirm(message):
    """Ask user for confirmation."""
    response = input(f"{message} (yes/no): ")
    return response.lower() in ("yes", "y")


def reset_db():
    """Drop and recreate the database."""
    db_url = settings.DATABASE_URL
    
    # Show database info and ask for confirmation
    logger.info(f"Database: {db_url}")
    if not confirm("⚠️ WARNING: This will DELETE ALL DATA in the database. Are you sure?"):
        logger.info("Operation cancelled.")
        return
    
    if not confirm("⚠️ DOUBLE CHECK: All existing data will be PERMANENTLY LOST! Type 'yes' to confirm"):
        logger.info("Operation cancelled.")
        return
    
    # Create engine
    logger.info("Connecting to database...")
    engine = create_engine(str(db_url))
    
    try:
        # Drop all tables in the correct order by dropping the entire schema
        logger.info("Dropping all tables and schema...")
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
        
        # Create all tables
        logger.info("Creating all tables...")
        SQLModel.metadata.create_all(engine)
        
        logger.info("Applying Alembic migrations...")
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        # Create session
        Session = sessionmaker(bind=engine)
        with Session() as session:
            # Add essential data like RSS feeds - use direct SQL to avoid import issues
            logger.info("Adding initial RSS feeds...")
            feeds = [
                (
                    "http://cbsnews.com/latest/rss/us",
                    "CBS News - U.S.",
                    "U.S. news headlines from CBS News",
                    True
                ),
                (
                    "https://www.cbsnews.com/latest/rss/politics",
                    "CBS News - Politics",
                    "Politics news headlines from CBS News",
                    True
                ),
                (
                    "https://www.cbsnews.com/latest/rss/technology",
                    "CBS News - Technology",
                    "Technology news headlines from CBS News",
                    True
                ),
            ]
            
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            
            for url, name, description, is_active in feeds:
                stmt = text("""
                    INSERT INTO rss_feeds (url, name, description, is_active, created_at, updated_at)
                    VALUES (:url, :name, :description, :is_active, :created_at, :updated_at)
                """)
                session.execute(stmt, {
                    "url": url,
                    "name": name,
                    "description": description,
                    "is_active": is_active,
                    "created_at": now,
                    "updated_at": now
                })
            
            session.commit()
            logger.info(f"Added {len(feeds)} initial RSS feeds.")
        
        logger.info("Database reset and initialized successfully!")
        
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        raise


if __name__ == "__main__":
    reset_db()

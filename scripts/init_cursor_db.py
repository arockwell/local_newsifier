"""Script to initialize a new database for a cursor instance."""

import logging
import os
import psycopg2
from pathlib import Path
from local_newsifier.config.settings import get_cursor_db_name
from local_newsifier.config.database import DatabaseSettings
from local_newsifier.models.base import Base
from sqlalchemy import create_engine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def init_cursor_db():
    """Initialize a new database for this cursor instance."""
    settings = DatabaseSettings()
    db_name = settings.POSTGRES_DB
    cursor_id = db_name.replace("local_newsifier_", "")
    
    # Save cursor ID to file
    env_file = Path(".env.cursor")
    env_file.write_text(f"export CURSOR_DB_ID={cursor_id}\n")
    logger.info(f"Saved cursor ID to {env_file}")
    
    # Connect to default postgres database to create new db
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=int(settings.POSTGRES_PORT),
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database="postgres"
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Drop database if it exists
            cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
            logger.info(f"Dropped database {db_name} if it existed")
            
            # Create new database
            cur.execute(f"CREATE DATABASE {db_name}")
            logger.info(f"Created new database {db_name}")
            
    finally:
        conn.close()
    
    # Create tables in the new database
    engine = create_engine(str(settings.DATABASE_URL))
    Base.metadata.create_all(engine)
    logger.info(f"Created all tables in database {db_name}")
    
    logger.info(f"To use this database in new shells, run: source {env_file}")
    return db_name

if __name__ == "__main__":
    db_name = init_cursor_db()
    logger.info(f"Successfully initialized database {db_name}")

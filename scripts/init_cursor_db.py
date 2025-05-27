"""Script to initialize a new database for a cursor instance.

This script:
1. Generates or uses an existing cursor ID stored in CURSOR_DB_ID env var
2. Creates a new database specific to this cursor instance
3. Sets up all required tables using SQLModel's metadata
4. Saves the cursor ID to .env.cursor for future sessions

Usage:
    poetry run python scripts/init_cursor_db.py
"""

import logging
import os  # noqa: F401
import sys
from pathlib import Path

import psycopg2
from sqlalchemy import create_engine

from local_newsifier.config.database import DatabaseSettings
from local_newsifier.models.base import TableBase as Base

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_cursor_db():
    """Initialize a new database for this cursor instance."""
    try:
        settings = DatabaseSettings()
        db_name = settings.POSTGRES_DB
        cursor_id = db_name.replace("local_newsifier_", "")

        # Save cursor ID to file
        env_file = Path(".env.cursor")
        env_file.write_text(f"export CURSOR_DB_ID={cursor_id}\n")
        logger.info(f"Saved cursor ID to {env_file}")

        # Connect to default postgres database to create new db
        try:
            conn = psycopg2.connect(
                host=settings.POSTGRES_HOST,
                port=int(settings.POSTGRES_PORT),
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database="postgres",
            )
            conn.autocommit = True
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            logger.error(
                "Make sure PostgreSQL is running and accessible with the " "configured credentials"
            )
            sys.exit(1)

        try:
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                db_exists = cur.fetchone() is not None

                if db_exists:
                    logger.info(f"Database {db_name} already exists, skipping creation")
                else:
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
        logger.info(
            "To check your database status: "
            "poetry run python -m src.local_newsifier.cli.main db stats"
        )
        return db_name

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.error("See docs/db_initialization.md for troubleshooting steps")
        sys.exit(1)


if __name__ == "__main__":
    print("Initializing database for Local Newsifier...")
    db_name = init_cursor_db()
    print("\n✅ Success! Database initialized and ready to use.")
    print(f"Database name: {db_name}")
    print("\nTo use this database in new shells, run:")
    print("  source .env.cursor")
    print("\nTo verify your database is working:")
    print("  poetry run python -m src.local_newsifier.cli.main db stats")

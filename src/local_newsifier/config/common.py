"""Common configuration constants and utilities.

This module contains shared configuration constants and utilities that are used
across multiple modules in the config package. Extracting these shared elements
helps prevent circular import dependencies.
"""

import os
import uuid
from pathlib import Path


def get_cursor_db_name() -> str:
    """Get a cursor-specific database name.

    Returns:
        Database name with cursor ID
    """
    cursor_id = os.environ.get("CURSOR_DB_ID")
    if not cursor_id:
        cursor_id = str(uuid.uuid4())[:8]
        os.environ["CURSOR_DB_ID"] = cursor_id
    return f"local_newsifier_{cursor_id}"


# Common database configuration defaults
DEFAULT_POSTGRES_USER = "postgres"
DEFAULT_POSTGRES_PASSWORD = "postgres"
DEFAULT_POSTGRES_HOST = "localhost"
DEFAULT_POSTGRES_PORT = "5432"
DEFAULT_DB_POOL_SIZE = 5
DEFAULT_DB_MAX_OVERFLOW = 10
DEFAULT_DB_ECHO = False

# Common directory settings
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_CACHE_DIR = Path("cache")
DEFAULT_TEMP_DIR = Path("temp")

# Common logging settings
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_database_url(user, password, host, port, db_name):
    """Construct a database URL from components.

    Args:
        user: PostgreSQL username
        password: PostgreSQL password
        host: PostgreSQL host
        port: PostgreSQL port
        db_name: PostgreSQL database name

    Returns:
        Formatted database URL string
    """
    return f"postgresql://{user}:{password}@" f"{host}:{port}/{db_name}"

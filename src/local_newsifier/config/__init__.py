"""Configuration package for the Local Newsifier application."""

# Import common module first as it has no dependencies
from local_newsifier.config.common import (DEFAULT_CACHE_DIR, DEFAULT_DB_ECHO,
                                           DEFAULT_DB_MAX_OVERFLOW, DEFAULT_DB_POOL_SIZE,
                                           DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL,
                                           DEFAULT_OUTPUT_DIR, DEFAULT_POSTGRES_HOST,
                                           DEFAULT_POSTGRES_PASSWORD, DEFAULT_POSTGRES_PORT,
                                           DEFAULT_POSTGRES_USER, DEFAULT_TEMP_DIR,
                                           get_cursor_db_name, get_database_url)
# Import database last as it depends on both common and settings
from local_newsifier.config.database import (DatabaseSettings, get_database, get_database_settings,
                                             get_database_url_from_components, get_db_session)
# Import settings next as it depends only on common
from local_newsifier.config.settings import Settings, get_settings

__all__ = [
    # Common module exports
    "get_cursor_db_name",
    "get_database_url",
    "DEFAULT_POSTGRES_USER",
    "DEFAULT_POSTGRES_PASSWORD",
    "DEFAULT_POSTGRES_HOST",
    "DEFAULT_POSTGRES_PORT",
    "DEFAULT_DB_POOL_SIZE",
    "DEFAULT_DB_MAX_OVERFLOW",
    "DEFAULT_DB_ECHO",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_CACHE_DIR",
    "DEFAULT_TEMP_DIR",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_LOG_FORMAT",
    # Settings module exports
    "Settings",
    "get_settings",
    # Database module exports
    "DatabaseSettings",
    "get_database",
    "get_database_settings",
    "get_db_session",
    "get_database_url_from_components",
]

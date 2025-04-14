"""Configuration package for local_newsifier.

This package contains all configuration-related code including:
- Application settings
- Database configuration
"""

from local_newsifier.config.settings import Settings, get_settings, get_cursor_db_name, settings

# Import after settings to avoid circular imports
from local_newsifier.config.database import (
    DatabaseSettings,
    get_database,
    get_database_settings,
    get_db_session,
)

__all__ = [
    "DatabaseSettings",
    "Settings",
    "get_cursor_db_name",
    "get_database",
    "get_database_settings",
    "get_db_session",
    "get_settings",
    "settings",
]

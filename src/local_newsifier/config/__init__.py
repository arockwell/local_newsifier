"""Configuration package for local_newsifier.

This package contains all configuration-related code including:
- Application settings
- Database configuration
"""

from local_newsifier.config.settings import settings
from local_newsifier.config.database import get_database_settings, get_db_session

__all__ = ['settings', 'get_database_settings', 'get_db_session'] 
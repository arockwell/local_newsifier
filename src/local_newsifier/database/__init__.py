"""Database package for the Local Newsifier application.

This package provides database access functions, classes, and utilities.
It promotes direct usage of CRUD operations for database access.
"""

# Import directly from engine.py
from local_newsifier.database.engine import (
    create_db_and_tables,
    get_engine,
    get_session,
    transaction,
    SessionManager,
    with_session,
)
from local_newsifier.database.async_engine import AsyncDatabase, get_async_database

__all__ = [
    # Database engine and session management
    "create_db_and_tables",
    "get_engine",
    "get_session",
    "transaction",
    "SessionManager",
    "with_session",
    "AsyncDatabase",
    "get_async_database",
]

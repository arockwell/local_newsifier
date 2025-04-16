"""Database package for the Local Newsifier application.

This package provides database access functions, classes, and utilities.
It promotes direct usage of CRUD operations for database access.
"""

# Import directly from engine.py since adapter.py is being deprecated
from local_newsifier.database.engine import (create_db_and_tables,
                                             create_session_factory,
                                             get_engine, get_session,
                                             transaction, SessionManager,
                                             with_session)

__all__ = [
    # Database engine and session management
    "create_db_and_tables",
    "create_session_factory",
    "get_engine",
    "get_session",
    "transaction",
    "SessionManager",
    "with_session",
]

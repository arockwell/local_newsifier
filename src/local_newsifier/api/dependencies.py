"""Dependency injection for the FastAPI application."""

from typing import Generator

from fastapi import Depends
from sqlmodel import Session

from local_newsifier.database.engine import SessionManager


def get_session() -> Generator[Session, None, None]:
    """Get a database session.

    This dependency provides a database session to route handlers.
    The session is automatically closed when the request is complete.

    Yields:
        Session: SQLModel session
    """
    with SessionManager() as session:
        yield session

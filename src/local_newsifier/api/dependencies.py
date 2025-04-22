"""Dependency injection for the FastAPI application."""

from typing import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from local_newsifier.database.engine import SessionManager


def require_admin(request: Request):
    """Verify admin session for protected routes.

    Args:
        request: FastAPI request

    Returns:
        True if authenticated, otherwise raises an exception

    Raises:
        HTTPException: If not authenticated, redirects to login page
    """
    if not request.session.get("authenticated"):
        # Store the requested URL to redirect back after login
        next_url = request.url.path
        login_url = f"/login?next={next_url}"
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": login_url},
        )
    return True


def get_session() -> Generator[Session, None, None]:
    """Get a database session.

    This dependency provides a database session to route handlers.
    The session is automatically closed when the request is complete.

    Yields:
        Session: SQLModel session
    """
    with SessionManager() as session:
        yield session

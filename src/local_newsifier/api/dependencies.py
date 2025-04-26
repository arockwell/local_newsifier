"""Dependency injection for the FastAPI application."""

import os
import pathlib
from typing import Generator

from fastapi import HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from local_newsifier.database.engine import SessionManager

# Get the templates directory path - works both in development and production
# This handles different environments: local development vs Railway deployment
if os.path.exists("src/local_newsifier/api/templates"):
    templates_dir = "src/local_newsifier/api/templates"  # Local development
else:
    templates_dir = str(pathlib.Path(__file__).parent / "templates")  # Production

templates = Jinja2Templates(directory=templates_dir)


def get_templates() -> Jinja2Templates:
    """Get the Jinja2 templates.
    
    Returns:
        Jinja2Templates: The templates object for HTML rendering
    """
    return templates


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

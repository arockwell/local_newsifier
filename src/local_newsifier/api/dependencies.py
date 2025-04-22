"""Dependency injection for the FastAPI application."""

import os
import pathlib
from typing import Generator

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from local_newsifier.database.engine import SessionManager

# Get the templates directory path - works both in development and production
if os.path.exists("src/local_newsifier/api/templates"):
    # Development environment
    templates_dir = "src/local_newsifier/api/templates"
else:
    # Production environment - use package-relative path
    templates_dir = str(pathlib.Path(__file__).parent / "templates")

templates = Jinja2Templates(directory=templates_dir)

def get_templates() -> Jinja2Templates:
    """Get the Jinja2 templates.
    
    This dependency provides access to the Jinja2 templates for rendering HTML responses.
    
    Returns:
        Jinja2Templates: The templates object
    """
    return templates

def get_session() -> Generator[Session, None, None]:
    """Get a database session.

    This dependency provides a database session to route handlers.
    The session is automatically closed when the request is complete.

    Yields:
        Session: SQLModel session
    """
    with SessionManager() as session:
        yield session

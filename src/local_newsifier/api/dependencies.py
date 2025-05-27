"""Dependency injection for the FastAPI application."""

import os
import pathlib
from typing import Generator

from fastapi import HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

# No direct container import as we're using injectable providers
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.rss_feed_service import RSSFeedService

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
    from local_newsifier.di.providers import get_session as get_injectable_session

    # Use injectable provider directly
    yield from get_injectable_session()


def get_article_service() -> ArticleService:
    """Get the article service.

    Returns:
        ArticleService: The article service instance
    """
    from local_newsifier.database.engine import get_session
    from local_newsifier.di.providers import get_article_service as get_injectable_article_service

    # Use injectable provider with session
    with next(get_session()) as session:
        return get_injectable_article_service(session=session)


def get_rss_feed_service() -> RSSFeedService:
    """Get the RSS feed service using the injectable pattern.

    Returns:
        RSSFeedService: The RSS feed service instance
    """
    from local_newsifier.database.engine import get_session
    from local_newsifier.di.providers import get_rss_feed_service as get_injectable_rss_feed_service

    # Use injectable provider with session
    with next(get_session()) as session:
        return get_injectable_rss_feed_service(session=session)

"""Dependency injection for the FastAPI application."""

import os
import pathlib
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, Request, status
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
    """Get a database session using FastAPI's native DI.

    This dependency provides a database session to route handlers.
    The session is automatically closed when the request is complete.

    Yields:
        Session: SQLModel session

    Raises:
        HTTPException: If database is unavailable
    """
    from local_newsifier.database.engine import get_engine

    engine = get_engine()
    if engine is None:
        raise HTTPException(status_code=500, detail="Database unavailable")

    session = Session(engine)
    try:
        yield session
        # Only commit if we're still in a transaction
        if session.in_transaction():
            session.commit()
    except Exception:
        # Rollback on any exception, but check if we're in a transaction first
        if session.in_transaction():
            session.rollback()
        raise
    finally:
        # Always close the session
        session.close()


def get_article_crud():
    """Get the article CRUD singleton."""
    from local_newsifier.crud.article import article

    return article


def get_analysis_result_crud():
    """Get the analysis result CRUD singleton."""
    from local_newsifier.crud.analysis_result import analysis_result

    return analysis_result


def get_entity_crud():
    """Get the entity CRUD singleton."""
    from local_newsifier.crud.entity import entity

    return entity


def get_canonical_entity_crud():
    """Get the canonical entity CRUD singleton."""
    from local_newsifier.crud.canonical_entity import canonical_entity

    return canonical_entity


def get_entity_mention_context_crud():
    """Get the entity mention context CRUD singleton."""
    from local_newsifier.crud.entity_mention_context import entity_mention_context

    return entity_mention_context


def get_entity_profile_crud():
    """Get the entity profile CRUD singleton."""
    from local_newsifier.crud.entity_profile import entity_profile

    return entity_profile


def get_rss_feed_crud():
    """Get the RSS feed CRUD singleton."""
    from local_newsifier.crud.rss_feed import rss_feed

    return rss_feed


def get_feed_processing_log_crud():
    """Get the feed processing log CRUD singleton."""
    from local_newsifier.crud.feed_processing_log import feed_processing_log

    return feed_processing_log


def get_nlp_model():
    """Provide the spaCy NLP model."""
    try:
        import spacy

        return spacy.load("en_core_web_lg")
    except (ImportError, OSError) as e:
        import logging

        logging.warning(f"Failed to load NLP model: {str(e)}")
        return None


def get_entity_extractor():
    """Provide the entity extractor tool."""
    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor

    return EntityExtractor()


def get_entity_resolver():
    """Provide the entity resolver tool."""
    from local_newsifier.tools.resolution.entity_resolver import EntityResolver

    return EntityResolver(similarity_threshold=0.85)


def get_context_analyzer():
    """Provide the context analyzer tool."""
    from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer

    return ContextAnalyzer(nlp_model=get_nlp_model())


def get_entity_service(
    session: Annotated[Session, Depends(get_session)],
    entity_crud=Depends(get_entity_crud),
    canonical_entity_crud=Depends(get_canonical_entity_crud),
    entity_mention_context_crud=Depends(get_entity_mention_context_crud),
    entity_profile_crud=Depends(get_entity_profile_crud),
    article_crud=Depends(get_article_crud),
    entity_extractor=Depends(get_entity_extractor),
    context_analyzer=Depends(get_context_analyzer),
    entity_resolver=Depends(get_entity_resolver),
):
    """Provide the entity service using FastAPI's native DI."""
    from local_newsifier.services.entity_service import EntityService

    return EntityService(
        entity_crud=entity_crud,
        canonical_entity_crud=canonical_entity_crud,
        entity_mention_context_crud=entity_mention_context_crud,
        entity_profile_crud=entity_profile_crud,
        article_crud=article_crud,
        entity_extractor=entity_extractor,
        context_analyzer=context_analyzer,
        entity_resolver=entity_resolver,
        session_factory=lambda: session,
    )


def get_article_service(
    session: Annotated[Session, Depends(get_session)],
    article_crud=Depends(get_article_crud),
    analysis_result_crud=Depends(get_analysis_result_crud),
    entity_service=Depends(get_entity_service),
) -> ArticleService:
    """Get the article service using FastAPI's native DI.

    Returns:
        ArticleService: The article service instance
    """
    return ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        entity_service=entity_service,
        session_factory=lambda: session,
    )


def get_rss_feed_service(
    session: Annotated[Session, Depends(get_session)],
    rss_feed_crud=Depends(get_rss_feed_crud),
    feed_processing_log_crud=Depends(get_feed_processing_log_crud),
    article_service=Depends(get_article_service),
) -> RSSFeedService:
    """Get the RSS feed service using FastAPI's native DI.

    Returns:
        RSSFeedService: The RSS feed service instance
    """
    return RSSFeedService(
        rss_feed_crud=rss_feed_crud,
        feed_processing_log_crud=feed_processing_log_crud,
        article_service=article_service,
        session_factory=lambda: session,
    )


def get_apify_webhook_service(session: Annotated[Session, Depends(get_session)]):
    """Get the Apify webhook service using FastAPI's native DI.

    Returns:
        ApifyWebhookService: The webhook service instance
    """
    from local_newsifier.config.settings import settings
    from local_newsifier.services.apify_webhook_service import ApifyWebhookService

    return ApifyWebhookService(session=session, webhook_secret=settings.APIFY_WEBHOOK_SECRET)

"""
Provider functions for fastapi-injectable.

This module contains provider functions for all core dependencies
that can be used with fastapi-injectable. These providers gradually
replace the DIContainer factories with injectable providers.

Dependency injection approach:
- We use use_cache=False for all injectable components for simplicity and safety
- This ensures every dependency injection gets a new instance
- Prevents any issues with state leakage between operations
- Particularly important for services, database interactions, and in non-HTTP contexts
"""

import logging
from typing import Annotated, Any, Generator, Optional

from fastapi import Depends
from fastapi_injectable import injectable

# Using injectable directly - no scope parameter in version 0.7.0
# We'll control instance reuse with use_cache=True/False
from sqlmodel import Session

logger = logging.getLogger(__name__)

# Database providers

@injectable(use_cache=False)
def get_session() -> Generator[Session, None, None]:
    """Provide a database session.
    
    Returns a session from the session factory and ensures
    it's properly closed when done.
    
    Yields:
        Database session
    """
    from local_newsifier.database.engine import get_session as get_db_session
    
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()


# CRUD providers

@injectable(use_cache=False)
def get_article_crud():
    """Provide the article CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        ArticleCRUD instance
    """
    from local_newsifier.crud.article import article
    return article


@injectable(use_cache=False)
def get_entity_crud():
    """Provide the entity CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        EntityCRUD instance
    """
    from local_newsifier.crud.entity import entity
    return entity


@injectable(use_cache=False)
def get_entity_relationship_crud():
    """Provide the entity relationship CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        EntityRelationshipCRUD instance
    """
    from local_newsifier.crud.entity_relationship import entity_relationship
    return entity_relationship


@injectable(use_cache=False)
def get_rss_feed_crud():
    """Provide the RSS feed CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        RSSFeedCRUD instance
    """
    from local_newsifier.crud.rss_feed import rss_feed
    return rss_feed


# Tool providers

@injectable(use_cache=False)
def get_web_scraper_tool():
    """Provide the web scraper tool.
    
    Uses TRANSIENT scope as this tool may maintain state between operations.
    
    Returns:
        WebScraperTool instance
    """
    from local_newsifier.tools.web_scraper import WebScraperTool
    return WebScraperTool()


@injectable(use_cache=False)
def get_entity_extractor():
    """Provide the entity extractor tool.
    
    Uses use_cache=False to create new instances for each injection, as NLP 
    tools may have stateful caches or models.
    
    Returns:
        EntityExtractor instance
    """
    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
    return EntityExtractor()


@injectable(use_cache=False)
def get_entity_resolver():
    """Provide the entity resolver tool.
    
    Uses use_cache=False to create new instances for each injection, as this tool
    may have state during the resolution process.
    
    Returns:
        EntityResolver instance
    """
    from local_newsifier.tools.resolution.entity_resolver import EntityResolver
    return EntityResolver()


@injectable(use_cache=False)
def get_rss_parser():
    """Provide the RSS parser tool.
    
    Uses use_cache=False to create new instances for each injection, as parsers
    may maintain state during processing.
    
    Returns:
        RSSParser instance
    """
    from local_newsifier.tools.rss_parser import RSSParser
    return RSSParser()


# Service providers

@injectable(use_cache=False)
def get_article_service(
    article_crud: Annotated[Any, Depends(get_article_crud)],
    entity_crud: Annotated[Any, Depends(get_entity_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the article service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        article_crud: Article CRUD component
        entity_crud: Entity CRUD component
        session: Database session
        
    Returns:
        ArticleService instance
    """
    from local_newsifier.services.article_service import ArticleService
    
    return ArticleService(
        article_crud=article_crud,
        entity_crud=entity_crud,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_entity_service(
    entity_crud: Annotated[Any, Depends(get_entity_crud)],
    entity_relationship_crud: Annotated[Any, Depends(get_entity_relationship_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the entity service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        entity_crud: Entity CRUD component
        entity_relationship_crud: Entity relationship CRUD component
        session: Database session
        
    Returns:
        EntityService instance
    """
    from local_newsifier.services.entity_service import EntityService
    
    return EntityService(
        entity_crud=entity_crud,
        entity_relationship_crud=entity_relationship_crud,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_rss_feed_service(
    rss_feed_crud: Annotated[Any, Depends(get_rss_feed_crud)],
    rss_parser: Annotated[Any, Depends(get_rss_parser)],
    article_service: Annotated[Any, Depends(get_article_service)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the RSS feed service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        rss_feed_crud: RSS feed CRUD component
        rss_parser: RSS parser tool
        article_service: Article service
        session: Database session
        
    Returns:
        RSSFeedService instance
    """
    from local_newsifier.services.rss_feed_service import RSSFeedService
    
    return RSSFeedService(
        rss_feed_crud=rss_feed_crud,
        rss_parser=rss_parser,
        article_service=article_service,
        session_factory=lambda: session
    )
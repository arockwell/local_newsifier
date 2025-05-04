"""
Provider functions for fastapi-injectable.

This module contains provider functions for all core dependencies
that can be used with fastapi-injectable. These providers gradually
replace the DIContainer factories with injectable providers.

Dependency injection approach:
- use_cache=False: Used for components that interact with databases or maintain state
  (services, CRUD operations, tools, parsers, etc.)
- use_cache=True (default): Could be used for purely functional utilities with no state
  that just transform inputs to outputs in a deterministic way

Most of our components use use_cache=False for safety, since they either directly 
interact with the database or maintain state between operations.
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
    from local_newsifier.database.session_utils import get_db_session
    
    with get_db_session() as session:
        yield session
    # No need to explicitly close the session as the context manager handles it


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


@injectable(use_cache=False)
def get_analysis_result_crud():
    """Provide the analysis result CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        AnalysisResultCRUD instance
    """
    from local_newsifier.crud.analysis_result import analysis_result
    return analysis_result


@injectable(use_cache=False)
def get_canonical_entity_crud():
    """Provide the canonical entity CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        CanonicalEntityCRUD instance
    """
    from local_newsifier.crud.canonical_entity import canonical_entity
    return canonical_entity


@injectable(use_cache=False)
def get_entity_mention_context_crud():
    """Provide the entity mention context CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        EntityMentionContextCRUD instance
    """
    from local_newsifier.crud.entity_mention_context import entity_mention_context
    return entity_mention_context


@injectable(use_cache=False)
def get_entity_profile_crud():
    """Provide the entity profile CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        EntityProfileCRUD instance
    """
    from local_newsifier.crud.entity_profile import entity_profile
    return entity_profile


@injectable(use_cache=False)
def get_feed_processing_log_crud():
    """Provide the feed processing log CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        FeedProcessingLogCRUD instance
    """
    from local_newsifier.crud.feed_processing_log import feed_processing_log
    return feed_processing_log


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
def get_sentiment_analyzer_tool():
    """Provide the sentiment analyzer tool.
    
    Uses use_cache=False to create new instances for each injection, as sentiment
    analysis tools may maintain state during processing and interact with NLP models.
    
    Returns:
        SentimentAnalysisTool instance
    """
    from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
    return SentimentAnalysisTool()


@injectable(use_cache=False)
def get_sentiment_tracker_tool():
    """Provide the sentiment tracker tool.
    
    Uses use_cache=False to create new instances for each injection, as it 
    interacts with database and maintains state during tracking.
    
    Returns:
        SentimentTracker instance
    """
    from local_newsifier.tools.sentiment_tracker import SentimentTracker
    return SentimentTracker()


@injectable(use_cache=False)
def get_trend_analyzer_tool():
    """Provide the trend analyzer tool.
    
    Uses use_cache=False to create new instances for each injection, as it 
    performs complex analysis that may maintain state during processing.
    
    Returns:
        TrendAnalyzer instance
    """
    from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer
    return TrendAnalyzer()


@injectable(use_cache=False)
def get_trend_reporter_tool():
    """Provide the trend reporter tool.
    
    Uses use_cache=False to create new instances for each injection, as it
    maintains state during report generation and handles file operations.
    
    Returns:
        TrendReporter instance
    """
    from local_newsifier.tools.trend_reporter import TrendReporter
    return TrendReporter(output_dir="trend_output")


@injectable(use_cache=False)
def get_context_analyzer_tool():
    """Provide the context analyzer tool.
    
    Uses use_cache=False to create new instances for each injection, as it
    loads and interacts with NLP models that may maintain state.
    
    Returns:
        ContextAnalyzer instance
    """
    from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
    return ContextAnalyzer()


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
def get_entity_extractor_tool():
    """Provide the entity extractor tool (alias with _tool suffix).
    
    This provides the same entity extractor with a consistent naming pattern.
    Uses use_cache=False to create new instances for each injection, as NLP 
    tools may have stateful caches or models.
    
    Returns:
        EntityExtractor instance
    """
    return get_entity_extractor()


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
def get_entity_resolver_tool():
    """Provide the entity resolver tool (alias with _tool suffix).
    
    This provides the same entity resolver with a consistent naming pattern.
    Uses use_cache=False to create new instances for each injection, as this tool
    may have state during the resolution process.
    
    Returns:
        EntityResolver instance
    """
    return get_entity_resolver()


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
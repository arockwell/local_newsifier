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

from local_newsifier.tools.entity_tracker_service import EntityTracker
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
from local_newsifier.tools.resolution.entity_resolver import EntityResolver

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
def get_apify_source_config_crud():
    """Provide the apify source config CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        ApifySourceConfigCRUD instance
    """
    from local_newsifier.crud.apify_source_config import apify_source_config
    return apify_source_config


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
def get_opinion_visualizer_tool():
    """Provide the opinion visualizer tool.
    
    Uses use_cache=False to create new instances for each injection, as it
    interacts with database and maintains state during visualization generation.
    
    Returns:
        OpinionVisualizerTool instance
    """
    from local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool
    return OpinionVisualizerTool()


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
def get_entity_tracker_tool():
    """Provide the entity tracker tool.
    
    Uses use_cache=False to create new instances for each injection, as this tool
    maintains state during the entity tracking process.
    
    Returns:
        EntityTracker instance
    """
    from local_newsifier.tools.entity_tracker_service import EntityTracker
    return EntityTracker()


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


@injectable(use_cache=False)
def get_file_writer_tool():
    """Provide the file writer tool.
    
    Uses use_cache=False to create new instances for each injection, as this tool
    maintains state during file writing operations.
    
    Returns:
        FileWriterTool instance
    """
    from local_newsifier.tools.file_writer import FileWriterTool
    return FileWriterTool(output_dir="output")


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
    feed_processing_log_crud: Annotated[Any, Depends(get_feed_processing_log_crud)],
    rss_parser: Annotated[Any, Depends(get_rss_parser)],
    article_service: Annotated[Any, Depends(get_article_service)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the RSS feed service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        rss_feed_crud: RSS feed CRUD component
        feed_processing_log_crud: Feed processing log CRUD component
        rss_parser: RSS parser tool
        article_service: Article service
        session: Database session
        
    Returns:
        RSSFeedService instance
    """
    from local_newsifier.services.rss_feed_service import RSSFeedService
    
    return RSSFeedService(
        rss_feed_crud=rss_feed_crud,
        feed_processing_log_crud=feed_processing_log_crud,
        article_service=article_service,
        session_factory=lambda: session
    )


# CLI-specific provider functions

@injectable(use_cache=False)
def get_news_pipeline_flow(
    article_service: Annotated[Any, Depends(get_article_service)],
    entity_service: Annotated[Any, Depends(get_entity_service)],
    web_scraper_tool: Annotated[Any, Depends(get_web_scraper_tool)],
    file_writer_tool: Annotated[Any, Depends(get_trend_reporter_tool)],
    entity_extractor_tool: Annotated[Any, Depends(get_entity_extractor_tool)],
    context_analyzer_tool: Annotated[Any, Depends(get_context_analyzer_tool)],
    entity_resolver_tool: Annotated[Any, Depends(get_entity_resolver_tool)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the news pipeline flow for CLI commands.
    
    Args:
        article_service: Article service
        entity_service: Entity service
        web_scraper_tool: Web scraper tool
        file_writer_tool: File writer tool
        entity_extractor_tool: Entity extractor tool
        context_analyzer_tool: Context analyzer tool
        entity_resolver_tool: Entity resolver tool
        session: Database session
        
    Returns:
        NewsPipelineFlow instance
    """
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    
    return NewsPipelineFlow(
        article_service=article_service,
        entity_service=entity_service,
        web_scraper=web_scraper_tool,
        file_writer=file_writer_tool,
        entity_extractor=entity_extractor_tool,
        context_analyzer=context_analyzer_tool,
        entity_resolver=entity_resolver_tool,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_entity_tracking_flow(
    entity_service: Annotated[Any, Depends(get_entity_service)],
    entity_tracker_tool: Annotated[Any, Depends(get_entity_tracker_tool)],  # Fixed dependency
    entity_extractor_tool: Annotated[Any, Depends(get_entity_extractor_tool)],
    context_analyzer_tool: Annotated[Any, Depends(get_context_analyzer_tool)],
    entity_resolver_tool: Annotated[Any, Depends(get_entity_resolver_tool)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the entity tracking flow for CLI commands.
    
    Args:
        entity_service: Entity service
        entity_tracker_tool: Entity tracker tool
        entity_extractor_tool: Entity extractor tool
        context_analyzer_tool: Context analyzer tool
        entity_resolver_tool: Entity resolver tool
        session: Database session
        
    Returns:
        EntityTrackingFlow instance
    """
    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
    
    return EntityTrackingFlow(
        entity_service=entity_service,
        entity_tracker=entity_tracker_tool,
        entity_extractor=entity_extractor_tool,
        context_analyzer=context_analyzer_tool,
        entity_resolver=entity_resolver_tool,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_apify_service():
    """Provide the Apify service.
    
    Uses use_cache=False to create new instances for each injection,
    as this service may maintain state during API interactions.
    
    Returns:
        ApifyService instance
    """
    from local_newsifier.services.apify_service import ApifyService
    from local_newsifier.config.settings import settings
    
    return ApifyService(settings.APIFY_TOKEN)
 
def get_analysis_service(
    article_crud: Annotated[Any, Depends(get_article_crud)],
    analysis_result_crud: Annotated[Any, Depends(get_analysis_result_crud)],
    trend_analyzer: Annotated[Any, Depends(get_trend_analyzer_tool)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the analysis service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        article_crud: Article CRUD component
        analysis_result_crud: Analysis result CRUD component
        trend_analyzer: Trend analyzer tool
        session: Database session
        
    Returns:
        AnalysisService instance
    """
    from local_newsifier.services.analysis_service import AnalysisService
    
    return AnalysisService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        trend_analyzer=trend_analyzer,
        session_factory=lambda: session
    )


# Flow providers

def get_entity_tracking_flow():
    """Factory function to provide the entity tracking flow.
    
    This function creates a new EntityTrackingFlow instance with all required dependencies
    injected explicitly. It's used by the container to get the flow.
    
    Returns:
        EntityTrackingFlow instance
    """
    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
    
    # Get all required dependencies
    entity_service = get_entity_service()
    entity_tracker = get_entity_tracker_tool()
    entity_extractor = get_entity_extractor_tool()
    context_analyzer = get_context_analyzer_tool()
    entity_resolver = get_entity_resolver_tool()
    session = next(get_session())
    
    # Create and return the flow with explicit dependencies
    return EntityTrackingFlow(
        entity_service=entity_service,
        entity_tracker=entity_tracker,
        entity_extractor=entity_extractor,
        context_analyzer=context_analyzer,
        entity_resolver=entity_resolver,
        session=session
    )


def get_news_pipeline_flow():
    """Factory function to provide the news pipeline flow.
    
    This function creates a new NewsPipelineFlow instance with all required dependencies
    injected explicitly. It's used by the container to get the flow.
    
    Returns:
        NewsPipelineFlow instance
    """
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.services.news_pipeline_service import NewsPipelineService
    
    # Get all required dependencies
    article_service = get_article_service()
    entity_service = get_entity_service()
    web_scraper = get_web_scraper_tool()
    file_writer = get_file_writer_tool()
    session = next(get_session())
    
    # Create pipeline service
    pipeline_service = NewsPipelineService(
        article_service=article_service,
        web_scraper=web_scraper,
        file_writer=file_writer,
        session_factory=lambda: session
    )
    
    # Create and return the flow
    return NewsPipelineFlow(
        article_service=article_service,
        entity_service=entity_service,
        pipeline_service=pipeline_service,
        web_scraper=web_scraper,
        file_writer=file_writer,
        session=session
    )


def get_trend_analysis_flow():
    """Factory function to provide the trend analysis flow.
    
    This function creates a new NewsTrendAnalysisFlow instance with all required dependencies
    injected explicitly. It's used by the container to get the flow.
    
    Returns:
        NewsTrendAnalysisFlow instance
    """
    from local_newsifier.flows.trend_analysis_flow import NewsTrendAnalysisFlow
    from local_newsifier.models.trend import TrendAnalysisConfig
    
    # Get all required dependencies
    analysis_service = get_analysis_service()
    trend_reporter = get_trend_reporter_tool()
    session = next(get_session())
    
    # Create and return the flow with explicit dependencies
    return NewsTrendAnalysisFlow(
        analysis_service=analysis_service,
        trend_reporter=trend_reporter,
        session=session,
        config=TrendAnalysisConfig()
    )


def get_public_opinion_flow():
    """Factory function to provide the public opinion flow.
    
    This function creates a new PublicOpinionFlow instance with all required dependencies
    injected explicitly. It's used by the container to get the flow.
    
    Returns:
        PublicOpinionFlow instance
    """
    from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
    
    # Get all required dependencies
    sentiment_analyzer = get_sentiment_analyzer_tool()
    sentiment_tracker = get_sentiment_tracker_tool()
    opinion_visualizer = get_opinion_visualizer_tool()
    session = next(get_session())
    
    # Create and return the flow with explicit dependencies
    return PublicOpinionFlow(
        sentiment_analyzer=sentiment_analyzer,
        sentiment_tracker=sentiment_tracker,
        opinion_visualizer=opinion_visualizer,
        session=session
    )


def get_rss_scraping_flow():
    """Factory function to provide the RSS scraping flow.
    
    This function creates a new RSSScrapingFlow instance with all required dependencies
    injected explicitly. It's used by the container to get the flow.
    
    Returns:
        RSSScrapingFlow instance
    """
    from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
    
    # Get all required dependencies
    rss_feed_service = get_rss_feed_service()
    article_service = get_article_service()
    rss_parser = get_rss_parser()
    web_scraper = get_web_scraper_tool()
    
    # Create and return the flow with explicit dependencies
    return RSSScrapingFlow(
        rss_feed_service=rss_feed_service,
        article_service=article_service,
        rss_parser=rss_parser,
        web_scraper=web_scraper,
        cache_dir="cache"
    )

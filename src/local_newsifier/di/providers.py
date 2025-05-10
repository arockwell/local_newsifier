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
from typing import Annotated, Any, Dict, Generator, Optional, TYPE_CHECKING

from fastapi import Depends
from fastapi_injectable import injectable

# Using injectable directly - no scope parameter in version 0.7.0
# We'll control instance reuse with use_cache=True/False
from sqlmodel import Session

if TYPE_CHECKING:
    from local_newsifier.crud.article import CRUDArticle
    from local_newsifier.crud.entity import CRUDEntity
    from local_newsifier.crud.analysis_result import CRUDAnalysisResult
    from local_newsifier.crud.canonical_entity import CRUDCanonicalEntity
    from local_newsifier.crud.entity_mention_context import CRUDEntityMentionContext
    from local_newsifier.crud.entity_profile import CRUDEntityProfile
    from local_newsifier.crud.entity_relationship import CRUDEntityRelationship
    from local_newsifier.crud.rss_feed import CRUDRSSFeed
    from local_newsifier.crud.feed_processing_log import CRUDFeedProcessingLog
    from local_newsifier.crud.apify_source_config import CRUDApifySourceConfig
    from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer
    from local_newsifier.tools.entity_tracker_service import EntityTracker
    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
    from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
    from local_newsifier.tools.resolution.entity_resolver import EntityResolver
    from local_newsifier.services.entity_service import EntityService
    from local_newsifier.services.article_service import ArticleService
    from local_newsifier.services.apify_service import ApifyService
    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
    from local_newsifier.flows.analysis.headline_trend_flow import HeadlineTrendFlow
    from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
    from local_newsifier.flows.trend_analysis_flow import NewsTrendAnalysisFlow

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


@injectable(use_cache=False)
def get_apify_source_config_crud():
    """Provide the Apify source config CRUD component.
    
    Uses use_cache=False to create new instances for each injection, as CRUD 
    components interact with the database and should not share state between operations.
    
    Returns:
        CRUDApifySourceConfig instance
    """
    from local_newsifier.crud.apify_source_config import apify_source_config
    return apify_source_config


# Tool providers

@injectable(use_cache=False)
def get_nlp_model() -> Any:
    """Provide the spaCy NLP model.

    Uses use_cache=False to create new instances for each injection,
    preventing shared state in NLP processing.

    Returns:
        Loaded spaCy Language model or None if loading fails
    """
    try:
        import spacy
        return spacy.load("en_core_web_lg")
    except (ImportError, OSError) as e:
        import logging
        logging.warning(f"Failed to load NLP model: {str(e)}")
        return None

@injectable(use_cache=False)
def get_web_scraper_tool():
    """Provide the web scraper tool.

    Uses use_cache=False to create new instances for each injection, as this tool
    maintains session and WebDriver state that shouldn't be shared between operations.

    Returns:
        WebScraperTool instance
    """
    from local_newsifier.tools.web_scraper import WebScraperTool

    # Create a new requests session for this instance
    import requests
    session = requests.Session()

    # Set a standard user agent
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    session.headers.update({"User-Agent": user_agent})

    return WebScraperTool(
        session=session,
        web_driver=None,  # WebDriver will be created lazily when needed
        user_agent=user_agent
    )


@injectable(use_cache=False)
def get_sentiment_analyzer_config():
    """Provide the configuration for the sentiment analyzer tool.

    This separates configuration from the tool instance, allowing for
    different configuration settings to be injected.

    Returns:
        Configuration dictionary with model_name
    """
    return {
        "model_name": "en_core_web_sm"
    }

@injectable(use_cache=False)
def get_sentiment_analyzer_tool():
    """Provide the sentiment analyzer tool.

    Uses use_cache=False to create new instances for each injection, as sentiment
    analysis tools may maintain state during processing and interact with NLP models.

    Returns:
        SentimentAnalyzer instance
    """
    from local_newsifier.tools.sentiment_analyzer import SentimentAnalyzer
    return SentimentAnalyzer(nlp_model=get_nlp_model())


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
def get_trend_analyzer_config():
    """Provide the configuration for the trend analyzer tool.

    This separates configuration from the tool instance, allowing for
    different configuration settings to be injected.

    Returns:
        Configuration dictionary with model_name
    """
    return {
        "model_name": "en_core_web_lg"
    }

@injectable(use_cache=False)
def get_trend_analyzer_tool():
    """Provide the trend analyzer tool.

    Uses use_cache=False to create new instances for each injection, as it
    performs complex analysis that may maintain state during processing.

    Returns:
        TrendAnalyzer instance
    """
    from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer
    return TrendAnalyzer(nlp_model=get_nlp_model())


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
def get_context_analyzer_config():
    """Provide the configuration for the context analyzer tool.

    This separates configuration from the tool instance, allowing for
    different configuration settings to be injected.

    Returns:
        Configuration dictionary with model_name
    """
    return {
        "model_name": "en_core_web_lg"
    }

@injectable(use_cache=False)
def get_context_analyzer_tool():
    """Provide the context analyzer tool.

    Uses use_cache=False to create new instances for each injection, as it
    loads and interacts with NLP models that may maintain state.

    Returns:
        ContextAnalyzer instance
    """
    from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
    return ContextAnalyzer(nlp_model=get_nlp_model())


@injectable(use_cache=False)
def get_apify_service():
    """Provide the Apify service.
    
    Uses use_cache=False to create new instances for each injection, as it
    interacts with external APIs that require fresh client instances.
    
    Returns:
        ApifyService instance
    """
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService()


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
def get_entity_resolver_config():
    """Provide the configuration for the entity resolver tool.

    This separates configuration from the tool instance, allowing for
    different configuration settings to be injected.

    Returns:
        Configuration dictionary with similarity_threshold
    """
    return {
        "similarity_threshold": 0.85
    }

@injectable(use_cache=False)
def get_entity_resolver(
    config: Annotated[Dict, Depends(get_entity_resolver_config)]
):
    """Provide the entity resolver tool.

    Uses use_cache=False to create new instances for each injection, as this tool
    may have state during the resolution process.

    Args:
        config: Configuration dictionary with similarity_threshold

    Returns:
        EntityResolver instance
    """
    from local_newsifier.tools.resolution.entity_resolver import EntityResolver
    return EntityResolver(similarity_threshold=config["similarity_threshold"])


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
def get_rss_parser_config():
    """Provide the configuration for the RSS parser tool.

    This separates configuration from the tool instance, allowing for
    different configuration settings to be injected.

    Returns:
        Configuration dictionary with cache_dir, request_timeout, and user_agent
    """
    return {
        "cache_dir": "cache",
        "request_timeout": 30,
        "user_agent": "Local Newsifier RSS Parser"
    }

@injectable(use_cache=False)
def get_rss_parser(
    config: Annotated[Dict, Depends(get_rss_parser_config)]
):
    """Provide the RSS parser tool.

    Uses use_cache=False to create new instances for each injection, as parsers
    may maintain state during processing.

    Args:
        config: Configuration dictionary with cache_dir, request_timeout, and user_agent

    Returns:
        RSSParser instance
    """
    from local_newsifier.tools.rss_parser import RSSParser
    return RSSParser(
        cache_dir=config["cache_dir"],
        request_timeout=config["request_timeout"],
        user_agent=config["user_agent"]
    )


@injectable(use_cache=False)
def get_file_writer_config():
    """Provide the configuration for the file writer tool.

    This separates configuration from the tool instance, allowing for
    different output directories to be injected.

    Returns:
        Configuration dictionary with output_dir
    """
    return {
        "output_dir": "output"
    }

@injectable(use_cache=False)
def get_file_writer_tool(
    config: Annotated[Dict, Depends(get_file_writer_config)]
):
    """Provide the file writer tool.

    Uses use_cache=False to create new instances for each injection, as this tool
    maintains state during file writing operations.

    Args:
        config: Configuration dictionary with output_dir

    Returns:
        FileWriterTool instance
    """
    from local_newsifier.tools.file_writer import FileWriterTool
    return FileWriterTool(output_dir=config["output_dir"])


# Service providers


@injectable(use_cache=False)
def get_apify_schedule_manager(
    apify_service: Annotated["ApifyService", Depends(get_apify_service)],
    apify_source_config_crud: Annotated["CRUDApifySourceConfig", Depends(get_apify_source_config_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the Apify schedule manager service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        apify_service: Apify service for API interactions
        apify_source_config_crud: CRUD for Apify source configurations
        session: Database session
        
    Returns:
        ApifyScheduleManager instance
    """
    from local_newsifier.services.apify_schedule_manager import ApifyScheduleManager
    
    return ApifyScheduleManager(
        apify_service=apify_service,
        apify_source_config_crud=apify_source_config_crud,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_analysis_service(
    analysis_result_crud: Annotated["CRUDAnalysisResult", Depends(get_analysis_result_crud)],
    article_crud: Annotated["CRUDArticle", Depends(get_article_crud)],
    entity_crud: Annotated["CRUDEntity", Depends(get_entity_crud)],
    trend_analyzer: Annotated["TrendAnalyzer", Depends(get_trend_analyzer_tool)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the analysis service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        analysis_result_crud: Analysis result CRUD component
        article_crud: Article CRUD component
        entity_crud: Entity CRUD component
        trend_analyzer: Trend analyzer tool
        session: Database session
        
    Returns:
        AnalysisService instance
    """
    from local_newsifier.services.analysis_service import AnalysisService
    
    return AnalysisService(
        analysis_result_crud=analysis_result_crud,
        article_crud=article_crud,
        entity_crud=entity_crud,
        trend_analyzer=trend_analyzer,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_entity_service(
    entity_crud: Annotated["CRUDEntity", Depends(get_entity_crud)],
    canonical_entity_crud: Annotated["CRUDCanonicalEntity", Depends(get_canonical_entity_crud)],
    entity_mention_context_crud: Annotated["CRUDEntityMentionContext", Depends(get_entity_mention_context_crud)],
    entity_profile_crud: Annotated["CRUDEntityProfile", Depends(get_entity_profile_crud)],
    article_crud: Annotated["CRUDArticle", Depends(get_article_crud)],
    entity_extractor: Annotated["EntityExtractor", Depends(get_entity_extractor)],
    context_analyzer: Annotated["ContextAnalyzer", Depends(get_context_analyzer_tool)],
    entity_resolver: Annotated["EntityResolver", Depends(get_entity_resolver)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the entity service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        entity_crud: Entity CRUD component
        canonical_entity_crud: Canonical entity CRUD component
        entity_mention_context_crud: Entity mention context CRUD component
        entity_profile_crud: Entity profile CRUD component
        article_crud: Article CRUD component
        entity_extractor: Entity extractor tool
        context_analyzer: Context analyzer tool
        entity_resolver: Entity resolver tool
        session: Database session
        
    Returns:
        EntityService instance
    """
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
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_article_service(
    article_crud: Annotated["CRUDArticle", Depends(get_article_crud)],
    analysis_result_crud: Annotated["CRUDAnalysisResult", Depends(get_analysis_result_crud)],
    entity_service: Annotated["EntityService", Depends(get_entity_service)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the article service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        article_crud: Article CRUD component
        analysis_result_crud: Analysis result CRUD component
        entity_service: Entity service
        session: Database session
        
    Returns:
        ArticleService instance
    """
    from local_newsifier.services.article_service import ArticleService
    
    return ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        entity_service=entity_service,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_news_pipeline_service(
    article_service: Annotated[Any, Depends(get_article_service)],
    web_scraper: Annotated[Any, Depends(get_web_scraper_tool)],
    file_writer: Annotated[Any, Depends(get_file_writer_tool)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the news pipeline service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        article_service: Article service
        web_scraper: Web scraper tool
        file_writer: File writer tool
        session: Database session
        
    Returns:
        NewsPipelineService instance
    """
    from local_newsifier.services.news_pipeline_service import NewsPipelineService
    
    return NewsPipelineService(
        article_service=article_service,
        web_scraper=web_scraper,
        file_writer=file_writer,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_rss_feed_service(
    rss_feed_crud: Annotated["CRUDRSSFeed", Depends(get_rss_feed_crud)],
    feed_processing_log_crud: Annotated["CRUDFeedProcessingLog", Depends(get_feed_processing_log_crud)],
    article_service: Annotated["ArticleService", Depends(get_article_service)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the RSS feed service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        rss_feed_crud: RSS feed CRUD component
        feed_processing_log_crud: Feed processing log CRUD component
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


@injectable(use_cache=False)
def get_analysis_service_legacy(
    article_crud: Annotated["CRUDArticle", Depends(get_article_crud)],
    analysis_result_crud: Annotated["CRUDAnalysisResult", Depends(get_analysis_result_crud)],
    trend_analyzer: Annotated["TrendAnalyzer", Depends(get_trend_analyzer_tool)],
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

@injectable(use_cache=False)
def get_entity_tracking_flow(
    entity_service: Annotated["EntityService", Depends(get_entity_service)],
    entity_tracker: Annotated["EntityTracker", Depends(get_entity_tracker_tool)],
    entity_extractor: Annotated["EntityExtractor", Depends(get_entity_extractor_tool)],
    context_analyzer: Annotated["ContextAnalyzer", Depends(get_context_analyzer_tool)],
    entity_resolver: Annotated["EntityResolver", Depends(get_entity_resolver_tool)],
    session: Annotated[Session, Depends(get_session)]
) -> "EntityTrackingFlow":
    """Provide the entity tracking flow with injectable dependencies.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        entity_service: Entity service
        entity_tracker: Entity tracker tool
        entity_extractor: Entity extractor tool
        context_analyzer: Context analyzer tool
        entity_resolver: Entity resolver tool
        session: Database session
        
    Returns:
        EntityTrackingFlow instance
    """
    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
    return EntityTrackingFlow(
        entity_service=entity_service,
        entity_tracker=entity_tracker,
        entity_extractor=entity_extractor,
        context_analyzer=context_analyzer,
        entity_resolver=entity_resolver,
        session=session,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_headline_trend_flow(
    analysis_service: Annotated[Any, Depends(get_analysis_service)],
    session: Annotated[Session, Depends(get_session)]
) -> "HeadlineTrendFlow":
    """Provide the headline trend flow.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        analysis_service: Analysis service
        session: Database session
        
    Returns:
        HeadlineTrendFlow instance
    """
    from local_newsifier.flows.analysis.headline_trend_flow import HeadlineTrendFlow
    
    return HeadlineTrendFlow(
        analysis_service=analysis_service,
        session=session
    )


@injectable(use_cache=False)
def get_rss_scraping_flow(
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)],
    article_service: Annotated[Any, Depends(get_article_service)],
    rss_parser: Annotated[Any, Depends(get_rss_parser)],
    web_scraper: Annotated[Any, Depends(get_web_scraper_tool)],
    session: Annotated[Session, Depends(get_session)]
) -> "RSSScrapingFlow":
    """Provide the RSS scraping flow with injectable dependencies.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        rss_feed_service: RSS feed service
        article_service: Article service
        rss_parser: RSS parser tool
        web_scraper: Web scraper tool
        session: Database session
        
    Returns:
        RSSScrapingFlow instance
    """
    from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
    
    return RSSScrapingFlow(
        rss_feed_service=rss_feed_service,
        article_service=article_service,
        rss_parser=rss_parser,
        web_scraper=web_scraper,
        cache_dir="cache",
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_news_pipeline_flow(
    article_service: Annotated[Any, Depends(get_article_service)],
    entity_service: Annotated[Any, Depends(get_entity_service)],
    pipeline_service: Annotated[Any, Depends(get_news_pipeline_service)],
    web_scraper: Annotated[Any, Depends(get_web_scraper_tool)],
    file_writer: Annotated[Any, Depends(get_file_writer_tool)],
    entity_extractor: Annotated[Any, Depends(get_entity_extractor_tool)],
    context_analyzer: Annotated[Any, Depends(get_context_analyzer_tool)],
    entity_resolver: Annotated[Any, Depends(get_entity_resolver_tool)],
    session: Annotated[Session, Depends(get_session)]
) -> "NewsPipelineFlow":
    """Provide the news pipeline flow with injectable dependencies.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        article_service: Article service
        entity_service: Entity service
        pipeline_service: News pipeline service
        web_scraper: Web scraper tool
        file_writer: File writer tool
        entity_extractor: Entity extractor tool
        context_analyzer: Context analyzer tool
        entity_resolver: Entity resolver tool
        session: Database session
        
    Returns:
        NewsPipelineFlow instance
    """
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    return NewsPipelineFlow(
        article_service=article_service,
        entity_service=entity_service,
        pipeline_service=pipeline_service,
        web_scraper=web_scraper,
        file_writer=file_writer,
        entity_extractor=entity_extractor,
        context_analyzer=context_analyzer,
        entity_resolver=entity_resolver,
        session=session,
        session_factory=lambda: session
    )


@injectable(use_cache=False)
def get_trend_analysis_flow(
    analysis_service: Annotated["AnalysisService", Depends(get_analysis_service)],
    trend_reporter: Annotated["TrendReporter", Depends(get_trend_reporter_tool)],
    session: Annotated[Session, Depends(get_session)]
) -> "NewsTrendAnalysisFlow":
    """Provide the trend analysis flow with injectable dependencies.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        analysis_service: Analysis service
        trend_reporter: Trend reporter tool
        session: Database session
        
    Returns:
        NewsTrendAnalysisFlow instance
    """
    from local_newsifier.flows.trend_analysis_flow import NewsTrendAnalysisFlow
    from local_newsifier.models.trend import TrendAnalysisConfig
    return NewsTrendAnalysisFlow(
        analysis_service=analysis_service,
        trend_reporter=trend_reporter,
        session=session,
        config=TrendAnalysisConfig()
    )


@injectable(use_cache=False)
def get_public_opinion_flow(
    sentiment_analyzer: Annotated["SentimentAnalyzer", Depends(get_sentiment_analyzer_tool)],
    sentiment_tracker: Annotated["SentimentTracker", Depends(get_sentiment_tracker_tool)],
    opinion_visualizer: Annotated["OpinionVisualizerTool", Depends(get_opinion_visualizer_tool)],
    session: Annotated[Session, Depends(get_session)]
) -> "PublicOpinionFlow":
    """Provide the public opinion flow with injectable dependencies.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    
    Args:
        sentiment_analyzer: Sentiment analysis tool
        sentiment_tracker: Sentiment tracker tool
        opinion_visualizer: Opinion visualizer tool
        session: Database session
        
    Returns:
        PublicOpinionFlow instance
    """
    from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
    return PublicOpinionFlow(
        sentiment_analyzer=sentiment_analyzer,
        sentiment_tracker=sentiment_tracker,
        opinion_visualizer=opinion_visualizer,
        session=session
    )


# CLI command providers

@injectable(use_cache=False)
def get_apify_service_cli(token: Optional[str] = None):
    """Provide the Apify service for CLI commands.
    
    This is a special provider for the CLI that allows passing a token from
    command-line arguments, environment variables, or settings.
    
    Args:
        token: Optional Apify token to use (overrides settings)
        
    Returns:
        ApifyService instance
    """
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService(token=token)


@injectable(use_cache=False)
def get_db_stats_command():
    """Provide the database stats command function.
    
    Uses use_cache=False to create a new instance for each injection,
    preventing session leakage between operations.
    
    Returns:
        Function to execute db stats command
    """
    from local_newsifier.cli.commands.db import db_stats
    return db_stats


@injectable(use_cache=False)
def get_db_duplicates_command():
    """Provide the database duplicates command function.
    
    Uses use_cache=False to create a new instance for each injection,
    preventing session leakage between operations.
    
    Returns:
        Function to execute db duplicates command
    """
    from local_newsifier.cli.commands.db import check_duplicates
    return check_duplicates


@injectable(use_cache=False)
def get_db_articles_command():
    """Provide the database articles command function.
    
    Uses use_cache=False to create a new instance for each injection,
    preventing session leakage between operations.
    
    Returns:
        Function to execute db articles command
    """
    from local_newsifier.cli.commands.db import list_articles
    return list_articles


@injectable(use_cache=False)
def get_db_inspect_command():
    """Provide the database inspect command function.
    
    Uses use_cache=False to create a new instance for each injection,
    preventing session leakage between operations.
    
    Returns:
        Function to execute db inspect command
    """
    from local_newsifier.cli.commands.db import inspect_record
    return inspect_record


@injectable(use_cache=False)
def get_feeds_list_command():
    """Provide the feeds list command function.
    
    Uses use_cache=False to create a new instance for each injection,
    preventing session leakage between operations.
    
    Returns:
        Function to execute feeds list command
    """
    from local_newsifier.cli.commands.feeds import list_feeds
    return list_feeds


@injectable(use_cache=False)
def get_feeds_add_command():
    """Provide the feeds add command function.
    
    Uses use_cache=False to create a new instance for each injection,
    preventing session leakage between operations.
    
    Returns:
        Function to execute feeds add command
    """
    from local_newsifier.cli.commands.feeds import add_feed
    return add_feed


@injectable(use_cache=False)
def get_feeds_show_command():
    """Provide the feeds show command function.
    
    Uses use_cache=False to create a new instance for each injection,
    preventing session leakage between operations.
    
    Returns:
        Function to execute feeds show command
    """
    from local_newsifier.cli.commands.feeds import show_feed
    return show_feed


@injectable(use_cache=False)
def get_feeds_process_command():
    """Provide the feeds process command function.
    
    Uses use_cache=False to create a new instance for each injection,
    preventing session leakage between operations.
    
    Returns:
        Function to execute feeds process command
    """
    from local_newsifier.cli.commands.feeds import process_feed
    return process_feed
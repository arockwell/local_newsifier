"""
Container Initialization

This module initializes the dependency injection container with all services
and flows in the application. It provides a central registry for dependency 
resolution and lifecycle management.
"""

from local_newsifier.di_container import DIContainer, Scope
from local_newsifier.database.engine import SessionManager
from local_newsifier.database.session_utils import get_container_session
import logging

logger = logging.getLogger(__name__)

# Import CRUD modules
from local_newsifier.crud import (
    analysis_result,
    apify_source_config,
    article,
    canonical_entity,
    entity,
    entity_mention_context,
    entity_profile,
    entity_relationship,
    rss_feed,
    feed_processing_log,
)

# Import service classes
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.rss_feed_service import RSSFeedService
from local_newsifier.services.apify_service import ApifyService


def init_container(environment="production"):
    """Initialize and configure the dependency injection container.
    
    This function creates a new container instance and registers all
    services, flows, and dependencies needed by the application.
    
    Args:
        environment: The environment to configure for ("production", "testing", "development")
    
    Returns:
        DIContainer: The initialized container
    """
    container = DIContainer()
    
    # Register environment
    container.register("environment", environment)
    
    # Register CRUD modules
    container.register("article_crud", article)
    container.register("analysis_result_crud", analysis_result)
    container.register("apify_source_config_crud", apify_source_config)
    container.register("entity_crud", entity)
    container.register("canonical_entity_crud", canonical_entity)
    container.register("entity_mention_context_crud", entity_mention_context)
    container.register("entity_profile_crud", entity_profile)
    container.register("entity_relationship_crud", entity_relationship)
    container.register("rss_feed_crud", rss_feed)
    container.register("feed_processing_log_crud", feed_processing_log)
    
    # Register session management
    if environment == "testing":
        # For testing, we might want different session behavior
        container.register_factory("session_factory", 
                                lambda c: SessionManager)
    else:
        container.register_factory("session_factory", 
                                lambda c: SessionManager)
    
    # Register session utility
    container.register_factory_with_params(
        "get_session", 
        lambda c, **kwargs: get_container_session(c, **kwargs)
    )
    
    # Register Core Tools
    register_core_tools(container)
    
    # Register Analysis Tools
    register_analysis_tools(container)
    
    # Register Entity Tools
    register_entity_tools(container)
    
    # Register service classes
    register_services(container)
    
    # Register flow classes
    register_flows(container)
    
    # Register parameterized factories for service access
    register_service_factories(container)
    
    # Environment-specific configurations
    if environment == "development":
        logger.info("Initializing container with development configurations")
        # Development-specific registrations
        pass
    elif environment == "testing":
        logger.info("Initializing container with testing configurations")
        # Testing-specific registrations
        pass
    else:
        logger.info("Initializing container with production configurations")
    
    return container

def register_service_factories(container):
    """Register parameterized factories for services.
    
    These factories allow getting services with runtime parameters.
    
    Args:
        container: The DI container instance
    """
    # Entity service with params
    container.register_factory_with_params(
        "entity_service_with_params",
        lambda c, **kwargs: kwargs.get("entity_service") or c.get("entity_service")
    )
    
    # Article service with params
    container.register_factory_with_params(
        "article_service_with_params",
        lambda c, **kwargs: kwargs.get("article_service") or c.get("article_service")
    )
    
    # News pipeline service with params
    container.register_factory_with_params(
        "news_pipeline_service_with_params",
        lambda c, **kwargs: kwargs.get("news_pipeline_service") or c.get("news_pipeline_service")
    )
    
    # Analysis service with params
    container.register_factory_with_params(
        "analysis_service_with_params",
        lambda c, **kwargs: kwargs.get("analysis_service") or c.get("analysis_service")
    )
    
    # RSS feed service with params
    container.register_factory_with_params(
        "rss_feed_service_with_params",
        lambda c, **kwargs: kwargs.get("rss_feed_service") or c.get("rss_feed_service")
    )

def register_services(container):
    """Register service classes in the container.
    
    This function registers all service classes with their dependencies.
    Services are the core business logic components that coordinate
    between CRUD operations and tools.
    
    Args:
        container: The DI container instance
    """
    # Import all service classes
    try:
        from local_newsifier.services.entity_service import EntityService
        from local_newsifier.services.news_pipeline_service import NewsPipelineService
        from local_newsifier.services.analysis_service import AnalysisService
        
        # Register EntityService with its dependencies
        container.register_factory(
            "entity_service", 
            lambda c: EntityService(
                entity_crud=c.get("entity_crud"),
                canonical_entity_crud=c.get("canonical_entity_crud"),
                entity_mention_context_crud=c.get("entity_mention_context_crud"),
                entity_profile_crud=c.get("entity_profile_crud"),
                article_crud=c.get("article_crud"),
                entity_extractor=c.get("entity_extractor_tool"),
                context_analyzer=c.get("context_analyzer_tool"),
                entity_resolver=c.get("entity_resolver_tool"),
                session_factory=c.get("session_factory")
            ),
            scope=Scope.SINGLETON
        )
        
        # Register AnalysisService (only if not already registered in analysis_tools)
        if not container.has("analysis_service"):
            container.register_factory(
                "analysis_service", 
                lambda c: AnalysisService(
                    analysis_result_crud=c.get("analysis_result_crud"),
                    article_crud=c.get("article_crud"),
                    entity_crud=c.get("entity_crud"),
                    trend_analyzer=c.get("trend_analyzer_tool"),
                    session_factory=c.get("session_factory")
                ),
                scope=Scope.SINGLETON
            )
        
        # Register NewsPipelineService
        container.register_factory(
            "news_pipeline_service", 
            lambda c: NewsPipelineService(
                article_service=c.get("article_service"),
                web_scraper=c.get("web_scraper_tool"),
                file_writer=c.get("file_writer_tool"),
                session_factory=c.get("session_factory")
            ),
            scope=Scope.SINGLETON
        )
        
        # Register ArticleService with lifecycle support
        container.register_factory(
            "article_service", 
            lambda c: ArticleService(
                article_crud=c.get("article_crud"),
                analysis_result_crud=c.get("analysis_result_crud"),
                entity_service=c.get("entity_service"),  # Will be lazily loaded
                session_factory=c.get("session_factory"),
                container=c  # Inject the container itself
            ),
            scope=Scope.SINGLETON
        )
        
        # Register cleanup handlers for services that need resource management
        container.register_cleanup(
            "article_service",
            lambda s: s.cleanup() if hasattr(s, "cleanup") else None
        )
        
        # Register RSSFeedService with lifecycle support
        container.register_factory(
            "rss_feed_service", 
            lambda c: RSSFeedService(
                rss_feed_crud=c.get("rss_feed_crud"),
                feed_processing_log_crud=c.get("feed_processing_log_crud"),
                article_service=c.get("article_service"),  # Will be lazily loaded
                session_factory=c.get("session_factory"),
                container=c  # Inject the container itself
            ),
            scope=Scope.SINGLETON
        )
        
        # Register cleanup handler for RSSFeedService
        container.register_cleanup(
            "rss_feed_service",
            lambda s: s.cleanup() if hasattr(s, "cleanup") else None
        )
        
    except ImportError as e:
        # Log error but continue initialization
        logger.error(f"Error registering services: {e}")

def register_core_tools(container):
    """Register core tool classes in the container."""
    try:
        from local_newsifier.tools.web_scraper import WebScraperTool
        from local_newsifier.tools.rss_parser import RSSParser
        from local_newsifier.tools.file_writer import FileWriterTool
        
        # Register web_scraper_tool with configurable user_agent
        container.register_factory_with_params(
            "web_scraper_tool", 
            lambda c, **kwargs: WebScraperTool(
                user_agent=kwargs.get("user_agent")
            )
        )
        
        # Register rss_parser_tool with configurable parameters
        container.register_factory_with_params(
            "rss_parser_tool", 
            lambda c, **kwargs: RSSParser()
        )
        
        # Register file_writer_tool with configurable output_dir
        container.register_factory_with_params(
            "file_writer_tool", 
            lambda c, **kwargs: FileWriterTool(
                output_dir=kwargs.get("output_dir", "output")
            )
        )
        
        # Backward compatibility registrations
        container.register_factory("web_scraper", lambda c: c.get("web_scraper_tool"))
        container.register_factory("rss_parser", lambda c: c.get("rss_parser_tool"))
        container.register_factory("file_writer", lambda c: c.get("file_writer_tool"))
        
    except ImportError as e:
        # Log error but continue initialization
        logger.error(f"Error registering core tools: {e}")


def register_analysis_tools(container):
    """Register analysis tools in the container.
    
    Args:
        container: The DI container instance
    """
    try:
        # Import analysis tools
        from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer
        from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
        from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
        from local_newsifier.tools.sentiment_tracker import SentimentTracker
        from local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool
        from local_newsifier.tools.trend_reporter import TrendReporter
        from local_newsifier.services.analysis_service import AnalysisService
        
        # Register trend_analyzer_tool
        container.register_factory(
            "trend_analyzer_tool", 
            lambda c: TrendAnalyzer()
        )
        
        # Register context_analyzer_tool
        container.register_factory(
            "context_analyzer_tool", 
            lambda c: ContextAnalyzer()
        )
        
        # Register sentiment_analyzer_tool with configurable session
        container.register_factory_with_params(
            "sentiment_analyzer_tool", 
            lambda c, **kwargs: SentimentAnalysisTool(
                session=kwargs.get("session")
            )
        )
        
        # Register sentiment_tracker_tool with configurable session
        container.register_factory_with_params(
            "sentiment_tracker_tool", 
            lambda c, **kwargs: SentimentTracker(
                session=kwargs.get("session")
            )
        )
        
        # Register opinion_visualizer_tool with configurable session
        container.register_factory_with_params(
            "opinion_visualizer_tool", 
            lambda c, **kwargs: OpinionVisualizerTool(
                session=kwargs.get("session")
            )
        )
        
        # Register trend_reporter_tool with configurable output_dir
        container.register_factory_with_params(
            "trend_reporter_tool", 
            lambda c, **kwargs: TrendReporter(
                output_dir=kwargs.get("output_dir", "trend_output")
            )
        )
        
        # Register analysis_service
        container.register_factory_with_params(
            "analysis_service", 
            lambda c, **kwargs: AnalysisService(
                session=kwargs.get("session")
            )
        )
        
        # Backward compatibility registrations
        container.register_factory("trend_analyzer", lambda c: c.get("trend_analyzer_tool"))
        container.register_factory("context_analyzer", lambda c: c.get("context_analyzer_tool"))
        container.register_factory("sentiment_analyzer", lambda c: c.get("sentiment_analyzer_tool"))
        container.register_factory("sentiment_tracker", lambda c: c.get("sentiment_tracker_tool"))
        container.register_factory("opinion_visualizer", lambda c: c.get("opinion_visualizer_tool"))
        container.register_factory("trend_reporter", lambda c: c.get("trend_reporter_tool"))
        
    except ImportError as e:
        # Log error but continue initialization
        logger.error(f"Error registering analysis tools: {e}")


def register_entity_tools(container):
    """Register entity-related tools in the container.
    
    Args:
        container: The DI container instance
    """
    try:
        # Import entity tools
        from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
        from local_newsifier.tools.resolution.entity_resolver import EntityResolver
        from local_newsifier.tools.entity_tracker_service import EntityTracker
        
        # Register entity_extractor_tool
        container.register_factory(
            "entity_extractor_tool", 
            lambda c: EntityExtractor()
        )
        
        # Register entity_resolver_tool
        container.register_factory(
            "entity_resolver_tool", 
            lambda c: EntityResolver()
        )
        
        # Register entity_tracker_tool
        container.register_factory(
            "entity_tracker_tool", 
            lambda c: EntityTracker()
        )
        
        # Backward compatibility registrations
        container.register_factory("entity_extractor", lambda c: c.get("entity_extractor_tool"))
        container.register_factory("entity_resolver", lambda c: c.get("entity_resolver_tool"))
        container.register_factory("entity_tracker", lambda c: c.get("entity_tracker_tool"))
        
    except ImportError as e:
        # Log error but continue initialization
        logger.error(f"Error registering entity tools: {e}")


def register_services(container):
    """Register service classes in the container.
    
    Args:
        container: The DI container instance
    """
    # ArticleService 
    container.register_factory("article_service", 
        lambda c: ArticleService(
            article_crud=c.get("article_crud"),
            analysis_result_crud=c.get("analysis_result_crud"),
            entity_service=c.get("entity_service"),  # Will be lazily loaded
            session_factory=c.get("session_factory"),
            container=c  # Inject the container itself
        )
    )
    
    # RSSFeedService
    container.register_factory("rss_feed_service", 
        lambda c: RSSFeedService(
            rss_feed_crud=c.get("rss_feed_crud"),
            feed_processing_log_crud=c.get("feed_processing_log_crud"),
            article_service=c.get("article_service"),  # Will be lazily loaded
            session_factory=c.get("session_factory"),
            container=c  # Inject the container itself
        )
    )
    
    # ApifyService - use test_mode in test environment
    container.register_factory("apify_service", 
        lambda c: ApifyService(test_mode=(environment == "testing"))
    )
    
    # Import at runtime to avoid circular imports
    try:
        from local_newsifier.services.apify_source_config_service import ApifySourceConfigService
        
        # ApifySourceConfigService
        container.register_factory("apify_source_config_service", 
            lambda c: ApifySourceConfigService(
                apify_source_config_crud=c.get("apify_source_config_crud"),
                apify_service=c.get("apify_service"),
                session_factory=c.get("session_factory"),
                container=c
            )
        )
    except ImportError as e:
        # Log error but continue initialization
        logger.error(f"Error registering ApifySourceConfigService: {e}")


def register_flows(container):
    """Register flow classes in the container.
    
    Flow classes orchestrate end-to-end processes by coordinating multiple
    services, tools, and resources. This function registers all flow classes
    with appropriate lifecycle management.
    
    Args:
        container: The DI container instance
    """
    try:
        # Import all flow classes
        from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
        from local_newsifier.flows.news_pipeline import NewsPipelineFlow
        from local_newsifier.flows.trend_analysis_flow import NewsTrendAnalysisFlow as TrendAnalysisFlow
        from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
        from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
        
        # Check for headline trend flow
        try:
            from local_newsifier.flows.analysis.headline_trend_flow import HeadlineTrendFlow
            has_headline_trend_flow = True
        except ImportError:
            has_headline_trend_flow = False
        
        # EntityTrackingFlow with proper dependencies
        container.register_factory(
            "entity_tracking_flow",
            lambda c: EntityTrackingFlow(
                entity_service=c.get("entity_service"),
                entity_tracker=c.get("entity_tracker_tool"),
                entity_extractor=c.get("entity_extractor_tool"),
                context_analyzer=c.get("context_analyzer_tool"),
                entity_resolver=c.get("entity_resolver_tool"),
                session_factory=c.get("session_factory")
            ),
            scope=Scope.SINGLETON
        )
        
        # Register cleanup handler
        container.register_cleanup(
            "entity_tracking_flow",
            lambda f: f.cleanup() if hasattr(f, "cleanup") else None
        )
        
        # NewsPipelineFlow with proper dependencies
        container.register_factory(
            "news_pipeline_flow",
            lambda c: NewsPipelineFlow(
                article_service=c.get("article_service"),
                entity_service=c.get("entity_service"),
                web_scraper=c.get("web_scraper_tool"),
                file_writer=c.get("file_writer_tool"),
                entity_extractor=c.get("entity_extractor_tool"),
                context_analyzer=c.get("context_analyzer_tool"),
                entity_resolver=c.get("entity_resolver_tool"),
                session_factory=c.get("session_factory")
            ),
            scope=Scope.SINGLETON
        )
        
        # Register cleanup handler
        container.register_cleanup(
            "news_pipeline_flow",
            lambda f: f.cleanup() if hasattr(f, "cleanup") else None
        )
        
        # TrendAnalysisFlow with proper dependencies
        container.register_factory(
            "trend_analysis_flow",
            lambda c: TrendAnalysisFlow(
                analysis_service=c.get("analysis_service"),
                trend_reporter=c.get("trend_reporter_tool"),
                output_dir="trend_output"
            ),
            scope=Scope.SINGLETON
        )
        
        # PublicOpinionFlow with proper dependencies
        container.register_factory(
            "public_opinion_flow",
            lambda c: PublicOpinionFlow(
                sentiment_analyzer=c.get("sentiment_analyzer_tool"),
                sentiment_tracker=c.get("sentiment_tracker_tool"),
                opinion_visualizer=c.get("opinion_visualizer_tool"),
                session_factory=c.get("session_factory")
            ),
            scope=Scope.SINGLETON
        )
        
        # RSSScrapingFlow
        container.register_factory(
            "rss_scraping_flow",
            lambda c: RSSScrapingFlow(
                rss_feed_service=c.get("rss_feed_service"),
                article_service=c.get("article_service")
            ),
            scope=Scope.SINGLETON
        )
        
        # Register cleanup handler
        container.register_cleanup(
            "rss_scraping_flow",
            lambda f: f.cleanup() if hasattr(f, "cleanup") else None
        )
        
        # HeadlineTrendFlow (if available)
        if has_headline_trend_flow:
            container.register_factory(
                "headline_trend_flow",
                lambda c: HeadlineTrendFlow(
                    analysis_service=c.get("analysis_service"),
                    article_service=c.get("article_service"),
                    trend_analyzer=c.get("trend_analyzer_tool"),
                    trend_reporter=c.get("trend_reporter_tool"),
                    session_factory=c.get("session_factory")
                ),
                scope=Scope.SINGLETON
            )
    except ImportError as e:
        # Log error but continue initialization
        logger.error(f"Error registering flows: {e}")


# Create the singleton container instance
container = init_container()

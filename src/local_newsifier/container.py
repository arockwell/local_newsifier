"""
Container Initialization

This module initializes the dependency injection container with all services.
It provides a single instance of the container for the application to use.
"""

from local_newsifier.di_container import DIContainer, Scope
from local_newsifier.database.engine import SessionManager

# Import CRUD modules
from local_newsifier.crud import (
    article,
    analysis_result,
    entity,
    canonical_entity,
    entity_mention_context,
    entity_profile,
    entity_relationship,
    rss_feed,
    feed_processing_log,
)

# Import service classes
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.rss_feed_service import RSSFeedService

# Import flow classes if they exist
try:
    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.flows.trend_analysis_flow import TrendAnalysisFlow
    from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
    from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
    FLOWS_AVAILABLE = True
except ImportError:
    FLOWS_AVAILABLE = False

# Import tool classes if they exist 
try:
    from local_newsifier.tools.rss_parser import RSSParser
    from local_newsifier.tools.web_scraper import WebScraper
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


def init_container(environment="production"):
    """Initialize and configure the dependency injection container.
    
    This function creates a new container instance and registers all
    services and dependencies needed by the application.
    
    Args:
        environment: The environment to configure for ("production", "testing", "development")
    
    Returns:
        DIContainer: The initialized container
    """
    container = DIContainer()
    
    # Register CRUD modules
    container.register("article_crud", article)
    container.register("analysis_result_crud", analysis_result)
    container.register("entity_crud", entity)
    container.register("canonical_entity_crud", canonical_entity)
    container.register("entity_mention_context_crud", entity_mention_context)
    container.register("entity_profile_crud", entity_profile)
    container.register("entity_relationship_crud", entity_relationship)
    container.register("rss_feed_crud", rss_feed)
    container.register("feed_processing_log_crud", feed_processing_log)
    
    # Register session manager
    if environment == "testing":
        # For testing, we might want different session behavior
        container.register_factory("session_factory", 
                                lambda c: SessionManager)
    else:
        container.register_factory("session_factory", 
                                lambda c: SessionManager)
    
    # Register tools if available
    if TOOLS_AVAILABLE:
        container.register_factory("rss_parser", 
                                 lambda c: RSSParser())
        container.register_factory("web_scraper", 
                                 lambda c: WebScraper())
    
    # Register services - use factories to handle circular dependencies
    
    # ArticleService 
    container.register_factory("article_service", 
        lambda c: ArticleService(
            article_crud=c.get("article_crud"),
            analysis_result_crud=c.get("analysis_result_crud"),
            entity_service=c.get("entity_service"),  # Will be lazily loaded
            session_factory=c.get("session_factory")
        )
    )
    
    # RSSFeedService
    container.register_factory("rss_feed_service", 
        lambda c: RSSFeedService(
            rss_feed_crud=c.get("rss_feed_crud"),
            feed_processing_log_crud=c.get("feed_processing_log_crud"),
            article_service=c.get("article_service"),  # Will be lazily loaded
            session_factory=c.get("session_factory")
        )
    )
    
    # Register tools if available (expanded)
    if TOOLS_AVAILABLE:
        container.register_factory("rss_parser", 
                               lambda c: RSSParser())
        container.register_factory("web_scraper", 
                               lambda c: WebScraper())
        
        # Register analysis tools
        try:
            from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
            from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
            from local_newsifier.tools.resolution.entity_resolver import EntityResolver
            from local_newsifier.tools.entity_tracker_service import EntityTracker
            from local_newsifier.tools.file_writer import FileWriterTool
            
            # Additional analysis tools
            from local_newsifier.services.analysis_service import AnalysisService
            from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
            from local_newsifier.tools.sentiment_tracker import SentimentTracker
            from local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool
            from local_newsifier.tools.trend_reporter import TrendReporter
            
            # Register entity analysis tools
            container.register_factory("entity_extractor", lambda c: EntityExtractor())
            container.register_factory("context_analyzer", lambda c: ContextAnalyzer())
            container.register_factory("entity_resolver", lambda c: EntityResolver())
            container.register_factory("entity_tracker", lambda c: EntityTracker())
            container.register_factory("file_writer", lambda c: FileWriterTool(output_dir="output"))
            
            # Register sentiment and trend analysis tools
            container.register_factory("analysis_service", lambda c: AnalysisService())
            container.register_factory("sentiment_analyzer", lambda c: SentimentAnalysisTool(session=None))
            container.register_factory("sentiment_tracker", lambda c: SentimentTracker(session=None))
            container.register_factory("opinion_visualizer", lambda c: OpinionVisualizerTool(session=None))
            container.register_factory("trend_reporter", lambda c: TrendReporter(output_dir="trend_output"))
        except ImportError:
            # These tools are optional
            pass
    
    # Register flow services if available
    if FLOWS_AVAILABLE:
        # EntityTrackingFlow with proper dependencies
        container.register_factory("entity_tracking_flow",
            lambda c: EntityTrackingFlow(
                entity_service=c.get("entity_service"),
                entity_tracker=c.get("entity_tracker"),
                entity_extractor=c.get("entity_extractor"),
                context_analyzer=c.get("context_analyzer"),
                entity_resolver=c.get("entity_resolver"),
                session_factory=c.get("session_factory")
            ))
        
        # NewsPipelineFlow with proper dependencies
        container.register_factory("news_pipeline_flow",
            lambda c: NewsPipelineFlow(
                article_service=c.get("article_service"),
                entity_service=c.get("entity_service"),
                web_scraper=c.get("web_scraper"),
                file_writer=c.get("file_writer"),
                entity_extractor=c.get("entity_extractor"),
                context_analyzer=c.get("context_analyzer"),
                entity_resolver=c.get("entity_resolver"),
                session_factory=c.get("session_factory")
            ))
        
        # TrendAnalysisFlow with proper dependencies
        container.register_factory("trend_analysis_flow",
            lambda c: TrendAnalysisFlow(
                analysis_service=c.get("analysis_service"),
                trend_reporter=c.get("trend_reporter"),
                output_dir="trend_output"
            ))
        
        # PublicOpinionFlow with proper dependencies
        container.register_factory("public_opinion_flow",
            lambda c: PublicOpinionFlow(
                sentiment_analyzer=c.get("sentiment_analyzer"),
                sentiment_tracker=c.get("sentiment_tracker"),
                opinion_visualizer=c.get("opinion_visualizer"),
                session_factory=c.get("session_factory")
            ))
        
        # RSSScrapingFlow
        container.register_factory("rss_scraping_flow",
            lambda c: RSSScrapingFlow(
                rss_feed_service=c.get("rss_feed_service"),
                article_service=c.get("article_service")
            ))
    
    # Register parameterized factories
    container.register_factory_with_params("entity_service_with_params",
        lambda c, **kwargs: kwargs.get("entity_service") or c.get("entity_service")
    )
    
    container.register_factory_with_params("article_service_with_params",
        lambda c, **kwargs: kwargs.get("article_service") or c.get("article_service")
    )
    
    # Environment-specific configurations
    if environment == "development":
        # Development-specific registrations
        pass
    elif environment == "testing":
        # Testing-specific registrations
        pass
    
    return container


# Create the singleton container instance
container = init_container()

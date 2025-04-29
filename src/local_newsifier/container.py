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
from local_newsifier.services.apify_service import ApifyService


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
    
    # Register Core Tools
    register_core_tools(container)
    
    # Register Analysis Tools
    register_analysis_tools(container)
    
    # Register Entity Tools
    register_entity_tools(container)
    
    # Register services - use factories to handle circular dependencies
    register_services(container)
    
    # Register flow services
    register_flows(container)
    
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


def register_core_tools(container):
    """Register core tool classes in the container.
    
    Args:
        container: The DI container instance
    """
    # Import core tools
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
        
        # Register rss_parser_tool with configurable cache_file
        container.register_factory_with_params(
            "rss_parser_tool", 
            lambda c, **kwargs: RSSParser(
                cache_file=kwargs.get("cache_file")
            )
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
        print(f"Error registering core tools: {e}")


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
        print(f"Error registering analysis tools: {e}")


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
        print(f"Error registering entity tools: {e}")


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
    
    # ApifyService
    container.register_factory("apify_service", 
        lambda c: ApifyService()
    )


def register_flows(container):
    """Register flow classes in the container.
    
    Args:
        container: The DI container instance
    """
    try:
        # Import flow classes
        from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
        from local_newsifier.flows.news_pipeline import NewsPipelineFlow
        from local_newsifier.flows.trend_analysis_flow import TrendAnalysisFlow
        from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
        from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
        
        # EntityTrackingFlow with proper dependencies
        container.register_factory("entity_tracking_flow",
            lambda c: EntityTrackingFlow(
                entity_service=c.get("entity_service"),
                entity_tracker=c.get("entity_tracker_tool"),
                entity_extractor=c.get("entity_extractor_tool"),
                context_analyzer=c.get("context_analyzer_tool"),
                entity_resolver=c.get("entity_resolver_tool"),
                session_factory=c.get("session_factory")
            ))
        
        # NewsPipelineFlow with proper dependencies
        container.register_factory("news_pipeline_flow",
            lambda c: NewsPipelineFlow(
                article_service=c.get("article_service"),
                entity_service=c.get("entity_service"),
                web_scraper=c.get("web_scraper_tool"),
                file_writer=c.get("file_writer_tool"),
                entity_extractor=c.get("entity_extractor_tool"),
                context_analyzer=c.get("context_analyzer_tool"),
                entity_resolver=c.get("entity_resolver_tool"),
                session_factory=c.get("session_factory")
            ))
        
        # TrendAnalysisFlow with proper dependencies
        container.register_factory("trend_analysis_flow",
            lambda c: TrendAnalysisFlow(
                analysis_service=c.get("analysis_service"),
                trend_reporter=c.get("trend_reporter_tool"),
                output_dir="trend_output"
            ))
        
        # PublicOpinionFlow with proper dependencies
        container.register_factory("public_opinion_flow",
            lambda c: PublicOpinionFlow(
                sentiment_analyzer=c.get("sentiment_analyzer_tool"),
                sentiment_tracker=c.get("sentiment_tracker_tool"),
                opinion_visualizer=c.get("opinion_visualizer_tool"),
                session_factory=c.get("session_factory")
            ))
        
        # RSSScrapingFlow
        container.register_factory("rss_scraping_flow",
            lambda c: RSSScrapingFlow(
                rss_feed_service=c.get("rss_feed_service"),
                article_service=c.get("article_service")
            ))
    except ImportError:
        # These flows are optional
        pass


# Create the singleton container instance
container = init_container()

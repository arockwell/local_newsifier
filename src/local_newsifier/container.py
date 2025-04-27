"""
Container Initialization

This module initializes the dependency injection container with all services.
It provides a single instance of the container for the application to use.
"""

from local_newsifier.di_container import DIContainer
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


def init_container():
    """Initialize and configure the dependency injection container.
    
    This function creates a new container instance and registers all
    services and dependencies needed by the application.
    
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
    
    # Register session factory
    container.register("session_factory", lambda: SessionManager())
    
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
    
    # Additional services will be added here as needed
    
    return container


# Create the singleton container instance
container = init_container()

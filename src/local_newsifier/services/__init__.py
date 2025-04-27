"""Services module for business logic coordination."""

# Direct imports for developers using this package
# flake8: noqa F401
from .article_service import ArticleService, article_service
from .entity_service import EntityService
from .news_pipeline_service import NewsPipelineService
from .rss_feed_service import rss_feed_service

# Global placeholder for entity_service, to be set later
entity_service = None

# Function to register entity_service, avoiding circular imports
def register_entity_service(service_instance):
    """Register entity_service to avoid circular imports.
    This will be called from tasks.py after the service is created.
    """
    global entity_service
    entity_service = service_instance

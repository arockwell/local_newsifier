"""Services module for business logic coordination."""

# Direct imports for developers using this package
# flake8: noqa F401
from .article_service import ArticleService, article_service
from .entity_service import EntityService
from .news_pipeline_service import NewsPipelineService
from .rss_feed_service import rss_feed_service

# For backward compatibility, also directly expose the entity_service instance 
from local_newsifier.tasks import entity_service

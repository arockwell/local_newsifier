"""Services module for business logic coordination."""

# Direct imports for developers using this package
# flake8: noqa F401
from .article_service import ArticleService
from .entity_service import EntityService
from .news_pipeline_service import NewsPipelineService
from .rss_feed_service import rss_feed_service

# Import instances from tasks to maintain backward compatibility
from local_newsifier.tasks import article_service, entity_service

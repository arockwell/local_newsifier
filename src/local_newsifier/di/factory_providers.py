"""Factory providers for resolving circular dependencies."""

import logging
from typing import Annotated, Any, Callable, TypeVar, TYPE_CHECKING

from fastapi import Depends
from fastapi_injectable import injectable

# Type to represent a factory function for a specific service type
T = TypeVar("T")
ServiceFactory = Callable[[], T]

if TYPE_CHECKING:
    from local_newsifier.services.article_service import ArticleService
    from local_newsifier.services.entity_service import EntityService
    from local_newsifier.services.rss_feed_service import RSSFeedService

logger = logging.getLogger(__name__)


@injectable(use_cache=False)
def get_entity_service_factory() -> ServiceFactory["EntityService"]:
    """Factory function for EntityService to break circular dependencies."""
    def factory() -> "EntityService":
        from local_newsifier.di.providers import get_entity_service
        return get_entity_service()
    return factory


@injectable(use_cache=False)
def get_article_service_factory() -> ServiceFactory["ArticleService"]:
    """Factory function for ArticleService to break circular dependencies."""
    def factory() -> "ArticleService":
        from local_newsifier.di.providers import get_article_service
        return get_article_service()
    return factory


@injectable(use_cache=False)
def get_rss_feed_service_factory() -> ServiceFactory["RSSFeedService"]:
    """Factory function for RSSFeedService to break circular dependencies."""
    def factory() -> "RSSFeedService":
        from local_newsifier.di.providers import get_rss_feed_service
        return get_rss_feed_service()
    return factory
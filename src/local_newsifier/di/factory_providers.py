"""
Factory providers for resolving circular dependencies.

This module provides factory functions that return callables which create 
service instances on demand. These factories are used to break circular
dependencies between services by deferring the actual service instantiation
until runtime.

Usage:
    # Get a factory that can create EntityService instances
    entity_service_factory = get_entity_service_factory()
    
    # Later, create an actual EntityService instance when needed
    entity_service = entity_service_factory()
"""

import logging
from typing import Annotated, Any, Callable, Optional, TypeVar, TYPE_CHECKING

from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

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
    """Provide a factory function for EntityService.
    
    This factory allows lazy creation of EntityService instances,
    which helps break circular dependencies with ArticleService.
    The factory function uses runtime imports to ensure no
    circular imports occur during module loading.
    
    Returns:
        A factory function that creates and returns an EntityService instance
    """
    def factory() -> "EntityService":
        # Runtime import to avoid circular imports
        from local_newsifier.di.providers import get_entity_service
        
        # Create a fresh instance of EntityService
        return get_entity_service()
    
    return factory


@injectable(use_cache=False)
def get_article_service_factory() -> ServiceFactory["ArticleService"]:
    """Provide a factory function for ArticleService.
    
    This factory allows lazy creation of ArticleService instances,
    which helps break circular dependencies with EntityService and
    RSSFeedService. The factory function uses runtime imports to
    ensure no circular imports occur during module loading.
    
    Returns:
        A factory function that creates and returns an ArticleService instance
    """
    def factory() -> "ArticleService":
        # Runtime import to avoid circular imports
        from local_newsifier.di.providers import get_article_service
        
        # Create a fresh instance of ArticleService
        return get_article_service()
    
    return factory


@injectable(use_cache=False)
def get_rss_feed_service_factory() -> ServiceFactory["RSSFeedService"]:
    """Provide a factory function for RSSFeedService.
    
    This factory allows lazy creation of RSSFeedService instances,
    which helps break circular dependencies with ArticleService.
    The factory function uses runtime imports to ensure no
    circular imports occur during module loading.
    
    Returns:
        A factory function that creates and returns a RSSFeedService instance
    """
    def factory() -> "RSSFeedService":
        # Runtime import to avoid circular imports
        from local_newsifier.di.providers import get_rss_feed_service
        
        # Create a fresh instance of RSSFeedService
        return get_rss_feed_service()
    
    return factory


# Factory for creating services with custom parameters
@injectable(use_cache=False)
def get_parameterized_service_factory(
    service_name: str,
    session: Annotated[Optional[Session], Depends()] = None
) -> Callable[..., Any]:
    """Provide a factory function for creating services with custom parameters.
    
    This is a more general-purpose factory that can create various services
    by name, with optional parameters. This is useful for cases where
    the same service type needs different parameters in different contexts.
    
    Args:
        service_name: The name of the service provider function to use
        session: Optional database session to inject
        
    Returns:
        A factory function that creates and returns the requested service
    """
    def factory(**kwargs: Any) -> Any:
        # Import the appropriate provider based on service name
        if service_name == "article_service":
            from local_newsifier.di.providers import get_article_service
            provider = get_article_service
        elif service_name == "entity_service":
            from local_newsifier.di.providers import get_entity_service
            provider = get_entity_service
        elif service_name == "rss_feed_service":
            from local_newsifier.di.providers import get_rss_feed_service
            provider = get_rss_feed_service
        else:
            raise ValueError(f"Unknown service name: {service_name}")
        
        # Pass along the session and any additional parameters
        params = kwargs.copy()
        if session is not None:
            params["session"] = session
            
        # Create the service with the given parameters
        # Note: This assumes the provider can handle these parameters,
        # which may require updates to the provider implementations
        return provider(**params)
    
    return factory
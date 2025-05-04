"""Proof of concept for fastapi-injectable migration.

This module demonstrates how services would be defined and used with 
fastapi-injectable. This is for planning purposes and doesn't use the
actual fastapi-injectable package yet due to version constraints.
"""

import inspect
from typing import Annotated, Dict, List, Optional, Type, TypeVar

from fastapi import Depends, FastAPI, Path
from pydantic import BaseModel
from sqlmodel import Session

from local_newsifier.di_adapter import adapter
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.entity_service import EntityService


# Mock fastapi-injectable decorators and utilities
def injectable(use_cache: bool = True):
    """Mock decorator for marking classes as injectable.
    
    Args:
        use_cache: Whether to reuse the same instance for identical dependency requests
            - True: Reuse the same instance (singleton-like behavior)
            - False: Create a new instance each time (transient-like behavior)
            
    Returns:
        Decorator function
    """
    def decorator(cls):
        # In a real implementation, this would register the class
        # with fastapi-injectable
        setattr(cls, "__injectable_use_cache__", use_cache)
        return cls
    
    return decorator


def Inject(service_type: Optional[Type] = None):
    """Mock function for injecting dependencies.
    
    Args:
        service_type: Optional explicit service type
        
    Returns:
        Dependency function
    """
    def get_dependency(service_type: Type):
        def _get_service():
            # In a real implementation, this would get the service
            # from fastapi-injectable's container
            # For now, we'll use our adapter to get from DIContainer
            return adapter.get_service(service_type)
        
        return _get_service
    
    if service_type is not None:
        return Depends(get_dependency(service_type))
    
    # If called without arguments, infer type from annotation
    frame = inspect.currentframe().f_back
    arg_name = next(iter(frame.f_locals))
    arg_type = frame.f_locals.get("__annotations__", {}).get(arg_name)
    
    if arg_type is None:
        raise ValueError("Cannot determine service type for injection")
        
    return Depends(get_dependency(arg_type))


# Example of how services would be defined with @injectable
@injectable(use_cache=False)  # Create new instance for each injection
class ExampleArticleService:
    """Example of how ArticleService would be defined with fastapi-injectable.
    
    Uses use_cache=False to ensure fresh instances for each injection,
    as this service interacts with the database.
    """
    
    def __init__(
        self, 
        entity_service: Annotated[EntityService, Inject()]
    ):
        self.entity_service = entity_service
        
    def get_article(self, article_id: int) -> Dict:
        """Get article by ID.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Article data
        """
        # Implementation would be the same as the current ArticleService
        return {"id": article_id, "title": "Example Article"}


# Example FastAPI route using the injectable pattern
def example_api_setup(app: FastAPI):
    """Example setup for FastAPI routes with fastapi-injectable.
    
    Args:
        app: FastAPI application
    """
    @app.get("/articles/{article_id}")
    def get_article(
        article_id: int = Path(...),
        article_service: Annotated[ArticleService, Depends()]  # Using standard FastAPI Depends
    ):
        """Get article by ID.
        
        Args:
            article_id: ID of the article
            article_service: Injected ArticleService
            
        Returns:
            Article data
        """
        return article_service.get_article(article_id)
    
    
    @app.get("/session-example")
    def session_example(
        session: Annotated[Session, Depends()]  # Using standard FastAPI Depends
    ):
        """Example using an injected session.
        
        Args:
            session: Injected database session
            
        Returns:
            Success message
        """
        # Use session for database operations
        return {"message": "Session injected successfully"}
    
    
    # Example of a more complex scenario with multiple dependencies
    class ArticleFilter(BaseModel):
        """Filter parameters for articles."""
        
        from_date: Optional[str] = None
        to_date: Optional[str] = None
        keywords: Optional[List[str]] = None
    
    
    @app.post("/articles/filter")
    def filter_articles(
        filter_params: ArticleFilter,
        article_service: Annotated[ArticleService, Depends()],
        entity_service: Annotated[EntityService, Depends()]
    ):
        """Filter articles by parameters.
        
        Args:
            filter_params: Filter parameters
            article_service: Injected ArticleService
            entity_service: Injected EntityService
            
        Returns:
            Filtered articles
        """
        # Use both services together
        return {"message": "Articles filtered"}
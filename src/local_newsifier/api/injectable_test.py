"""Test module for fastapi-injectable integration with the API.

This module demonstrates how to use fastapi-injectable with
the existing API architecture for smooth migration.
"""

from typing import Annotated, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi_injectable import injectable, get_injected_obj

from local_newsifier.fastapi_injectable_adapter import inject_adapter
from local_newsifier.models.article import Article
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.entity_service import EntityService
from local_newsifier.container import container as di_container

# Create a router for injectable test endpoints
router = APIRouter(
    prefix="/injectable",
    tags=["injectable"],
    responses={404: {"description": "Not found"}},
)

# Create factories for our services
@injectable(use_cache=True)
def get_article_service():
    """Get the article service from DIContainer."""
    return di_container.get("article_service")

@injectable(use_cache=True)
def get_entity_service():
    """Get the entity service from DIContainer."""
    return di_container.get("entity_service")

# Create a new injectable service that uses our existing services
@injectable(use_cache=True)
def get_article_info_service(
    article_service: Annotated[ArticleService, Depends(get_article_service)],
    entity_service: Annotated[EntityService, Depends(get_entity_service)],
):
    """Get a service that provides article statistics and information."""
    class ArticleInfoService:
        """Service that provides article statistics and information."""
        
        def __init__(self, article_service, entity_service):
            """Initialize with injected dependencies."""
            self.article_service = article_service
            self.entity_service = entity_service
        
        def get_service_info(self) -> Dict:
            """Get information about the services."""
            return {
                "article_service": self.article_service.__class__.__name__,
                "entity_service": self.entity_service.__class__.__name__,
            }
        
        def get_article_stats(self) -> Dict:
            """Get article statistics."""
            # In a real implementation, this would fetch actual stats
            # For this test, we'll just return some placeholder data
            return {
                "total_articles": 100,
                "articles_with_entities": 95,
                "total_entities": 500,
                "entity_types": ["PERSON", "ORGANIZATION", "LOCATION"],
            }
    
    return ArticleInfoService(article_service, entity_service)

# Create routes that use the injectable service
@router.get("/info", response_model=Dict)
@inject_adapter
async def get_injectable_info(
    article_info_service: Annotated[object, Depends(get_article_info_service)],
):
    """Get information about the injectable services."""
    try:
        service_info = article_info_service.get_service_info()
        return {
            "success": True,
            "message": "Successfully used services via fastapi-injectable",
            "service_info": service_info,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/stats", response_model=Dict)
@inject_adapter
async def get_article_stats(
    article_info_service: Annotated[object, Depends(get_article_info_service)],
):
    """Get article statistics using the injectable service."""
    try:
        stats = article_info_service.get_article_stats()
        return {
            "success": True,
            "message": "Successfully retrieved article statistics",
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Simple test endpoints that directly use the DIContainer
@router.get("/direct-info", response_model=Dict)
async def get_direct_info():
    """Get information about services directly from DIContainer."""
    try:
        article_service = di_container.get("article_service")
        entity_service = di_container.get("entity_service")
        
        return {
            "success": True,
            "message": "Successfully got services directly from DIContainer",
            "service_info": {
                "article_service": article_service.__class__.__name__,
                "entity_service": entity_service.__class__.__name__,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
#!/usr/bin/env python
"""Test script for fastapi-injectable adapter.

This script creates a test FastAPI application that uses the
fastapi-injectable adapter to demonstrate how to migrate
from the current DIContainer to fastapi-injectable.
"""

import logging
import sys
import os
from pathlib import Path
import uvicorn
from typing import Annotated, Dict, List, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from fastapi import FastAPI, Depends, HTTPException
    from fastapi_injectable import injectable, get_injected_obj, register_app
except ImportError as e:
    print(f"Error importing FastAPI or fastapi-injectable: {e}")
    print("Make sure fastapi-injectable is installed with: poetry add fastapi-injectable")
    sys.exit(1)

try:
    from local_newsifier.container import container as di_container
    from local_newsifier.fastapi_injectable_adapter import (
        register_with_injectable, 
        inject_adapter,
        register_container_service
    )
    from local_newsifier.models.article import Article
    from local_newsifier.services.article_service import ArticleService
    from local_newsifier.services.entity_service import EntityService
except ImportError as e:
    print(f"Error importing local_newsifier modules: {e}")
    print("Make sure you're running this script from the project root")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create a test FastAPI app
app = FastAPI(
    title="FastAPI Injectable Test",
    description="Test application for fastapi-injectable adapter",
)

# Register the FastAPI app with fastapi-injectable
logger.info("Registering app with fastapi-injectable")

# Register core services from DIContainer
logger.info("Registering DIContainer services with fastapi-injectable")
register_container_service("article_service")
register_container_service("entity_service")

# Create service factories using injectable
@injectable(use_cache=True)
def get_article_service_factory():
    """Get the article service from DIContainer."""
    return di_container.get("article_service")

@injectable(use_cache=True)
def get_entity_service_factory():
    """Get the entity service from DIContainer."""
    return di_container.get("entity_service")

# Create a new injectable service factory
@injectable(use_cache=True)
def get_test_service(
    article_service: Annotated[ArticleService, Depends(get_article_service_factory)],
):
    """Factory for TestService."""
    class TestService:
        """Test service that uses both DIContainer and fastapi-injectable services."""
        
        def __init__(self, article_service):
            """Initialize with injected dependencies."""
            self.article_service = article_service
            
        def get_service_info(self) -> Dict:
            """Get information about the services."""
            return {
                "article_service": self.article_service.__class__.__name__,
                "article_service_from": "fastapi-injectable",
            }
    
    return TestService(article_service)

# Register routes that use both DI systems
@app.get("/test/di", response_model=Dict)
@inject_adapter
async def test_di(
    test_service: Annotated[object, Depends(get_test_service)],
):
    """Test endpoint that uses services from both DIContainer and fastapi-injectable."""
    try:
        service_info = test_service.get_service_info()
        
        # Also test getting a service directly from DIContainer
        entity_service = di_container.get("entity_service")
        
        return {
            "success": True,
            "message": "Successfully used both DI systems",
            "service_info": service_info,
            "entity_service_type": entity_service.__class__.__name__,
        }
    except Exception as e:
        logger.exception("Error in test_di endpoint")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/test/article-service", response_model=Dict)
@inject_adapter
async def test_article_service(
    article_service: Annotated[ArticleService, Depends(get_article_service_factory)],
):
    """Test endpoint that uses the article service from fastapi-injectable."""
    try:
        # Get article service properties
        return {
            "success": True,
            "message": "Successfully used article service from fastapi-injectable",
            "article_service_type": article_service.__class__.__name__,
            "has_article_crud": hasattr(article_service, "article_crud"),
            "has_analysis_result_crud": hasattr(article_service, "analysis_result_crud"),
        }
    except Exception as e:
        logger.exception("Error in test_article_service endpoint")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/test/container", response_model=Dict)
async def test_container():
    """Test endpoint that uses services directly from DIContainer."""
    try:
        article_service = di_container.get("article_service")
        entity_service = di_container.get("entity_service")
        
        return {
            "success": True,
            "message": "Successfully used services directly from DIContainer",
            "article_service_type": article_service.__class__.__name__,
            "entity_service_type": entity_service.__class__.__name__,
        }
    except Exception as e:
        logger.exception("Error in test_container endpoint")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint showing test links."""
    return {
        "message": "FastAPI Injectable Test Application",
        "test_endpoints": [
            {"path": "/test/di", "description": "Test both DI systems"},
            {"path": "/test/article-service", "description": "Test article service from fastapi-injectable"},
            {"path": "/test/container", "description": "Test DIContainer directly"},
        ]
    }

async def startup():
    """Initialize the application."""
    logger.info("Initializing fastapi-injectable")
    await register_app(app)
    logger.info("fastapi-injectable initialized")

def main():
    """Run the test application."""
    logger.info("Starting test application for fastapi-injectable adapter")
    print("Available at http://127.0.0.1:8000")
    print("Endpoints:")
    print("  - /test/di - Test both DI systems")
    print("  - /test/article-service - Test article service from fastapi-injectable")
    print("  - /test/container - Test DIContainer directly")
    
    # Initialize fastapi-injectable
    import asyncio
    asyncio.run(startup())
    
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
        )
    except Exception as e:
        logger.exception(f"Error running uvicorn server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
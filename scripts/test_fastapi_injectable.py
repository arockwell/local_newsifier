#!/usr/bin/env python
"""Test script for fastapi-injectable integration.

This unified test script provides comprehensive testing for:
1. FastAPI upgrade compatibility
2. fastapi-injectable adapter functionality
3. Integration with the DIContainer

Run modes:
- Default: Run all tests and exit
- Server: Run as a standalone test server (--server)
- API Integration: Test with main API integration (--api-integration)
"""

import logging
import sys
import os
from pathlib import Path
import uvicorn
import argparse
from typing import Annotated, Dict, List, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from fastapi import FastAPI, Depends, HTTPException, Path, Request
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient
    from fastapi_injectable import injectable, get_injected_obj, register_app
    from sqlmodel import Session
except ImportError as e:
    print(f"Error importing FastAPI or fastapi-injectable: {e}")
    print("Make sure fastapi-injectable is installed with: poetry add fastapi-injectable")
    sys.exit(1)

try:
    from local_newsifier.container import container as di_container
    from local_newsifier.api.dependencies import get_session
    from local_newsifier.database.engine import SessionManager
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
    description="Test application for fastapi-injectable integration",
)

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

# ----- BASIC FASTAPI UPGRADE TESTS -----

@app.get("/")
async def root():
    """Root endpoint showing test links."""
    return {
        "message": "FastAPI Injectable Test Application",
        "test_endpoints": [
            {"path": "/upgrade/basic", "description": "Test basic FastAPI functionality"},
            {"path": "/upgrade/session", "description": "Test session dependency"},
            {"path": "/upgrade/container", "description": "Test container access"},
            {"path": "/upgrade/error", "description": "Test error handling"},
            {"path": "/test/di", "description": "Test both DI systems"},
            {"path": "/test/article-service", "description": "Test article service from fastapi-injectable"},
            {"path": "/test/container", "description": "Test DIContainer directly"},
        ]
    }

@app.get("/upgrade/basic")
async def basic_test():
    """Basic endpoint for testing FastAPI upgrade."""
    return {"message": "FastAPI upgrade test successful"}

@app.get("/upgrade/session")
async def session_test(session: Session = Depends(get_session)):
    """Test session dependency."""
    # Just verify we can get a session
    return {"message": "Session dependency works"}

@app.get("/upgrade/container")
async def container_test():
    """Test container access."""
    # Try to get a service from the container
    session_factory = di_container.get("session_factory")
    if session_factory is None:
        raise HTTPException(status_code=500, detail="Container not working")
    return {"message": "Container access works"}

@app.get("/upgrade/error")
async def error_test():
    """Test error handling."""
    raise HTTPException(status_code=404, detail="Test error handling")

# ----- INJECTABLE ADAPTER TESTS -----

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

async def startup():
    """Initialize the application."""
    logger.info("Initializing fastapi-injectable")
    await register_app(app)
    logger.info("fastapi-injectable initialized")

def run_tests():
    """Run basic tests on the FastAPI app."""
    client = TestClient(app)
    
    # Test FastAPI upgrade endpoints
    print("\n----- Testing FastAPI Upgrade Compatibility -----")
    
    # Test root endpoint
    response = client.get("/upgrade/basic")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI upgrade test successful"}
    print("✓ Basic endpoint test passed")
    
    # Test session dependency
    response = client.get("/upgrade/session")
    assert response.status_code == 200
    assert response.json() == {"message": "Session dependency works"}
    print("✓ Session dependency test passed")
    
    # Test container access
    response = client.get("/upgrade/container")
    assert response.status_code == 200
    assert response.json() == {"message": "Container access works"}
    print("✓ Container access test passed")
    
    # Test error handling
    response = client.get("/upgrade/error")
    assert response.status_code == 404
    assert response.json() == {"detail": "Test error handling"}
    print("✓ Error handling test passed")
    
    # Test fastapi-injectable adapter endpoints
    print("\n----- Testing fastapi-injectable Adapter -----")
    
    # Test DI endpoint
    response = client.get("/test/di")
    assert response.status_code == 200
    assert response.json()["success"] == True
    print("✓ DI integration test passed")
    
    # Test article service endpoint
    response = client.get("/test/article-service")
    assert response.status_code == 200
    assert response.json()["success"] == True
    print("✓ Article service test passed")
    
    # Test container endpoint
    response = client.get("/test/container")
    assert response.status_code == 200
    assert response.json()["success"] == True
    print("✓ Container access test passed")
    
    print("\nAll tests passed! FastAPI upgrade and fastapi-injectable adapter are working correctly.")

def test_api_integration():
    """Test the integration with the main API."""
    # This function would test against a running API instance
    # In this simplified version, we'll just provide instructions
    print("\n----- Testing API Integration -----")
    print("To test API integration:")
    print("1. Start the API with: poetry run uvicorn local_newsifier.api.main:app --reload")
    print("2. Test the injectable endpoints with:")
    print("   curl http://localhost:8000/injectable/info")
    print("   curl http://localhost:8000/injectable/stats")
    print("3. Verify regular endpoints still work:")
    print("   curl http://localhost:8000/health")
    print("   curl http://localhost:8000/config")

def main():
    """Run the test application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test fastapi-injectable integration")
    parser.add_argument(
        "--server", 
        action="store_true", 
        help="Run as a standalone test server"
    )
    parser.add_argument(
        "--api-integration", 
        action="store_true", 
        help="Test integration with main API"
    )
    args = parser.parse_args()
    
    if args.server:
        # Run as a server
        logger.info("Starting test server for fastapi-injectable integration")
        print("Available at http://127.0.0.1:8000")
        print("Endpoints:")
        print("  - / - Root with endpoint list")
        print("  - /upgrade/* - Test FastAPI upgrade compatibility")
        print("  - /test/* - Test fastapi-injectable adapter")
        
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
    elif args.api_integration:
        # Test API integration
        test_api_integration()
    else:
        # Run tests
        # Initialize fastapi-injectable
        import asyncio
        asyncio.run(startup())
        run_tests()

if __name__ == "__main__":
    main()
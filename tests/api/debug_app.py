"""Script to debug FastAPI app routes and dependencies."""

import logging
import sys
from fastapi import FastAPI, Depends, Path, Body
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("debug_app")

# Create a test FastAPI app
app = FastAPI()
from local_newsifier.api.routers import articles

# Include the articles router
app.include_router(articles.router)

# Create a test client
client = TestClient(app)

# Print all routes
logger.info("Available routes:")
for route in app.routes:
    if isinstance(route, APIRoute):
        logger.info(f"Route: {route.path} - Methods: {route.methods}")
        logger.info(f"  Dependencies: {[d for d in route.dependencies]}")
        logger.info(f"  Endpoint: {route.endpoint.__name__}")
        logger.info(f"  Response model: {getattr(route, 'response_model', None)}")

# Test article creation
article_data = {
    "title": "Test Debug Article",
    "content": "This is a test article content for debugging.",
    "url": "https://example.com/test-debug-article",
    "source": "test_source",
    "status": "new",
    "published_at": datetime.now().isoformat(),
    "scraped_at": datetime.now().isoformat()
}

logger.info(f"Sending POST request to /articles/ with data: {article_data}")
response = client.post("/articles/", json=article_data)
logger.info(f"Response status: {response.status_code}")
logger.info(f"Response headers: {response.headers}")
logger.info(f"Response body: {response.content.decode('utf-8')}")

# Log all the details about the endpoint
for route in app.routes:
    if isinstance(route, APIRoute) and route.path == "/articles/":
        logger.info(f"POST /articles/ endpoint details:")
        logger.info(f"  Endpoint function: {route.endpoint}")
        logger.info(f"  Dependencies: {route.dependencies}")
        logger.info(f"  Response model: {getattr(route, 'response_model', None)}")
        
        # Get function signature
        import inspect
        sig = inspect.signature(route.endpoint)
        logger.info(f"  Function signature: {sig}")
        
        # Get parameter details
        for name, param in sig.parameters.items():
            logger.info(f"    Parameter {name}: {param.annotation}")

# Print article model from Pydantic
from local_newsifier.api.routers.articles import ArticleCreate
logger.info(f"ArticleCreate model fields: {ArticleCreate.model_fields}")
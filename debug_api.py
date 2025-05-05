"""Standalone script to test article API."""

import os
import sys
import json
import logging
from datetime import datetime, timezone
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    stream=sys.stderr,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger("debug_api")

# We need to test with the real API
# Start FastAPI server in separate terminal with:
# poetry run uvicorn src.local_newsifier.api.main:app --reload

def test_create_article():
    """Test creating an article via direct API call."""
    
    # Test data
    article_data = {
        "title": "Test Article",
        "content": "This is a test article content.",
        "url": "https://example.com/test-article",
        "source": "test_source",
        "status": "new",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Sending data: {json.dumps(article_data, indent=2)}")
    
    # Make the API call
    try:
        response = requests.post("http://localhost:8000/articles/", json=article_data)
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Headers: {response.headers}")
        
        # Try to parse as JSON
        try:
            content = response.json()
            logger.info(f"Response content (JSON): {json.dumps(content, indent=2)}")
        except Exception:
            logger.info(f"Response content (text): {response.text}")
            
        return response
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        logger.exception(e)
        return None

if __name__ == "__main__":
    logger.info("Starting API test")
    result = test_create_article()
    logger.info("Test complete")
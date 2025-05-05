"""Test file for debugging article API issues."""

from datetime import datetime, timezone
import json

from fastapi import status
from fastapi.testclient import TestClient

def test_debug_create_article(client: TestClient, db_session):
    """Debug test to see detailed error output."""
    article_data = {
        "title": "Test Article",
        "content": "This is a test article content.",
        "url": "https://example.com/test-article",
        "source": "test_source",
        "status": "new",
        # Use current date in ISO format for published_at
        "published_at": datetime.now(timezone.utc).isoformat(),
        # Add scraped_at which is required but not in the model defaults
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }

    # Send request
    response = client.post("/articles/", json=article_data)
    
    # Print debug info
    print("\n\n========== DEBUG OUTPUT ==========")
    print(f"Status Code: {response.status_code}")
    
    # Print headers
    print("\n--- Headers ---")
    for key, value in response.headers.items():
        print(f"{key}: {value}")
    
    # Print content
    print("\n--- Content ---")
    try:
        content_json = json.loads(response.content)
        print(json.dumps(content_json, indent=2))
    except:
        print(response.content.decode('utf-8'))
        
    # Print request data
    print("\n--- Request Data ---")
    print(json.dumps(article_data, indent=2))
    print("======== END DEBUG OUTPUT ========\n\n")
    
    # This will fail, but we'll see the output
    assert response.status_code == status.HTTP_201_CREATED
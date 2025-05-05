"""Debug script to test article creation endpoint."""

from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from local_newsifier.api.main import app

# Create a database engine for testing
sqlite_file = "file:memdb1?mode=memory&cache=shared&uri=true"
engine = create_engine(sqlite_file)

# Create tables for testing
SQLModel.metadata.create_all(engine)

# Create a database session for testing
with Session(engine) as db_session:
    # Create a test client
    client = TestClient(app)
    
    # Create test article data
    article_data = {
        "title": "Test Article",
        "content": "This is a test article content.",
        "url": "https://example.com/test-article",
        "source": "test_source",
        "status": "new",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Send the request
    response = client.post("/articles/", json=article_data)
    
    # Print detailed debug information
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Content: {response.content.decode('utf-8')}")
    print(f"Request Data: {article_data}")
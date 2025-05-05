"""Debug script for the by_url endpoint."""

import sys
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from local_newsifier.api.routers import articles
from local_newsifier.models.article import Article
from sqlmodel import Session, SQLModel, create_engine

# Create a database engine for testing
sqlite_file = "sqlite:///:memory:"
engine = create_engine(sqlite_file)

# Create tables for testing
SQLModel.metadata.create_all(engine)

# Create a fresh FastAPI app for testing
app = FastAPI()

# Include article router
app.include_router(articles.router)

# Print all routes
print("Available routes:")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"{route.path} - {route.methods}")

# Create a test client
client = TestClient(app)

# Create a session for database operations
with Session(engine) as session:
    # Use a unique timestamp to avoid duplicate URL errors
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    url = f"https://example.com/test-article-{timestamp}"
    
    # Create an article
    article = Article(
        title="Test Article",
        content="This is a test article content.",
        url=url,
        source="test_source",
        status="new",
        published_at=datetime.now(timezone.utc),
        scraped_at=datetime.now(timezone.utc),
    )
    session.add(article)
    session.commit()
    
    # Test retrieving it by URL as query parameter
    print(f"\nTesting GET /articles/by-url?url={url}")
    response = client.get(f"/articles/by-url?url={url}")
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response content: {response.content.decode('utf-8')}")
    
    # Try invalid URL
    invalid_url = "not-a-valid-url"
    print(f"\nTesting GET /articles/by-url?url={invalid_url}")
    response = client.get(f"/articles/by-url?url={invalid_url}")
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content.decode('utf-8')}")
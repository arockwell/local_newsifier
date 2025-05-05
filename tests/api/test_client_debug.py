"""Test client debug script."""

from fastapi.testclient import TestClient

from local_newsifier.api.main import app

# Create a client
client = TestClient(app)

# Test the article endpoints
print("Testing article endpoints...")

# List available routes
print("\nAvailable routes:")
for route in app.routes:
    print(f"{route.path} - {route.methods}")

# Test health endpoint
response = client.get("/health")
print(f"\nHealth check: {response.status_code}")
print(f"Response: {response.json()}")

# Try to create an article
article_data = {
    "title": "Test Article",
    "content": "This is a test article content.",
    "url": "https://example.com/test-article",
    "source": "test_source",
    "status": "new",
}
print("\nAttempting to create article...")
response = client.post("/articles/", json=article_data)
print(f"Create article status: {response.status_code}")
try:
    print(f"Response: {response.json()}")
except Exception:
    print(f"Raw response: {response.content.decode('utf-8')}")
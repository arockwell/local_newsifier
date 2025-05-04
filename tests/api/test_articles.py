"""Tests for the article router endpoints."""

from datetime import datetime, timezone

from fastapi import status
from fastapi.testclient import TestClient

from local_newsifier.models.article import Article


class TestArticleRouter:
    """Tests for the article router endpoints."""

    def test_create_article(self, client: TestClient, db_session):
        """Test creating a new article."""
        article_data = {
            "title": "Test Article",
            "content": "This is a test article content.",
            "url": "https://example.com/test-article",
            "source": "test_source",
            "status": "new",
            "published_at": "2025-05-04T05:24:49.629885Z",  # Add published_at field
        }

        response = client.post("/articles/", json=article_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == article_data["title"]
        assert data["url"] == article_data["url"]

    def test_get_article_by_url(self, client: TestClient, db_session):
        """Test getting an article by URL."""
        # Create an article first
        article = Article(
            title="Test Article",
            content="This is a test article content.",
            url="https://example.com/test-article",
            source="test_source",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc),
        )
        db_session.add(article)
        db_session.commit()

        # Test retrieving it by URL
        url = "https://example.com/test-article"
        response = client.get(f"/articles/url/{url}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Test Article"
        assert data["url"] == url

    def test_get_article_by_complex_url(self, client: TestClient, db_session):
        """Test getting an article by URL with path components."""
        # Create an article with a complex URL
        complex_url = (
            "https://example.com/path/with/multiple/segments?param=value&other=value"
        )
        article = Article(
            title="Complex URL Article",
            content="This article has a complex URL with multiple path segments.",
            url=complex_url,
            source="test_source",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc),
        )
        db_session.add(article)
        db_session.commit()

        # Test retrieving it by the complex URL
        response = client.get(f"/articles/url/{complex_url}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Complex URL Article"
        assert data["url"] == complex_url

    def test_get_article_by_url_not_found(self, client: TestClient, db_session):
        """Test getting a non-existent article by URL."""
        url = "https://example.com/nonexistent-article"
        response = client.get(f"/articles/url/{url}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "not_found"
        assert data["error"]["detail"] == f"Article with URL '{url}' not found"

    def test_get_article_by_url_invalid_format(self, client: TestClient, db_session):
        """Test getting an article with an invalid URL format."""
        invalid_url = "not-a-valid-url"
        response = client.get(f"/articles/url/{invalid_url}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "Invalid URL format" in data["detail"]

    def test_update_article(self, client: TestClient, db_session):
        """Test updating an article."""
        # Create an article first
        article = Article(
            title="Original Title",
            content="Original content.",
            url="https://example.com/article",
            source="test_source",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc),
        )
        db_session.add(article)
        db_session.commit()

        # Update the article
        update_data = {"title": "Updated Title", "status": "processed"}
        response = client.put(f"/articles/{article.id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "processed"
        assert data["content"] == "Original content"  # Unchanged

    def test_delete_article(self, client: TestClient, db_session):
        """Test deleting an article."""
        # Create an article first
        article = Article(
            title="Article to Delete",
            content="This article will be deleted.",
            url="https://example.com/article-to-delete",
            source="test_source",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc),
        )
        db_session.add(article)
        db_session.commit()

        # Delete the article
        response = client.delete(f"/articles/{article.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's gone
        response = client.get(f"/articles/{article.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

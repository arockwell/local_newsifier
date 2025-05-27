"""Tests for the NewsPipelineService."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


def test_process_url():
    """Test processing an article from a URL."""
    # Arrange
    # Mock the web scraper
    mock_web_scraper = MagicMock()
    mock_web_scraper.scrape_url.return_value = {
        "title": "Test Article",
        "content": "John Doe visited the city.",
        "published_at": datetime(2025, 1, 1),
    }

    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [
            {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1}
        ],
        "analysis_result": {
            "entities": [
                {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1}
            ],
            "statistics": {"total_entities": 1},
        },
    }

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service, web_scraper=mock_web_scraper, session_factory=None
    )

    # Act
    result = service.process_url("https://example.com")

    # Assert
    # Verify web scraper was called correctly
    mock_web_scraper.scrape_url.assert_called_once_with("https://example.com")

    # Verify article service was called correctly
    mock_article_service.process_article.assert_called_once_with(
        url="https://example.com",
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Verify result
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"
    assert len(result["entities"]) == 1
    assert result["entities"][0]["original_text"] == "John Doe"
    assert result["analysis_result"]["statistics"]["total_entities"] == 1


def test_process_url_scraping_failed():
    """Test processing an article when scraping fails."""
    # Arrange
    # Mock the web scraper to return None (scraping failed)
    mock_web_scraper = MagicMock()
    mock_web_scraper.scrape_url.return_value = None

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=MagicMock(), web_scraper=mock_web_scraper, session_factory=None
    )

    # Act
    result = service.process_url("https://example.com")

    # Assert
    assert result["status"] == "error"
    assert "Failed to scrape content" in result["message"]


def test_process_content():
    """Test processing article content directly."""
    # Arrange
    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [
            {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1}
        ],
        "analysis_result": {
            "entities": [
                {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1}
            ],
            "statistics": {"total_entities": 1},
        },
    }

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service, web_scraper=MagicMock(), session_factory=None
    )

    # Act
    result = service.process_content(
        url="https://example.com",
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Assert
    # Verify article service was called correctly
    mock_article_service.process_article.assert_called_once_with(
        url="https://example.com",
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Verify result
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"
    assert len(result["entities"]) == 1
    assert result["entities"][0]["original_text"] == "John Doe"
    assert result["analysis_result"]["statistics"]["total_entities"] == 1


def test_process_content_with_file_writer():
    """Test processing article content with file writer."""
    # Arrange
    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [],
        "analysis_result": {"statistics": {"total_entities": 0}},
    }

    # Mock the file writer
    mock_file_writer = MagicMock()
    mock_file_writer.write_results.return_value = "/path/to/output.json"

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service,
        web_scraper=MagicMock(),
        file_writer=mock_file_writer,
        session_factory=None,
    )

    # Act
    result = service.process_content(
        url="https://example.com", content="Test content", title="Test Article"
    )

    # Assert
    # Verify file writer was called
    mock_file_writer.write_results.assert_called_once()

    # Verify result includes file path
    assert result["file_path"] == "/path/to/output.json"

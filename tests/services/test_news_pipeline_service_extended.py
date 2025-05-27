"""Extended tests for the NewsPipelineService."""

from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest


def test_pipeline_initialization_with_custom_config():
    """Test initializing pipeline with custom configuration."""
    # Arrange
    # Create custom mock dependencies
    mock_article_service = MagicMock()
    mock_web_scraper = MagicMock()
    mock_file_writer = MagicMock()
    mock_custom_session_factory = MagicMock()

    # Create the service with custom configuration
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service,
        web_scraper=mock_web_scraper,
        file_writer=mock_file_writer,
        session_factory=mock_custom_session_factory,
    )

    # Assert
    # Verify the service was initialized with the custom dependencies
    assert service.article_service is mock_article_service
    assert service.web_scraper is mock_web_scraper
    assert service.file_writer is mock_file_writer
    assert service.session_factory is mock_custom_session_factory


def test_process_url_with_stage_error():
    """Test handling errors in specific pipeline stages."""
    # Arrange
    # Mock the web scraper to succeed
    mock_web_scraper = MagicMock()
    mock_web_scraper.scrape_url.return_value = {
        "title": "Test Article",
        "content": "Test content",
        "published_at": datetime(2025, 1, 1),
    }

    # Mock the article service to fail
    mock_article_service = MagicMock()
    mock_article_service.process_article.side_effect = Exception("Processing error")

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service, web_scraper=mock_web_scraper, session_factory=None
    )

    # Act
    # This should catch the exception and return an error result
    result = service.process_url("https://example.com")

    # Assert
    # Verify web scraper was called
    mock_web_scraper.scrape_url.assert_called_once_with("https://example.com")

    # Verify article service was called
    mock_article_service.process_article.assert_called_once()

    # Verify error result
    assert "status" in result
    assert result["status"] == "error"
    assert "Processing error" in result["message"]


def test_process_content_with_custom_session():
    """Test processing with a custom database session."""
    # Arrange
    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [],
    }

    # Create a custom session factory
    mock_custom_session = MagicMock()
    mock_custom_session_factory = MagicMock()
    mock_custom_session_factory.return_value.__enter__.return_value = mock_custom_session

    # Create the service with the custom session factory
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service,
        web_scraper=MagicMock(),
        session_factory=mock_custom_session_factory,
    )

    # Act
    result = service.process_content(
        url="https://example.com",
        content="Test content",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Assert
    # Verify article service was called with correct parameters
    mock_article_service.process_article.assert_called_once_with(
        url="https://example.com",
        content="Test content",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Verify result
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"


def test_pipeline_with_alternative_scraper():
    """Test pipeline with a different web scraper implementation."""
    # Arrange
    # Create an alternative scraper with different return format
    mock_alternative_scraper = MagicMock()
    mock_alternative_scraper.scrape_url.return_value = {
        "title": "Alternative Scraper Title",
        "content": "Content from alternative scraper",
        "published_at": datetime(2025, 1, 1),
        "author": "John Doe",  # Additional field not in standard scraper
        "tags": ["news", "tech"],  # Additional field not in standard scraper
    }

    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Alternative Scraper Title",
        "url": "https://example.com",
        "entities": [],
    }

    # Create the service with the alternative scraper
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service,
        web_scraper=mock_alternative_scraper,
        session_factory=None,
    )

    # Act
    result = service.process_url("https://example.com")

    # Assert
    # Verify alternative scraper was called
    mock_alternative_scraper.scrape_url.assert_called_once_with("https://example.com")

    # Verify article service was called with data from alternative scraper
    mock_article_service.process_article.assert_called_once_with(
        url="https://example.com",
        content="Content from alternative scraper",
        title="Alternative Scraper Title",
        published_at=datetime(2025, 1, 1),
    )

    # Verify result
    assert result["article_id"] == 1
    assert result["title"] == "Alternative Scraper Title"
    assert result["url"] == "https://example.com"


def test_process_url_with_scraper_returning_none():
    """Test handling when scraper returns None."""
    # Arrange
    # Mock the web scraper to return None
    mock_web_scraper = MagicMock()
    mock_web_scraper.scrape_url.return_value = None

    # Mock the article service
    mock_article_service = MagicMock()

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service, web_scraper=mock_web_scraper, session_factory=None
    )

    # Act
    result = service.process_url("https://example.com")

    # Assert
    # Verify web scraper was called
    mock_web_scraper.scrape_url.assert_called_once_with("https://example.com")

    # Verify article service was not called
    mock_article_service.process_article.assert_not_called()

    # Verify error result
    assert result["status"] == "error"
    assert "Failed to scrape content" in result["message"]


def test_process_content_with_missing_published_date():
    """Test processing content without a published date."""
    # Arrange
    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [],
    }

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service, web_scraper=MagicMock(), session_factory=None
    )

    # Act
    # Call without published_at
    result = service.process_content(
        url="https://example.com", content="Test content", title="Test Article"
    )

    # Assert
    # Verify article service was called with current date
    mock_article_service.process_article.assert_called_once()
    # Get the args from the call
    args, kwargs = mock_article_service.process_article.call_args
    # Verify published_at was provided and is a datetime
    assert "published_at" in kwargs
    assert isinstance(kwargs["published_at"], datetime)

    # Verify result
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"


def test_process_url_with_partial_scraper_data():
    """Test processing with partial data from scraper."""
    # Arrange
    # Mock the web scraper to return partial data
    mock_web_scraper = MagicMock()
    mock_web_scraper.scrape_url.return_value = {
        "title": "Test Article",
        "content": "Test content",
        # Missing published_at
    }

    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [],
    }

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service, web_scraper=mock_web_scraper, session_factory=None
    )

    # Act
    result = service.process_url("https://example.com")

    # Assert
    # Verify web scraper was called
    mock_web_scraper.scrape_url.assert_called_once_with("https://example.com")

    # Verify article service was called with current date
    mock_article_service.process_article.assert_called_once()
    # Get the args from the call
    args, kwargs = mock_article_service.process_article.call_args
    # Verify published_at was provided and is a datetime
    assert "published_at" in kwargs
    assert isinstance(kwargs["published_at"], datetime)

    # Verify result
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"


def test_process_content_with_file_writer_error():
    """Test handling errors from file writer."""
    # Arrange
    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [],
    }

    # Mock the file writer to raise an exception
    mock_file_writer = MagicMock()
    mock_file_writer.write_results.side_effect = Exception("File writing error")

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service,
        web_scraper=MagicMock(),
        file_writer=mock_file_writer,
        session_factory=None,
    )

    # Act
    # This should catch the exception and return the result without file_path
    result = service.process_content(
        url="https://example.com", content="Test content", title="Test Article"
    )

    # Assert
    # Verify article service was called
    mock_article_service.process_article.assert_called_once()

    # Verify file writer was called
    mock_file_writer.write_results.assert_called_once()

    # Verify result doesn't have file_path but has other data
    assert "file_path" not in result
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"

    # Verify error is included in result
    assert "error" in result
    assert "File writing error" in result["error"]


def test_process_url_and_content_integration():
    """Test integration between process_url and process_content."""
    # Arrange
    # Mock the web scraper
    mock_web_scraper = MagicMock()
    mock_web_scraper.scrape_url.return_value = {
        "title": "Test Article",
        "content": "Test content",
        "published_at": datetime(2025, 1, 1),
    }

    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [],
    }

    # Create the service with mocks
    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    service = NewsPipelineService(
        article_service=mock_article_service, web_scraper=mock_web_scraper, session_factory=None
    )

    # Act
    # Process a URL
    url_result = service.process_url("https://example.com")

    # Process content directly with the same data
    content_result = service.process_content(
        url="https://example.com",
        content="Test content",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Assert
    # Verify both methods were called with the same parameters
    mock_article_service.process_article.assert_has_calls(
        [
            call(
                url="https://example.com",
                content="Test content",
                title="Test Article",
                published_at=datetime(2025, 1, 1),
            ),
            call(
                url="https://example.com",
                content="Test content",
                title="Test Article",
                published_at=datetime(2025, 1, 1),
            ),
        ]
    )

    # Verify both results are the same
    assert url_result == content_result

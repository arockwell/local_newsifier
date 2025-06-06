"""Consolidated tests for the NewsPipelineService.

This file combines tests from:
- test_news_pipeline_service.py (core functionality)
- test_news_pipeline_service_extended.py (edge cases and alternative configurations)
"""

from datetime import datetime
from unittest.mock import MagicMock, call

# Test helper fixtures
# Note: mock_pipeline_deps fixture is now in conftest.py


class TestNewsPipelineServiceCore:
    """Core functionality tests."""

    def test_process_url(self, mock_pipeline_deps):
        """Test processing an article from a URL."""
        # Arrange
        deps = mock_pipeline_deps

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
        )

        # Act
        result = service.process_url("https://example.com")

        # Assert
        # Verify web scraper was called correctly
        deps["web_scraper"].scrape_url.assert_called_once_with("https://example.com")

        # Verify article service was called correctly
        deps["article_service"].process_article.assert_called_once_with(
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

    def test_process_url_scraping_failed(self, mock_pipeline_deps):
        """Test processing an article when scraping fails."""
        # Arrange
        deps = mock_pipeline_deps

        # Mock the web scraper to return None (scraping failed)
        deps["web_scraper"].scrape_url.return_value = None

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
        )

        # Act
        result = service.process_url("https://example.com")

        # Assert
        assert result["status"] == "error"
        assert "Failed to scrape content" in result["message"]

    def test_process_content(self, mock_pipeline_deps):
        """Test processing article content directly."""
        # Arrange
        deps = mock_pipeline_deps

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
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
        deps["article_service"].process_article.assert_called_once_with(
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

    def test_process_content_with_file_writer(self, mock_pipeline_deps):
        """Test processing article content with file writer."""
        # Arrange
        deps = mock_pipeline_deps

        # Simplify the return value for this test
        deps["article_service"].process_article.return_value = {
            "article_id": 1,
            "title": "Test Article",
            "url": "https://example.com",
            "entities": [],
            "analysis_result": {"statistics": {"total_entities": 0}},
        }

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            file_writer=deps["file_writer"],
            session_factory=None,
        )

        # Act
        result = service.process_content(
            url="https://example.com", content="Test content", title="Test Article"
        )

        # Assert
        # Verify file writer was called
        deps["file_writer"].write_results.assert_called_once()

        # Verify result includes file path
        assert result["file_path"] == "/path/to/output.json"


class TestNewsPipelineServiceConfiguration:
    """Tests for different configurations and edge cases."""

    def test_pipeline_initialization_with_custom_config(self):
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

    def test_process_url_with_stage_error(self, mock_pipeline_deps):
        """Test handling errors in specific pipeline stages."""
        # Arrange
        deps = mock_pipeline_deps

        # Mock the article service to fail
        deps["article_service"].process_article.side_effect = Exception("Processing error")

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
        )

        # Act
        # This should catch the exception and return an error result
        result = service.process_url("https://example.com")

        # Assert
        # Verify web scraper was called
        deps["web_scraper"].scrape_url.assert_called_once_with("https://example.com")

        # Verify article service was called
        deps["article_service"].process_article.assert_called_once()

        # Verify error result
        assert "status" in result
        assert result["status"] == "error"
        assert "Processing error" in result["message"]

    def test_process_content_with_custom_session(self, mock_pipeline_deps):
        """Test processing with a custom database session."""
        # Arrange
        deps = mock_pipeline_deps

        # Create the service with the custom session factory
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=deps["session_factory"],
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
        deps["article_service"].process_article.assert_called_once_with(
            url="https://example.com",
            content="Test content",
            title="Test Article",
            published_at=datetime(2025, 1, 1),
        )

        # Verify result
        assert result["article_id"] == 1
        assert result["title"] == "Test Article"
        assert result["url"] == "https://example.com"

    def test_pipeline_with_alternative_scraper(self, mock_pipeline_deps):
        """Test pipeline with a different web scraper implementation."""
        # Arrange
        deps = mock_pipeline_deps

        # Create an alternative scraper with different return format
        deps["web_scraper"].scrape_url.return_value = {
            "title": "Alternative Scraper Title",
            "content": "Content from alternative scraper",
            "published_at": datetime(2025, 1, 1),
            "author": "John Doe",  # Additional field not in standard scraper
            "tags": ["news", "tech"],  # Additional field not in standard scraper
        }

        # Update article service mock
        deps["article_service"].process_article.return_value = {
            "article_id": 1,
            "title": "Alternative Scraper Title",
            "url": "https://example.com",
            "entities": [],
        }

        # Create the service with the alternative scraper
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
        )

        # Act
        result = service.process_url("https://example.com")

        # Assert
        # Verify alternative scraper was called
        deps["web_scraper"].scrape_url.assert_called_once_with("https://example.com")

        # Verify article service was called with data from alternative scraper
        deps["article_service"].process_article.assert_called_once_with(
            url="https://example.com",
            content="Content from alternative scraper",
            title="Alternative Scraper Title",
            published_at=datetime(2025, 1, 1),
        )

        # Verify result
        assert result["article_id"] == 1
        assert result["title"] == "Alternative Scraper Title"
        assert result["url"] == "https://example.com"


class TestNewsPipelineServiceEdgeCases:
    """Tests for edge cases and error handling."""

    def test_process_url_with_scraper_returning_none(self, mock_pipeline_deps):
        """Test handling when scraper returns None."""
        # Arrange
        deps = mock_pipeline_deps

        # Mock the web scraper to return None
        deps["web_scraper"].scrape_url.return_value = None

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
        )

        # Act
        result = service.process_url("https://example.com")

        # Assert
        # Verify web scraper was called
        deps["web_scraper"].scrape_url.assert_called_once_with("https://example.com")

        # Verify article service was not called
        deps["article_service"].process_article.assert_not_called()

        # Verify error result
        assert result["status"] == "error"
        assert "Failed to scrape content" in result["message"]

    def test_process_content_with_missing_published_date(self, mock_pipeline_deps):
        """Test processing content without a published date."""
        # Arrange
        deps = mock_pipeline_deps

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
        )

        # Act
        # Call without published_at
        result = service.process_content(
            url="https://example.com", content="Test content", title="Test Article"
        )

        # Assert
        # Verify article service was called with current date
        deps["article_service"].process_article.assert_called_once()
        # Get the args from the call
        args, kwargs = deps["article_service"].process_article.call_args
        # Verify published_at was provided and is a datetime
        assert "published_at" in kwargs
        assert isinstance(kwargs["published_at"], datetime)

        # Verify result
        assert result["article_id"] == 1
        assert result["title"] == "Test Article"
        assert result["url"] == "https://example.com"

    def test_process_url_with_partial_scraper_data(self, mock_pipeline_deps):
        """Test processing with partial data from scraper."""
        # Arrange
        deps = mock_pipeline_deps

        # Mock the web scraper to return partial data
        deps["web_scraper"].scrape_url.return_value = {
            "title": "Test Article",
            "content": "Test content",
            # Missing published_at
        }

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
        )

        # Act
        result = service.process_url("https://example.com")

        # Assert
        # Verify web scraper was called
        deps["web_scraper"].scrape_url.assert_called_once_with("https://example.com")

        # Verify article service was called with current date
        deps["article_service"].process_article.assert_called_once()
        # Get the args from the call
        args, kwargs = deps["article_service"].process_article.call_args
        # Verify published_at was provided and is a datetime
        assert "published_at" in kwargs
        assert isinstance(kwargs["published_at"], datetime)

        # Verify result
        assert result["article_id"] == 1
        assert result["title"] == "Test Article"
        assert result["url"] == "https://example.com"

    def test_process_content_with_file_writer_error(self, mock_pipeline_deps):
        """Test handling errors from file writer."""
        # Arrange
        deps = mock_pipeline_deps

        # Mock the file writer to raise an exception
        deps["file_writer"].write_results.side_effect = Exception("File writing error")

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            file_writer=deps["file_writer"],
            session_factory=None,
        )

        # Act
        # This should catch the exception and return the result without file_path
        result = service.process_content(
            url="https://example.com", content="Test content", title="Test Article"
        )

        # Assert
        # Verify article service was called
        deps["article_service"].process_article.assert_called_once()

        # Verify file writer was called
        deps["file_writer"].write_results.assert_called_once()

        # Verify result doesn't have file_path but has other data
        assert "file_path" not in result
        assert result["article_id"] == 1
        assert result["title"] == "Test Article"
        assert result["url"] == "https://example.com"

        # Verify error is included in result
        assert "error" in result
        assert "File writing error" in result["error"]

    def test_process_url_and_content_integration(self, mock_pipeline_deps):
        """Test integration between process_url and process_content."""
        # Arrange
        deps = mock_pipeline_deps

        # Create the service with mocks
        from local_newsifier.services.news_pipeline_service import NewsPipelineService

        service = NewsPipelineService(
            article_service=deps["article_service"],
            web_scraper=deps["web_scraper"],
            session_factory=None,
        )

        # Act
        # Process a URL
        url_result = service.process_url("https://example.com")

        # Process content directly with the same data
        content_result = service.process_content(
            url="https://example.com",
            content="John Doe visited the city.",
            title="Test Article",
            published_at=datetime(2025, 1, 1),
        )

        # Assert
        # Verify both methods were called with the same parameters
        deps["article_service"].process_article.assert_has_calls(
            [
                call(
                    url="https://example.com",
                    content="John Doe visited the city.",
                    title="Test Article",
                    published_at=datetime(2025, 1, 1),
                ),
                call(
                    url="https://example.com",
                    content="John Doe visited the city.",
                    title="Test Article",
                    published_at=datetime(2025, 1, 1),
                ),
            ]
        )

        # Verify both results are the same
        assert url_result == content_result

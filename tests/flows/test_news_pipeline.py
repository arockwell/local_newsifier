"""Tests for the news pipeline flow."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from tenacity import retry, stop_after_attempt, wait_exponential

from local_newsifier.flows.news_pipeline import NewsPipelineFlow
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.web_scraper import WebScraperTool


@pytest.fixture(scope="function")
def mock_scraper():
    """Create a mock scraper that returns successful results."""

    def successful_scrape(state):
        state.scraped_text = "Test article content"
        state.status = AnalysisStatus.SCRAPE_SUCCEEDED
        return state

    scraper = Mock()
    scraper.scrape = Mock(side_effect=successful_scrape)
    return scraper


@pytest.fixture(scope="function")
def mock_article_service():
    """Create a mock article service that returns successful results."""

    def successful_save(session, state):
        state.article_id = 123
        state.status = AnalysisStatus.SAVE_SUCCEEDED
        return state

    service = Mock()
    service.create_article_from_state = Mock(side_effect=successful_save)
    return service


@pytest.fixture(scope="function")
def mock_pipeline_service():
    """Create a mock pipeline service that returns successful results."""

    def successful_process(state):
        state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
        state.entities = [{"name": "Test Entity", "type": "PERSON"}]
        state.sentiment_score = 0.8
        state.topics = ["politics", "local"]
        state.summary = "This is a test summary."
        return state

    service = Mock()
    service.process_article_with_state = Mock(side_effect=successful_process)
    return service


def test_news_pipeline_init():
    """Test initializing the news pipeline flow."""
    # Test with default parameters
    flow = NewsPipelineFlow()
    
    # Test with explicit dependencies
    mock_scraper = Mock()
    mock_pipeline_service = Mock()
    mock_article_service = Mock()
    
    flow = NewsPipelineFlow(
        scraper=mock_scraper,
        pipeline_service=mock_pipeline_service,
        article_service=mock_article_service
    )
    
    assert flow.scraper is mock_scraper
    assert flow.pipeline_service is mock_pipeline_service
    assert flow.article_service is mock_article_service


def test_process_with_successful_flow(mock_scraper, mock_pipeline_service, mock_article_service):
    """Test the news pipeline flow with successful processing."""
    # Create a test state
    state = NewsAnalysisState(
        content="Test content",
        title="Test Article",
        url="https://example.com/article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Create flow with mocked dependencies
    flow = NewsPipelineFlow(
        scraper=mock_scraper,
        pipeline_service=mock_pipeline_service,
        article_service=mock_article_service
    )
    
    # Process the state
    result = flow.process(state)
    
    # Verify the pipeline service was called
    mock_pipeline_service.process_article_with_state.assert_called_once_with(state)
    
    # Verify the result
    assert result.status == AnalysisStatus.ANALYSIS_SUCCEEDED
    assert len(result.entities) == 1
    assert result.sentiment_score == 0.8
    assert len(result.topics) == 2
    assert result.summary == "This is a test summary."


def test_process_article(mock_scraper, mock_pipeline_service, mock_article_service):
    """Test processing an article by ID."""
    # Mock the get method of article_crud
    with patch("local_newsifier.crud.article.article.get") as mock_get:
        # Setup mock article
        mock_article = Mock()
        mock_article.id = 123
        mock_article.content = "Test content"
        mock_article.title = "Test Article"
        mock_article.url = "https://example.com/article"
        mock_article.published_at = datetime(2025, 1, 1)
        
        mock_get.return_value = mock_article
        
        # Create flow with mocked dependencies and session
        mock_session = Mock()
        
        # Mock the session_factory
        def mock_session_factory():
            class MockContextManager:
                def __enter__(self):
                    return mock_session
                def __exit__(self, *args):
                    pass
            return MockContextManager()
        
        flow = NewsPipelineFlow(
            scraper=mock_scraper,
            pipeline_service=mock_pipeline_service,
            article_service=mock_article_service,
            session_factory=mock_session_factory
        )
        
        # Process article
        result = flow.process_article(123)
        
        # Verify article was retrieved
        mock_get.assert_called_once_with(mock_session, id=123)
        
        # Verify pipeline service was called
        assert mock_pipeline_service.process_article_with_state.call_count == 1
        
        # Verify result format
        assert result["status"] == "ANALYSIS_SUCCEEDED"
        assert "entities" in result
        assert "sentiment" in result
        assert "topics" in result
        assert "summary" in result


def test_analyze_with_url(mock_scraper, mock_pipeline_service, mock_article_service):
    """Test analyzing an article from a URL."""
    # Setup mock scraper behavior
    mock_scraper.scrape_article.return_value = {
        "content": "Test content",
        "title": "Test Article",
        "published_at": datetime(2025, 1, 1)
    }
    
    # Create flow with mocked dependencies
    flow = NewsPipelineFlow(
        scraper=mock_scraper,
        pipeline_service=mock_pipeline_service,
        article_service=mock_article_service
    )
    
    # Analyze with URL
    result = flow.analyze_with_url("https://example.com/article")
    
    # Verify scraper was called with correct URL
    mock_scraper.scrape_article.assert_called_once_with("https://example.com/article")
    
    # Verify pipeline service was called
    assert mock_pipeline_service.process_article_with_state.call_count == 1
    
    # Verify result format
    assert result["status"] == "ANALYSIS_SUCCEEDED"
    assert "entities" in result
    assert "sentiment" in result
    assert "topics" in result
    assert "summary" in result


def test_analyze_with_text(mock_scraper, mock_pipeline_service, mock_article_service):
    """Test analyzing an article from raw text."""
    # Create flow with mocked dependencies
    flow = NewsPipelineFlow(
        scraper=mock_scraper,
        pipeline_service=mock_pipeline_service,
        article_service=mock_article_service
    )
    
    # Analyze with text
    result = flow.analyze_with_text(
        content="Test content",
        title="Test Article",
        url="https://example.com/article"
    )
    
    # Verify pipeline service was called
    assert mock_pipeline_service.process_article_with_state.call_count == 1
    
    # Verify result format
    assert result["status"] == "ANALYSIS_SUCCEEDED"
    assert "entities" in result
    assert "sentiment" in result
    assert "topics" in result
    assert "summary" in result

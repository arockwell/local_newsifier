"""Tests for the news pipeline flow."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from tenacity import retry, stop_after_attempt, wait_exponential

from local_newsifier.flows.news_pipeline import NewsPipelineFlow
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.web_scraper import WebScraperTool


@pytest.fixture(scope="session")
def mock_scraper():
    """Create a mock scraper that returns successful results."""

    def successful_scrape(state):
        state.scraped_text = "Test article content"
        state.status = AnalysisStatus.SCRAPE_SUCCEEDED
        return state

    scraper = Mock()
    scraper.scrape = Mock(side_effect=successful_scrape)
    return scraper


@pytest.fixture(scope="session")
def mock_article_service():
    """Create a mock article service that returns successful results."""
    
    article_service = Mock()
    article_service.process_article = Mock(return_value={
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com/test",
        "entities": [{"original_text": "John Doe", "canonical_name": "John Doe"}],
        "analysis_result": {
            "entities": [{"original_text": "John Doe", "canonical_name": "John Doe"}],
            "statistics": {
                "entity_counts": {"PERSON": 1},
                "total_entities": 1
            }
        }
    })
    return article_service


@pytest.fixture(scope="session")
def mock_file_writer():
    """Create a mock file writer that returns successful results."""

    def successful_save(state):
        state.saved_at = datetime.now()
        state.status = AnalysisStatus.SAVE_SUCCEEDED
        return state

    writer = Mock()
    writer.save = Mock(side_effect=successful_save)
    return writer


@pytest.fixture(scope="session")
def mock_pipeline_service():
    """Create a mock pipeline service that returns successful results."""
    pipeline_service = Mock()
    pipeline_service.process_url = Mock(return_value={
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com/test",
        "entities": [{"original_text": "John Doe", "canonical_name": "John Doe"}],
        "analysis_result": {
            "entities": [{"original_text": "John Doe", "canonical_name": "John Doe"}],
            "statistics": {
                "entity_counts": {"PERSON": 1},
                "total_entities": 1
            }
        }
    })
    return pipeline_service


@pytest.fixture(scope="session")
def pipeline(mock_scraper, mock_article_service, mock_file_writer, mock_pipeline_service):
    """Create a pipeline instance with mocked components."""
    # Create mock entity service and tools as needed by constructor
    mock_entity_service = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    
    # Set up function to fix session_factory access
    mock_session_factory_fn = lambda: Mock()
    
    with patch('local_newsifier.flows.news_pipeline.injectable', lambda **kwargs: lambda cls: cls):
        pipeline = NewsPipelineFlow(
            web_scraper=mock_scraper,
            file_writer=mock_file_writer,
            article_service=mock_article_service,
            pipeline_service=mock_pipeline_service,
            entity_service=mock_entity_service,
            entity_extractor=mock_entity_extractor,
            context_analyzer=mock_context_analyzer,
            entity_resolver=mock_entity_resolver,
            session_factory=mock_session_factory_fn,
            output_dir="test_output"
        )
    return pipeline


@pytest.fixture(autouse=True)
def reset_mocks(pipeline):
    """Reset all mocks before each test."""
    # Store original side effects
    scraper_effect = getattr(pipeline.scraper.scrape, "side_effect", None)
    article_service_effect = getattr(pipeline.article_service.process_article, "side_effect", None)
    writer_effect = getattr(pipeline.writer.save, "side_effect", None)

    # Reset mocks if they are Mock objects
    if isinstance(pipeline.scraper, Mock):
        pipeline.scraper.reset_mock()
    if isinstance(pipeline.article_service, Mock):
        pipeline.article_service.reset_mock()
    if isinstance(pipeline.writer, Mock):
        pipeline.writer.reset_mock()

    # Restore original side effects if they exist
    if scraper_effect is not None and isinstance(pipeline.scraper.scrape, Mock):
        pipeline.scraper.scrape.side_effect = scraper_effect
    if article_service_effect is not None and isinstance(pipeline.article_service.process_article, Mock):
        pipeline.article_service.process_article.side_effect = article_service_effect
    if writer_effect is not None and isinstance(pipeline.writer.save, Mock):
        pipeline.writer.save.side_effect = writer_effect

    yield


def test_pipeline_flow_success(pipeline):
    """Test successful pipeline execution from start to finish."""
    url = "https://example.com/test-article"

    # Execute pipeline
    state = pipeline.start_pipeline(url)

    # Verify final state
    assert state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert state.target_url == url
    assert len(state.run_logs) > 0
    assert state.scraped_text is not None
    assert state.analysis_results is not None
    assert state.saved_at is not None

    # Verify component calls
    pipeline.scraper.scrape.assert_called_once()
    pipeline.article_service.process_article.assert_called_once()
    pipeline.writer.save.assert_called_once()


def test_pipeline_resume_from_scrape_failed(pipeline):
    """Test pipeline resumption after scraping failure."""
    # Create failed state
    state = NewsAnalysisState(target_url="https://example.com/failed")
    state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK

    # Resume pipeline
    resumed_state = pipeline.resume_pipeline("test_run", state)

    # Verify recovery
    assert resumed_state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert resumed_state.scraped_text is not None
    assert resumed_state.analysis_results is not None
    assert resumed_state.saved_at is not None

    # Verify component calls
    pipeline.scraper.scrape.assert_called_once()
    pipeline.article_service.process_article.assert_called_once()
    pipeline.writer.save.assert_called_once()


def test_pipeline_resume_from_analysis_failed(pipeline):
    """Test pipeline resumption after analysis failure."""
    # Create state with successful scrape but failed analysis
    state = NewsAnalysisState(target_url="https://example.com/analysis-failed")
    state.status = AnalysisStatus.ANALYSIS_FAILED
    state.scraped_text = "Test content for analysis"

    # Resume pipeline
    resumed_state = pipeline.resume_pipeline("test_run", state)

    # Verify recovery
    assert resumed_state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert resumed_state.analysis_results is not None
    assert resumed_state.saved_at is not None

    # Verify component calls
    pipeline.scraper.scrape.assert_not_called()  # Should skip scrape
    pipeline.article_service.process_article.assert_called_once()
    pipeline.writer.save.assert_called_once()


def test_pipeline_resume_from_save_failed(pipeline):
    """Test pipeline resumption after save failure."""
    # Create state with successful analysis but failed save
    state = NewsAnalysisState(target_url="https://example.com/save-failed")
    state.status = AnalysisStatus.SAVE_FAILED
    state.scraped_text = "Test content"
    state.analysis_results = {"entities": {"PERSON": []}}

    # Resume pipeline
    resumed_state = pipeline.resume_pipeline("test_run", state)

    # Verify recovery
    assert resumed_state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert resumed_state.saved_at is not None

    # Verify component calls
    pipeline.scraper.scrape.assert_not_called()  # Should skip scrape
    pipeline.article_service.process_article.assert_not_called()  # Should skip analysis
    pipeline.writer.save.assert_called_once()


def test_pipeline_resume_invalid_state(pipeline):
    """Test pipeline resumption with invalid state."""
    # Create completed state
    state = NewsAnalysisState(target_url="https://example.com/completed")
    state.status = AnalysisStatus.SAVE_SUCCEEDED

    # Attempt to resume completed pipeline
    with pytest.raises(ValueError) as exc_info:
        pipeline.resume_pipeline("test_run", state)
    assert "Cannot resume from status" in str(exc_info.value)


def test_pipeline_resume_no_state(pipeline):
    """Test pipeline resumption with no state provided."""
    # Attempt to resume without state
    with pytest.raises(NotImplementedError) as exc_info:
        pipeline.resume_pipeline("test_run")
    assert "State loading not implemented" in str(exc_info.value)


def test_pipeline_scrape_failure(pipeline):
    """Test pipeline handling of scraping failures."""

    # Mock scraper to fail
    def scrape_failure(state):
        state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
        state.set_error("scrape", Exception("Network error"))
        return state

    pipeline.scraper.scrape = Mock(side_effect=scrape_failure)

    # Start pipeline
    state = pipeline.start_pipeline("https://example.com/error")

    # Verify error handling
    assert state.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
    assert state.error_details is not None
    assert state.error_details.task == "scrape"
    assert state.error_details.type == "Exception"
    assert "Network error" in state.error_details.message

    # Verify component calls
    pipeline.scraper.scrape.assert_called_once()
    pipeline.article_service.process_article.assert_not_called()  # Should not call article service after scrape failure
    pipeline.writer.save.assert_not_called()  # Should not call writer after scrape failure


def test_pipeline_analysis_failure(pipeline):
    """Test pipeline handling of analysis failures."""

    # Mock scraper to succeed
    def successful_scrape(state):
        state.scraped_text = "Test article content"
        state.status = AnalysisStatus.SCRAPE_SUCCEEDED
        return state

    pipeline.scraper.scrape = Mock(side_effect=successful_scrape)

    # Mock article service to fail
    def process_article_failure(*args, **kwargs):
        raise Exception("Analysis error")
        
    pipeline.article_service.process_article = Mock(side_effect=process_article_failure)

    # Start pipeline
    state = pipeline.start_pipeline("https://example.com/error")

    # Verify error handling
    assert state.status == AnalysisStatus.ANALYSIS_FAILED
    assert state.error_details is not None
    assert state.error_details.task == "analysis"
    assert state.error_details.type == "Exception"
    assert "Analysis error" in state.error_details.message

    # Verify component calls
    pipeline.scraper.scrape.assert_called_once()
    pipeline.article_service.process_article.assert_called_once()
    pipeline.writer.save.assert_not_called()  # Should not call writer after analysis failure


def test_pipeline_save_failure(pipeline):
    """Test pipeline handling of save failures."""

    # Mock scraper to succeed
    def successful_scrape(state):
        state.scraped_text = "Test article content"
        state.status = AnalysisStatus.SCRAPE_SUCCEEDED
        return state

    pipeline.scraper.scrape = Mock(side_effect=successful_scrape)

    # Mock article service to succeed
    pipeline.article_service.process_article = Mock(return_value={
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com/test",
        "entities": [{"original_text": "John Doe", "canonical_name": "John Doe"}],
        "analysis_result": {
            "entities": [{"original_text": "John Doe", "canonical_name": "John Doe"}],
            "statistics": {
                "entity_counts": {"PERSON": 1},
                "total_entities": 1
            }
        }
    })

    # Mock writer to fail
    def save_failure(state):
        state.status = AnalysisStatus.SAVE_FAILED
        state.set_error("save", Exception("Save error"))
        return state

    pipeline.writer.save = Mock(side_effect=save_failure)

    # Start pipeline
    state = pipeline.start_pipeline("https://example.com/error")

    # Verify error handling
    assert state.status == AnalysisStatus.SAVE_FAILED
    assert state.error_details is not None
    assert state.error_details.task == "save"
    assert state.error_details.type == "Exception"
    assert "Save error" in state.error_details.message

    # Verify component calls
    pipeline.scraper.scrape.assert_called_once()
    pipeline.article_service.process_article.assert_called_once()
    pipeline.writer.save.assert_called_once()


def test_pipeline_retry_attempts(pipeline):
    """Test pipeline retry logic."""

    # Create a mock scraper with retry logic
    class MockScraper:
        def __init__(self):
            self.call_count = 0

        @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.1))
        def scrape(self, state):
            self.call_count += 1
            if self.call_count == 1:
                state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
                state.set_error("scrape", Exception("Network error"))
                raise Exception("Network error")  # This will trigger the retry
            else:
                state.scraped_text = "Test article content"
                state.status = AnalysisStatus.SCRAPE_SUCCEEDED
                state.error_details = None  # Clear error details on success
            return state

    # Replace scraper with our mock
    mock_scraper = MockScraper()
    pipeline.scraper = mock_scraper

    # Mock article service to succeed
    pipeline.article_service.process_article = Mock(return_value={
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com/test",
        "entities": [{"original_text": "John Doe", "canonical_name": "John Doe"}],
        "analysis_result": {
            "entities": [{"original_text": "John Doe", "canonical_name": "John Doe"}],
            "statistics": {
                "entity_counts": {"PERSON": 1},
                "total_entities": 1
            }
        }
    })

    # Mock writer to succeed
    def successful_save(state):
        state.saved_at = datetime.now()
        state.status = AnalysisStatus.SAVE_SUCCEEDED
        return state

    pipeline.writer.save = Mock(side_effect=successful_save)

    # Start pipeline
    state = pipeline.start_pipeline("https://example.com/retry")

    # Verify final state
    assert state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert state.scraped_text is not None
    assert state.analysis_results is not None
    assert state.saved_at is not None

    # Verify retry behavior
    assert mock_scraper.call_count == 2


def test_pipeline_invalid_url(pipeline):
    """Test pipeline handling of invalid URLs."""

    # Mock scraper to raise ValueError for invalid URL
    def invalid_url_scrape(state):
        raise ValueError("Invalid URL: not-a-url")

    pipeline.scraper = Mock()
    pipeline.scraper.scrape = Mock(side_effect=invalid_url_scrape)

    # Start pipeline with invalid URL
    with pytest.raises(ValueError) as exc_info:
        pipeline.start_pipeline("not-a-url")
    assert "Invalid URL" in str(exc_info.value)

    # Verify component calls
    pipeline.scraper.scrape.assert_called_once()
    pipeline.article_service.process_article.assert_not_called()
    pipeline.writer.save.assert_not_called()

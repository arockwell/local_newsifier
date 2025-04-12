"""Tests for the news pipeline flow."""

from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from tenacity import retry, stop_after_attempt, wait_exponential

import pytest

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.flows.news_pipeline import NewsPipelineFlow
from src.local_newsifier.tools.web_scraper import WebScraperTool


@pytest.fixture
def mock_scraper():
    """Create a mock scraper that returns successful results."""
    def successful_scrape(state):
        state.scraped_text = "Test article content"
        state.status = AnalysisStatus.SCRAPE_SUCCEEDED
        return state
    
    scraper = Mock()
    scraper.scrape = Mock(side_effect=successful_scrape)
    return scraper


@pytest.fixture
def mock_analyzer():
    """Create a mock analyzer that returns successful results."""
    def successful_analyze(state):
        state.analysis_results = {"entities": {"PERSON": ["John Doe"]}}
        state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
        return state
    
    analyzer = Mock()
    analyzer.analyze = Mock(side_effect=successful_analyze)
    return analyzer


@pytest.fixture
def mock_file_writer():
    """Create a mock file writer that returns successful results."""
    def successful_save(state):
        state.saved_at = datetime.now()
        state.status = AnalysisStatus.SAVE_SUCCEEDED
        return state
    
    writer = Mock()
    writer.save = Mock(side_effect=successful_save)
    return writer


def test_pipeline_flow_success(mock_scraper, mock_analyzer, mock_file_writer):
    """Test successful pipeline execution from start to finish."""
    # Initialize pipeline with mocked components
    pipeline = NewsPipelineFlow(output_dir="test_output")
    pipeline.scraper = mock_scraper
    pipeline.analyzer = mock_analyzer
    pipeline.writer = mock_file_writer
    
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
    mock_scraper.scrape.assert_called_once()
    mock_analyzer.analyze.assert_called_once()
    mock_file_writer.save.assert_called_once()


def test_pipeline_resume_from_scrape_failed(mock_scraper, mock_analyzer, mock_file_writer):
    """Test pipeline resumption after scraping failure."""
    pipeline = NewsPipelineFlow(output_dir="test_output")
    pipeline.scraper = mock_scraper
    pipeline.analyzer = mock_analyzer
    pipeline.writer = mock_file_writer
    
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
    mock_scraper.scrape.assert_called_once()
    mock_analyzer.analyze.assert_called_once()
    mock_file_writer.save.assert_called_once()


def test_pipeline_resume_from_analysis_failed(mock_scraper, mock_analyzer, mock_file_writer):
    """Test pipeline resumption after analysis failure."""
    pipeline = NewsPipelineFlow(output_dir="test_output")
    pipeline.scraper = mock_scraper
    pipeline.analyzer = mock_analyzer
    pipeline.writer = mock_file_writer
    
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
    mock_scraper.scrape.assert_not_called()  # Should skip scrape
    mock_analyzer.analyze.assert_called_once()
    mock_file_writer.save.assert_called_once()


def test_pipeline_resume_from_save_failed(mock_scraper, mock_analyzer, mock_file_writer):
    """Test pipeline resumption after save failure."""
    pipeline = NewsPipelineFlow(output_dir="test_output")
    pipeline.scraper = mock_scraper
    pipeline.analyzer = mock_analyzer
    pipeline.writer = mock_file_writer
    
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
    mock_scraper.scrape.assert_not_called()  # Should skip scrape
    mock_analyzer.analyze.assert_not_called()  # Should skip analysis
    mock_file_writer.save.assert_called_once()


def test_pipeline_resume_invalid_state():
    """Test pipeline resumption with invalid state."""
    pipeline = NewsPipelineFlow(output_dir="test_output")
    
    # Create completed state
    state = NewsAnalysisState(target_url="https://example.com/completed")
    state.status = AnalysisStatus.SAVE_SUCCEEDED
    
    # Attempt to resume completed pipeline
    with pytest.raises(ValueError) as exc_info:
        pipeline.resume_pipeline("test_run", state)
    assert "Cannot resume from status" in str(exc_info.value)


def test_pipeline_resume_no_state():
    """Test pipeline resumption with no state provided."""
    pipeline = NewsPipelineFlow(output_dir="test_output")
    
    # Attempt to resume without state
    with pytest.raises(NotImplementedError) as exc_info:
        pipeline.resume_pipeline("test_run")
    assert "State loading not implemented" in str(exc_info.value)


def test_pipeline_scrape_failure(mock_analyzer, mock_file_writer):
    """Test pipeline handling of scraping failures."""
    # Create pipeline with mock components
    pipeline = NewsPipelineFlow(output_dir="test_output")
    
    # Mock scraper to fail
    def scrape_failure(state):
        state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
        state.set_error("scrape", Exception("Network error"))
        return state
    
    pipeline.scraper.scrape = Mock(side_effect=scrape_failure)
    pipeline.analyzer = mock_analyzer
    pipeline.writer = mock_file_writer
    
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
    mock_analyzer.analyze.assert_not_called()  # Should not call analyzer after scrape failure
    mock_file_writer.save.assert_not_called()  # Should not call writer after scrape failure


def test_pipeline_analysis_failure(mock_scraper, mock_file_writer):
    """Test pipeline handling of analysis failures."""
    # Create pipeline with mock components
    pipeline = NewsPipelineFlow(output_dir="test_output")
    
    # Mock analyzer to fail
    def analysis_failure(state):
        state.status = AnalysisStatus.ANALYSIS_FAILED
        state.set_error("analysis", Exception("Analysis error"))
        return state
    
    pipeline.scraper = mock_scraper
    pipeline.analyzer.analyze = Mock(side_effect=analysis_failure)
    pipeline.writer = mock_file_writer
    
    # Start pipeline
    state = pipeline.start_pipeline("https://example.com/error")
    
    # Verify error handling
    assert state.status == AnalysisStatus.ANALYSIS_FAILED
    assert state.error_details is not None
    assert state.error_details.task == "analysis"
    assert state.error_details.type == "Exception"
    assert "Analysis error" in state.error_details.message
    
    # Verify component calls
    mock_scraper.scrape.assert_called_once()
    pipeline.analyzer.analyze.assert_called_once()
    mock_file_writer.save.assert_not_called()  # Should not call writer after analysis failure


def test_pipeline_save_failure(mock_scraper, mock_analyzer):
    """Test pipeline handling of save failures."""
    # Create pipeline with mock components
    pipeline = NewsPipelineFlow(output_dir="test_output")
    
    # Mock writer to fail
    def save_failure(state):
        state.status = AnalysisStatus.SAVE_FAILED
        state.set_error("save", Exception("Save error"))
        return state
    
    pipeline.scraper = mock_scraper
    pipeline.analyzer = mock_analyzer
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
    mock_scraper.scrape.assert_called_once()
    mock_analyzer.analyze.assert_called_once()
    pipeline.writer.save.assert_called_once()


def test_pipeline_retry_attempts(mock_analyzer, mock_file_writer):
    """Test pipeline retry attempts."""
    pipeline = NewsPipelineFlow(output_dir="test_output")

    # Set up mock analyzer to return success
    def successful_analyze(state):
        state.analysis_results = {"entities": {"PERSON": ["John Doe"]}}
        state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
        return state
    mock_analyzer.analyze = Mock(side_effect=successful_analyze)

    # Set up mock file writer to return success
    def successful_save(state):
        state.save_path = "test_output/test.json"
        state.status = AnalysisStatus.SAVE_SUCCEEDED
        return state
    mock_file_writer.save = Mock(side_effect=successful_save)

    # Mock the web scraper to fail once and then succeed
    class MockScraper(WebScraperTool):
        def __init__(self):
            super().__init__()
            self.call_count = 0

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            reraise=True
        )
        def scrape(self, state):
            self.call_count += 1
            print(f"MockScraper.scrape called (attempt {self.call_count})")

            if self.call_count == 1:
                # First call fails
                print("First attempt: Simulating network failure")
                state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
                state.set_error("scrape", Exception("Temporary failure"))
                raise Exception("Temporary failure")  # This will trigger the retry
            else:
                # Second call succeeds
                print("Second attempt: Simulating successful scrape")
                state.scraped_text = "Test article content"
                state.status = AnalysisStatus.SCRAPE_SUCCEEDED
                state.error_details = None  # Clear error details on success
                return state

    mock_scraper = MockScraper()
    pipeline.scraper = mock_scraper
    pipeline.analyzer = mock_analyzer
    pipeline.writer = mock_file_writer

    # Create initial state with failure
    state = NewsAnalysisState(target_url="https://example.com")
    state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
    state.set_error("scrape", Exception("Temporary failure"))

    print("\nStarting pipeline resume test...")
    print(f"Initial state status: {state.status}")
    print(f"Initial error details: {state.error_details}")

    # Resume pipeline
    state = pipeline.resume_pipeline("test_run", state)

    print(f"\nFinal state status: {state.status}")
    print(f"Final error details: {state.error_details}")
    print(f"Scraper call count: {mock_scraper.call_count}")
    print(f"Run logs: {state.run_logs}")

    # Verify the pipeline succeeded
    assert state.status == AnalysisStatus.SAVE_SUCCEEDED, f"Expected SAVE_SUCCEEDED but got {state.status}"
    assert state.error_details is None, f"Expected no errors but got {state.error_details}"
    assert state.scraped_text is not None
    assert state.analysis_results is not None
    assert state.save_path is not None

    # Verify the web scraper was called twice
    assert mock_scraper.call_count == 2, f"Expected 2 scraper calls but got {mock_scraper.call_count}"

    # Verify the retry attempt was logged
    assert any("Retry attempt" in log for log in state.run_logs), "No retry attempt found in logs"

    # Verify mock calls
    mock_analyzer.analyze.assert_called_once()
    mock_file_writer.save.assert_called_once()


def test_pipeline_invalid_url():
    """Test pipeline handling of invalid URLs."""
    pipeline = NewsPipelineFlow(output_dir="test_output")
    
    # Mock the URL validation in WebScraperTool
    with patch.object(pipeline.scraper, '_fetch_url') as mock_fetch:
        # Test with empty URL
        mock_fetch.side_effect = ValueError("Invalid URL: No scheme supplied")
        with pytest.raises(ValueError) as exc_info:
            pipeline.start_pipeline("")
        assert "Invalid URL" in str(exc_info.value)
        assert "No scheme supplied" in str(exc_info.value)

        # Test with malformed URL
        mock_fetch.side_effect = ValueError("Invalid URL: Invalid URL")
        with pytest.raises(ValueError) as exc_info:
            pipeline.start_pipeline("not-a-url")
        assert "Invalid URL" in str(exc_info.value) 
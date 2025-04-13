"""Tests for the news pipeline flow."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path

import pytest
from tenacity import retry, stop_after_attempt, wait_exponential

from local_newsifier.flows.news_pipeline import NewsPipelineFlow
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.web_scraper import WebScraperTool
from local_newsifier.tools.ner_analyzer import NERAnalyzerTool
from local_newsifier.tools.file_writer import FileWriterTool


@pytest.fixture(scope="function")
def mock_web_scraper():
    """Create a mock WebScraperTool instance that returns a successful state."""
    scraper = MagicMock()
    
    # Configure scrape_url to return a successful state
    def mock_scrape_url(url):
        return NewsAnalysisState(
            target_url=url,
            status=AnalysisStatus.CONTENT_EXTRACTED,
            scraped_text="Test article content",
            title="Test Article",
            published_date="2024-03-14"
        )
    
    scraper.scrape_url = MagicMock(side_effect=mock_scrape_url)
    return scraper


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
def mock_analyzer():
    """Create a mock analyzer that returns successful results."""

    def successful_analyze(state):
        state.analysis_results = {"entities": {"PERSON": ["John Doe"]}}
        state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
        return state

    analyzer = Mock()
    analyzer.analyze = Mock(side_effect=successful_analyze)
    return analyzer


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
def pipeline(mock_scraper, mock_analyzer, mock_file_writer):
    """Create a pipeline instance with mocked components."""
    with patch("local_newsifier.flows.news_pipeline.NERAnalyzerTool") as mock_ner:
        mock_ner.return_value = mock_analyzer
        pipeline = NewsPipelineFlow(output_dir="test_output")
        pipeline.scraper = mock_scraper
        pipeline.writer = mock_file_writer
        return pipeline


@pytest.fixture(autouse=True)
def reset_mocks(pipeline):
    """Reset all mocks before each test."""
    # Store original side effects
    scraper_effect = getattr(pipeline.scraper.scrape, "side_effect", None)
    analyzer_effect = getattr(pipeline.analyzer.analyze, "side_effect", None)
    writer_effect = getattr(pipeline.writer.save, "side_effect", None)

    # Reset mocks if they are Mock objects
    if isinstance(pipeline.scraper, Mock):
        pipeline.scraper.reset_mock()
    if isinstance(pipeline.analyzer, Mock):
        pipeline.analyzer.reset_mock()
    if isinstance(pipeline.writer, Mock):
        pipeline.writer.reset_mock()

    # Restore original side effects if they exist
    if scraper_effect is not None and isinstance(pipeline.scraper.scrape, Mock):
        pipeline.scraper.scrape.side_effect = scraper_effect
    if analyzer_effect is not None and isinstance(pipeline.analyzer.analyze, Mock):
        pipeline.analyzer.analyze.side_effect = analyzer_effect
    if writer_effect is not None and isinstance(pipeline.writer.save, Mock):
        pipeline.writer.save.side_effect = writer_effect

    yield


def test_pipeline_flow_success(pipeline):
    """Test successful pipeline execution from start to finish."""
    url = "https://example.com/test-article"
    
    # Mock the scraper to return successful state
    scrape_state = NewsAnalysisState(target_url=url)
    scrape_state.status = AnalysisStatus.SCRAPE_SUCCEEDED
    scrape_state.scraped_text = "Test article content"
    scrape_state.add_log("Scraping completed")
    pipeline.scraper = Mock()
    pipeline.scraper.scrape.return_value = scrape_state
    
    # Mock the analyzer to return successful state
    analyze_state = NewsAnalysisState(target_url=url)
    analyze_state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
    analyze_state.scraped_text = scrape_state.scraped_text
    analyze_state.analysis_results = {"entities": {"PERSON": ["John Doe"]}}
    analyze_state.add_log("Analysis completed")
    pipeline.analyzer = Mock()
    pipeline.analyzer.analyze.return_value = analyze_state
    
    # Mock the writer to return successful state
    final_state = NewsAnalysisState(target_url=url)
    final_state.status = AnalysisStatus.SAVE_SUCCEEDED
    final_state.scraped_text = analyze_state.scraped_text
    final_state.analysis_results = analyze_state.analysis_results
    final_state.saved_at = datetime.now()
    final_state.add_log("Save completed")
    pipeline.writer = Mock()
    pipeline.writer.save.return_value = final_state

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
    pipeline.analyzer.analyze.assert_called_once()
    pipeline.writer.save.assert_called_once()


def test_pipeline_resume_from_scrape_failed(pipeline):
    """Test pipeline resumption after scraping failure."""
    # Create failed state
    url = "https://example.com/failed"
    state = NewsAnalysisState(target_url=url)
    state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
    state.add_log("Initial scrape failed")
    
    # Mock the scraper to return successful state
    scrape_state = NewsAnalysisState(target_url=url)
    scrape_state.status = AnalysisStatus.SCRAPE_SUCCEEDED
    scrape_state.scraped_text = "Test article content"
    scrape_state.add_log("Retry scrape succeeded")
    pipeline.scraper = Mock()
    pipeline.scraper.scrape.return_value = scrape_state
    
    # Mock the analyzer to return successful state
    analyze_state = NewsAnalysisState(target_url=url)
    analyze_state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
    analyze_state.scraped_text = scrape_state.scraped_text
    analyze_state.analysis_results = {"entities": {"PERSON": ["John Doe"]}}
    analyze_state.add_log("Analysis completed")
    pipeline.analyzer = Mock()
    pipeline.analyzer.analyze.return_value = analyze_state
    
    # Mock the writer to return successful state
    final_state = NewsAnalysisState(target_url=url)
    final_state.status = AnalysisStatus.SAVE_SUCCEEDED
    final_state.scraped_text = analyze_state.scraped_text
    final_state.analysis_results = analyze_state.analysis_results
    final_state.saved_at = datetime.now()
    final_state.add_log("Save completed")
    pipeline.writer = Mock()
    pipeline.writer.save.return_value = final_state

    # Resume pipeline
    resumed_state = pipeline.resume_pipeline("test_run", state)

    # Verify recovery
    assert resumed_state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert resumed_state.scraped_text is not None
    assert resumed_state.analysis_results is not None
    assert resumed_state.saved_at is not None

    # Verify component calls
    pipeline.scraper.scrape.assert_called_once()
    pipeline.analyzer.analyze.assert_called_once()
    pipeline.writer.save.assert_called_once()


def test_pipeline_resume_from_analysis_failed(pipeline):
    """Test pipeline resumption after analysis failure."""
    # Create state with successful scrape but failed analysis
    url = "https://example.com/analysis-failed"
    state = NewsAnalysisState(target_url=url)
    state.status = AnalysisStatus.ANALYSIS_FAILED
    state.scraped_text = "Test content for analysis"
    state.add_log("Initial analysis failed")
    
    # Mock the analyzer to return successful state
    analyze_state = NewsAnalysisState(target_url=url)
    analyze_state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
    analyze_state.scraped_text = state.scraped_text
    analyze_state.analysis_results = {"entities": {"PERSON": ["John Doe"]}}
    analyze_state.add_log("Retry analysis succeeded")
    pipeline.analyzer = Mock()
    pipeline.analyzer.analyze.return_value = analyze_state
    
    # Mock the writer to return successful state
    final_state = NewsAnalysisState(target_url=url)
    final_state.status = AnalysisStatus.SAVE_SUCCEEDED
    final_state.scraped_text = analyze_state.scraped_text
    final_state.analysis_results = analyze_state.analysis_results
    final_state.saved_at = datetime.now()
    final_state.add_log("Save completed")
    pipeline.writer = Mock()
    pipeline.writer.save.return_value = final_state

    # Resume pipeline
    resumed_state = pipeline.resume_pipeline("test_run", state)

    # Verify recovery
    assert resumed_state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert resumed_state.analysis_results is not None
    assert resumed_state.saved_at is not None

    # Verify component calls
    pipeline.analyzer.analyze.assert_called_once()
    pipeline.writer.save.assert_called_once()


def test_pipeline_resume_from_save_failed(pipeline):
    """Test pipeline resumption after save failure."""
    # Create state with successful analysis but failed save
    url = "https://example.com/save-failed"
    state = NewsAnalysisState(target_url=url)
    state.status = AnalysisStatus.SAVE_FAILED
    state.scraped_text = "Test content"
    state.analysis_results = {"entities": {"PERSON": []}}
    state.add_log("Initial save failed")
    
    # Mock the writer to return successful state
    final_state = NewsAnalysisState(target_url=url)
    final_state.status = AnalysisStatus.SAVE_SUCCEEDED
    final_state.scraped_text = state.scraped_text
    final_state.analysis_results = state.analysis_results
    final_state.saved_at = datetime.now()
    final_state.add_log("Retry save succeeded")
    pipeline.writer = Mock()
    pipeline.writer.save.return_value = final_state

    # Resume pipeline
    resumed_state = pipeline.resume_pipeline("test_run", state)

    # Verify recovery
    assert resumed_state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert resumed_state.saved_at is not None

    # Verify component calls
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
    # Replace components with mocks
    pipeline.scraper = Mock()
    pipeline.analyzer = Mock()
    pipeline.writer = Mock()

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
    pipeline.analyzer.analyze.assert_not_called()
    pipeline.writer.save.assert_not_called()


def test_pipeline_analysis_failure(pipeline):
    """Test pipeline handling of analysis failures."""
    # Replace components with mocks
    pipeline.scraper = Mock()
    pipeline.analyzer = Mock()
    pipeline.writer = Mock()

    # Mock scraper to succeed
    def successful_scrape(state):
        state.scraped_text = "Test article content"
        state.status = AnalysisStatus.SCRAPE_SUCCEEDED
        return state

    pipeline.scraper.scrape = Mock(side_effect=successful_scrape)

    # Mock analyzer to fail
    def analysis_failure(state):
        state.status = AnalysisStatus.ANALYSIS_FAILED
        state.set_error("analysis", Exception("Analysis error"))
        return state

    pipeline.analyzer.analyze = Mock(side_effect=analysis_failure)

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
    pipeline.analyzer.analyze.assert_called_once()
    pipeline.writer.save.assert_not_called()


def test_pipeline_save_failure(pipeline):
    """Test pipeline handling of save failures."""

    # Mock scraper to succeed
    def successful_scrape(state):
        state.scraped_text = "Test article content"
        state.status = AnalysisStatus.SCRAPE_SUCCEEDED
        return state

    pipeline.scraper.scrape = Mock(side_effect=successful_scrape)

    # Mock analyzer to succeed
    def successful_analyze(state):
        state.analysis_results = {"entities": {"PERSON": ["John Doe"]}}
        state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
        return state

    pipeline.analyzer.analyze = Mock(side_effect=successful_analyze)

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
    pipeline.analyzer.analyze.assert_called_once()
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

    # Mock analyzer to succeed
    def successful_analyze(state):
        state.analysis_results = {"entities": {"PERSON": ["John Doe"]}}
        state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
        return state

    pipeline.analyzer.analyze = Mock(side_effect=successful_analyze)

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
    # Replace components with mocks
    pipeline.scraper = Mock()
    pipeline.analyzer = Mock()
    pipeline.writer = Mock()

    # Mock scraper to raise ValueError for invalid URL
    def invalid_url_scrape(state):
        raise ValueError("Invalid URL: not-a-url")

    pipeline.scraper.scrape = Mock(side_effect=invalid_url_scrape)

    # Start pipeline with invalid URL
    with pytest.raises(ValueError) as exc_info:
        pipeline.start_pipeline("not-a-url")
    assert "Invalid URL" in str(exc_info.value)

    # Verify component calls
    pipeline.scraper.scrape.assert_called_once()
    pipeline.analyzer.analyze.assert_not_called()
    pipeline.writer.save.assert_not_called()


@pytest.fixture
def pipeline():
    pipeline = NewsPipelineFlow(output_dir="test_output")
    # Don't mock components in the fixture, let individual tests handle mocking
    return pipeline


@pytest.fixture
def mock_state():
    return NewsAnalysisState(target_url="https://example.com")


def test_pipeline_initialization():
    pipeline = NewsPipelineFlow(output_dir="test_output")
    assert isinstance(pipeline.scraper, WebScraperTool)
    assert isinstance(pipeline.analyzer, NERAnalyzerTool)
    assert isinstance(pipeline.writer, FileWriterTool)
    assert isinstance(pipeline.writer.output_dir, Path)
    assert str(pipeline.writer.output_dir) == "test_output"


def test_scrape_content(pipeline, mock_state):
    pipeline.scraper = Mock()
    pipeline.scraper.scrape.return_value = mock_state
    result = pipeline.scrape_content(mock_state)
    assert result == mock_state
    pipeline.scraper.scrape.assert_called_once_with(mock_state)


def test_analyze_content(pipeline, mock_state):
    pipeline.analyzer = Mock()
    pipeline.analyzer.analyze.return_value = mock_state
    result = pipeline.analyze_content(mock_state)
    assert result == mock_state
    pipeline.analyzer.analyze.assert_called_once_with(mock_state)


def test_save_results(pipeline, mock_state):
    pipeline.writer = Mock()
    pipeline.writer.save.return_value = mock_state
    result = pipeline.save_results(mock_state)
    assert result == mock_state
    pipeline.writer.save.assert_called_once_with(mock_state)


@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.scrape_content")
@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.analyze_content")
@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.save_results")
def test_start_pipeline_success(
    mock_save, mock_analyze, mock_scrape, pipeline, mock_state
):
    # Mock the state transitions
    scrape_state = NewsAnalysisState(target_url="https://example.com")
    scrape_state.status = AnalysisStatus.SCRAPE_SUCCEEDED
    
    analyze_state = NewsAnalysisState(target_url="https://example.com")
    analyze_state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
    
    final_state = NewsAnalysisState(target_url="https://example.com")
    final_state.status = AnalysisStatus.SAVE_SUCCEEDED
    
    mock_scrape.return_value = scrape_state
    mock_analyze.return_value = analyze_state
    mock_save.return_value = final_state
    
    result = pipeline.start_pipeline("https://example.com")
    assert result.status == AnalysisStatus.SAVE_SUCCEEDED
    mock_scrape.assert_called_once()
    mock_analyze.assert_called_once()
    mock_save.assert_called_once()


@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.scrape_content")
def test_start_pipeline_scrape_failure(mock_scrape, pipeline):
    # Mock failed scrape
    failed_state = NewsAnalysisState(target_url="https://example.com")
    failed_state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
    mock_scrape.return_value = failed_state
    
    result = pipeline.start_pipeline("https://example.com")
    assert result.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
    mock_scrape.assert_called_once()


def test_resume_pipeline_no_state(pipeline):
    with pytest.raises(NotImplementedError):
        pipeline.resume_pipeline("test_run_id")


@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.scrape_content")
@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.analyze_content")
@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.save_results")
def test_resume_pipeline_from_initialized(
    mock_save, mock_analyze, mock_scrape, pipeline, mock_state
):
    mock_state.status = AnalysisStatus.INITIALIZED
    
    # Mock successful state transitions
    scrape_state = NewsAnalysisState(target_url="https://example.com")
    scrape_state.status = AnalysisStatus.SCRAPE_SUCCEEDED
    analyze_state = NewsAnalysisState(target_url="https://example.com")
    analyze_state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
    final_state = NewsAnalysisState(target_url="https://example.com")
    final_state.status = AnalysisStatus.SAVE_SUCCEEDED
    
    mock_scrape.return_value = scrape_state
    mock_analyze.return_value = analyze_state
    mock_save.return_value = final_state
    
    result = pipeline.resume_pipeline("test_run_id", mock_state)
    assert result.status == AnalysisStatus.SAVE_SUCCEEDED
    mock_scrape.assert_called_once()
    mock_analyze.assert_called_once()
    mock_save.assert_called_once()


@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.analyze_content")
@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.save_results")
def test_resume_pipeline_from_scrape_succeeded(
    mock_save, mock_analyze, pipeline, mock_state
):
    mock_state.status = AnalysisStatus.SCRAPE_SUCCEEDED
    
    # Mock successful state transitions
    analyze_state = NewsAnalysisState(target_url="https://example.com")
    analyze_state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
    final_state = NewsAnalysisState(target_url="https://example.com")
    final_state.status = AnalysisStatus.SAVE_SUCCEEDED
    
    mock_analyze.return_value = analyze_state
    mock_save.return_value = final_state
    
    result = pipeline.resume_pipeline("test_run_id", mock_state)
    assert result.status == AnalysisStatus.SAVE_SUCCEEDED
    mock_analyze.assert_called_once()
    mock_save.assert_called_once()


@patch("local_newsifier.flows.news_pipeline.NewsPipelineFlow.save_results")
def test_resume_pipeline_from_analysis_succeeded(mock_save, pipeline, mock_state):
    mock_state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
    
    final_state = NewsAnalysisState(target_url="https://example.com")
    final_state.status = AnalysisStatus.SAVE_SUCCEEDED
    mock_save.return_value = final_state
    
    result = pipeline.resume_pipeline("test_run_id", mock_state)
    assert result.status == AnalysisStatus.SAVE_SUCCEEDED
    mock_save.assert_called_once()


def test_resume_pipeline_invalid_status(pipeline, mock_state):
    mock_state.status = AnalysisStatus.SAVE_SUCCEEDED
    with pytest.raises(ValueError):
        pipeline.resume_pipeline("test_run_id", mock_state)

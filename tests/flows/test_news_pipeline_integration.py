"""Integration tests for the NewsPipelineFlow with the service layer."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock spaCy and TextBlob before imports
patch("spacy.load", MagicMock(return_value=MagicMock())).start()
patch(
    "textblob.TextBlob",
    MagicMock(return_value=MagicMock(sentiment=MagicMock(polarity=0.5, subjectivity=0.7))),
).start()
patch("spacy.language.Language", MagicMock()).start()

from tests.ci_skip_config import ci_skip
from tests.fixtures.event_loop import event_loop_fixture


@patch("local_newsifier.flows.news_pipeline.EntityService")
@patch("local_newsifier.flows.news_pipeline.EntityExtractor")
@patch("local_newsifier.flows.news_pipeline.ContextAnalyzer")
@patch("local_newsifier.flows.news_pipeline.EntityResolver")
@patch("local_newsifier.tools.entity_tracker_service.EntityExtractor")
def test_news_pipeline_with_entity_service(
    mock_extractor_tracker,
    mock_resolver_class,
    mock_analyzer_class,
    mock_extractor_class,
    mock_entity_service_class,
):
    """Test that the news pipeline works with the entity service."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
    from local_newsifier.services.article_service import ArticleService
    from local_newsifier.services.news_pipeline_service import NewsPipelineService
    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
    from local_newsifier.tools.file_writer import FileWriterTool
    from local_newsifier.tools.sentiment_analyzer import SentimentAnalyzer
    from local_newsifier.tools.web_scraper import WebScraperTool

    # Create a mock for EntityService that will be returned by the class
    mock_entity_service = MagicMock()
    mock_entity_service_class.return_value = mock_entity_service

    # Create mocks
    mock_scraper = MagicMock(spec=WebScraperTool)
    mock_writer = MagicMock(spec=FileWriterTool)
    mock_entity_extractor = MagicMock(spec=EntityExtractor)
    mock_sentiment_analyzer = MagicMock(spec=SentimentAnalyzer)
    mock_article_service = MagicMock(spec=ArticleService)
    mock_pipeline_service = MagicMock(spec=NewsPipelineService)

    # Setup mocks
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    mock_extractor_tracker.return_value = mock_extractor

    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer

    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver

    # Create pipeline with mocked dependencies
    pipeline = NewsPipelineFlow(
        web_scraper=mock_scraper,
        file_writer=mock_writer,
        entity_extractor=mock_entity_extractor,
        article_service=mock_article_service,
        pipeline_service=mock_pipeline_service,
    )

    # Mock the scraper to return test data
    mock_state = NewsAnalysisState(
        target_url="https://example.com",
        scraped_text="John Doe visited New York City yesterday.",
        scraped_title="Local Visit",
        scraped_at=datetime(2025, 1, 1),
        status=AnalysisStatus.SCRAPE_SUCCEEDED,
    )
    pipeline.scraper.scrape = MagicMock(return_value=mock_state)

    # Mock the article service
    pipeline.article_service.process_article = MagicMock(
        return_value={
            "article_id": 1,
            "title": "Local Visit",
            "url": "https://example.com",
            "entities": [
                {
                    "original_text": "John Doe",
                    "canonical_name": "John Doe",
                    "canonical_id": 1,
                    "context": "John Doe visited New York City yesterday.",
                    "sentiment_score": 0.5,
                    "framing_category": "neutral",
                },
                {
                    "original_text": "New York City",
                    "canonical_name": "New York City",
                    "canonical_id": 2,
                    "context": "John Doe visited New York City yesterday.",
                    "sentiment_score": 0.0,
                    "framing_category": "neutral",
                },
            ],
            "analysis_result": {
                "entities": [
                    {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1},
                    {
                        "original_text": "New York City",
                        "canonical_name": "New York City",
                        "canonical_id": 2,
                    },
                ],
                "statistics": {"entity_counts": {"PERSON": 1, "GPE": 1}, "total_entities": 2},
            },
        }
    )

    # Mock the file writer
    mock_result_state = NewsAnalysisState(
        target_url="https://example.com",
        scraped_text="John Doe visited New York City yesterday.",
        scraped_title="Local Visit",
        scraped_at=datetime(2025, 1, 1),
        status=AnalysisStatus.SAVE_SUCCEEDED,
        analysis_results={
            "entities": [
                {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1},
                {
                    "original_text": "New York City",
                    "canonical_name": "New York City",
                    "canonical_id": 2,
                },
            ],
            "statistics": {"entity_counts": {"PERSON": 1, "GPE": 1}, "total_entities": 2},
        },
    )
    pipeline.writer.save = MagicMock(return_value=mock_result_state)

    # If the class has async methods, directly replace them with mocks
    if hasattr(pipeline, "start_pipeline_async"):
        pipeline.start_pipeline_async = AsyncMock(return_value=mock_result_state)
    if hasattr(pipeline.scraper, "scrape_async"):
        pipeline.scraper.scrape_async = AsyncMock(return_value=mock_state)
    if hasattr(pipeline.writer, "save_async"):
        pipeline.writer.save_async = AsyncMock(return_value=mock_result_state)

    # Act - Use the synchronous method directly
    result = pipeline.start_pipeline("https://example.com")

    # Assert
    assert result.status == AnalysisStatus.SAVE_SUCCEEDED
    assert "entities" in result.analysis_results
    assert len(result.analysis_results["entities"]) == 2

    # Verify service was called
    pipeline.article_service.process_article.assert_called_once()


@patch("local_newsifier.flows.news_pipeline.EntityService")
@patch("local_newsifier.flows.news_pipeline.EntityExtractor")
@patch("local_newsifier.flows.news_pipeline.ContextAnalyzer")
@patch("local_newsifier.flows.news_pipeline.EntityResolver")
@patch("local_newsifier.tools.entity_tracker_service.EntityExtractor")
def test_process_url_directly(
    mock_extractor_tracker,
    mock_resolver_class,
    mock_analyzer_class,
    mock_extractor_class,
    mock_entity_service_class,
):
    """Test processing a URL directly using the pipeline service."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.services.article_service import ArticleService
    from local_newsifier.services.news_pipeline_service import NewsPipelineService
    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
    from local_newsifier.tools.file_writer import FileWriterTool
    from local_newsifier.tools.sentiment_analyzer import SentimentAnalyzer
    from local_newsifier.tools.web_scraper import WebScraperTool

    # Create a mock for EntityService that will be returned by the class
    mock_entity_service = MagicMock()
    mock_entity_service_class.return_value = mock_entity_service

    # Create mocks
    mock_scraper = MagicMock(spec=WebScraperTool)
    mock_writer = MagicMock(spec=FileWriterTool)
    mock_entity_extractor = MagicMock(spec=EntityExtractor)
    mock_sentiment_analyzer = MagicMock(spec=SentimentAnalyzer)
    mock_article_service = MagicMock(spec=ArticleService)
    mock_pipeline_service = MagicMock(spec=NewsPipelineService)

    # Setup mocks
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    mock_extractor_tracker.return_value = mock_extractor

    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer

    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver

    # Create pipeline with mocked dependencies
    pipeline = NewsPipelineFlow(
        web_scraper=mock_scraper,
        file_writer=mock_writer,
        entity_extractor=mock_entity_extractor,
        article_service=mock_article_service,
        pipeline_service=mock_pipeline_service,
    )

    # The expected result
    expected_result = {
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

    # Mock the pipeline service
    pipeline.pipeline_service.process_url = MagicMock(return_value=expected_result)

    # If the class has async methods, directly replace them with mocks
    if hasattr(pipeline, "process_url_directly_async"):
        pipeline.process_url_directly_async = AsyncMock(return_value=expected_result)
    if hasattr(pipeline.pipeline_service, "process_url_async"):
        pipeline.pipeline_service.process_url_async = AsyncMock(return_value=expected_result)

    # Act - Use the synchronous method directly
    result = pipeline.process_url_directly("https://example.com")

    # Assert
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert len(result["entities"]) == 1
    assert result["entities"][0]["original_text"] == "John Doe"

    # Verify service was called
    pipeline.pipeline_service.process_url.assert_called_once_with("https://example.com")


@patch("local_newsifier.flows.news_pipeline.EntityService")
@patch("local_newsifier.flows.news_pipeline.EntityExtractor")
@patch("local_newsifier.flows.news_pipeline.ContextAnalyzer")
@patch("local_newsifier.flows.news_pipeline.EntityResolver")
@patch("local_newsifier.tools.entity_tracker_service.EntityExtractor")
def test_integration_with_entity_tracking(
    mock_extractor_tracker,
    mock_resolver_class,
    mock_analyzer_class,
    mock_extractor_class,
    mock_entity_service_class,
):
    """Test integration with entity tracking components."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
    from local_newsifier.services.article_service import ArticleService
    from local_newsifier.services.news_pipeline_service import NewsPipelineService
    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
    from local_newsifier.tools.file_writer import FileWriterTool
    from local_newsifier.tools.sentiment_analyzer import SentimentAnalyzer
    from local_newsifier.tools.web_scraper import WebScraperTool

    # Create a mock for EntityService that will be returned by the class
    mock_entity_service = MagicMock()
    mock_entity_service_class.return_value = mock_entity_service

    # Create mocks
    mock_scraper = MagicMock(spec=WebScraperTool)
    mock_writer = MagicMock(spec=FileWriterTool)
    mock_entity_extractor = MagicMock(spec=EntityExtractor)
    mock_sentiment_analyzer = MagicMock(spec=SentimentAnalyzer)
    mock_article_service = MagicMock(spec=ArticleService)
    mock_pipeline_service = MagicMock(spec=NewsPipelineService)

    # Setup mocks
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    mock_extractor_tracker.return_value = mock_extractor

    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer

    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver

    # Create pipeline with mocked dependencies
    pipeline = NewsPipelineFlow(
        web_scraper=mock_scraper,
        file_writer=mock_writer,
        entity_extractor=mock_entity_extractor,
        article_service=mock_article_service,
        pipeline_service=mock_pipeline_service,
    )

    # The expected article service result
    article_result = {
        "article_id": 1,
        "title": "Local Visit",
        "url": "https://example.com",
        "entities": [
            {
                "original_text": "John Doe",
                "canonical_name": "John Doe",
                "canonical_id": 1,
                "context": "John Doe visited New York City yesterday.",
                "sentiment_score": 0.5,
                "framing_category": "neutral",
            }
        ],
        "analysis_result": {
            "entities": [
                {
                    "original_text": "John Doe",
                    "canonical_name": "John Doe",
                    "canonical_id": 1,
                    "context": "John Doe visited New York City yesterday.",
                    "sentiment_score": 0.5,
                    "framing_category": "neutral",
                }
            ],
            "statistics": {"entity_counts": {"PERSON": 1}, "total_entities": 1},
        },
    }

    # Mock the article service to avoid database operations
    pipeline.article_service.process_article = MagicMock(return_value=article_result)

    # Mock states for scraper and writer
    scraper_state = NewsAnalysisState(
        target_url="https://example.com",
        scraped_text="John Doe visited New York City yesterday.",
        scraped_title="Local Visit",
        scraped_at=datetime(2025, 1, 1),
        status=AnalysisStatus.SCRAPE_SUCCEEDED,
    )

    writer_state = NewsAnalysisState(
        target_url="https://example.com",
        scraped_text="John Doe visited New York City yesterday.",
        scraped_title="Local Visit",
        scraped_at=datetime(2025, 1, 1),
        status=AnalysisStatus.SAVE_SUCCEEDED,
        analysis_results={
            "entities": [
                {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1}
            ]
        },
    )

    # Mock the service methods
    pipeline.scraper.scrape = MagicMock(return_value=scraper_state)
    pipeline.writer.save = MagicMock(return_value=writer_state)

    # If the class has async methods, directly replace them with mocks
    if hasattr(pipeline, "start_pipeline_async"):
        pipeline.start_pipeline_async = AsyncMock(return_value=writer_state)
    if hasattr(pipeline.article_service, "process_article_async"):
        pipeline.article_service.process_article_async = AsyncMock(return_value=article_result)
    if hasattr(pipeline.scraper, "scrape_async"):
        pipeline.scraper.scrape_async = AsyncMock(return_value=scraper_state)
    if hasattr(pipeline.writer, "save_async"):
        pipeline.writer.save_async = AsyncMock(return_value=writer_state)

    # Act - Use the synchronous method directly
    result = pipeline.start_pipeline("https://example.com")

    # Assert
    assert result.status == AnalysisStatus.SAVE_SUCCEEDED

    # Verify article service was called
    pipeline.article_service.process_article.assert_called_once()

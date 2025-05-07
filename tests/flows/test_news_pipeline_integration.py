"""Integration tests for the NewsPipelineFlow with the service layer."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Mock spaCy and TextBlob before imports
patch('spacy.load', MagicMock(return_value=MagicMock())).start()
patch('textblob.TextBlob', MagicMock(return_value=MagicMock(
    sentiment=MagicMock(polarity=0.5, subjectivity=0.7)
))).start()
patch('spacy.language.Language', MagicMock()).start()

@patch("local_newsifier.flows.news_pipeline.EntityExtractor")
@patch("local_newsifier.flows.news_pipeline.ContextAnalyzer")
@patch("local_newsifier.flows.news_pipeline.EntityResolver")
@patch("local_newsifier.tools.entity_tracker_service.EntityExtractor")
def test_news_pipeline_with_entity_service(
    mock_extractor_tracker, mock_resolver_class, mock_analyzer_class, mock_extractor_class
):
    """Test that the news pipeline works with the entity service."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus
    
    # Setup mocks
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    mock_extractor_tracker.return_value = mock_extractor
    
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer
    
    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver
    
    # Create pipeline with mocked dependencies
    with patch("local_newsifier.flows.news_pipeline.EntityService") as mock_entity_service_class:
        with patch("local_newsifier.flows.news_pipeline.ArticleService") as mock_article_service_class:
            # Create pipeline with mocked entity service
            pipeline = NewsPipelineFlow()
            
            # Mock the scraper to return test data
            pipeline.scraper.scrape = MagicMock(return_value=NewsAnalysisState(
                target_url="https://example.com",
                scraped_text="John Doe visited New York City yesterday.",
                scraped_title="Local Visit",
                scraped_at=datetime(2025, 1, 1),
                status=AnalysisStatus.SCRAPE_SUCCEEDED
            ))
            
            # Mock the article service
            pipeline.article_service.process_article = MagicMock(return_value={
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
                        "framing_category": "neutral"
                    },
                    {
                        "original_text": "New York City",
                        "canonical_name": "New York City",
                        "canonical_id": 2,
                        "context": "John Doe visited New York City yesterday.",
                        "sentiment_score": 0.0,
                        "framing_category": "neutral"
                    }
                ],
                "analysis_result": {
                    "entities": [
                        {
                            "original_text": "John Doe",
                            "canonical_name": "John Doe",
                            "canonical_id": 1
                        },
                        {
                            "original_text": "New York City",
                            "canonical_name": "New York City",
                            "canonical_id": 2
                        }
                    ],
                    "statistics": {
                        "entity_counts": {
                            "PERSON": 1,
                            "GPE": 1
                        },
                        "total_entities": 2
                    }
                }
            })
            
            # Mock the file writer
            pipeline.writer.save = MagicMock(return_value=NewsAnalysisState(
                target_url="https://example.com",
                scraped_text="John Doe visited New York City yesterday.",
                scraped_title="Local Visit",
                scraped_at=datetime(2025, 1, 1),
                status=AnalysisStatus.SAVE_SUCCEEDED,
                analysis_results={
                    "entities": [
                        {
                            "original_text": "John Doe",
                            "canonical_name": "John Doe",
                            "canonical_id": 1
                        },
                        {
                            "original_text": "New York City",
                            "canonical_name": "New York City",
                            "canonical_id": 2
                        }
                    ],
                    "statistics": {
                        "entity_counts": {
                            "PERSON": 1,
                            "GPE": 1
                        },
                        "total_entities": 2
                    }
                }
            ))
            
            # Act
            result = pipeline.start_pipeline("https://example.com")
            
            # Assert
            assert result.status == AnalysisStatus.SAVE_SUCCEEDED
            assert "entities" in result.analysis_results
            assert result.analysis_results["statistics"]["total_entities"] == 2
            
            # Verify service was called
            pipeline.article_service.process_article.assert_called_once()

@patch("local_newsifier.flows.news_pipeline.EntityExtractor")
@patch("local_newsifier.flows.news_pipeline.ContextAnalyzer")
@patch("local_newsifier.flows.news_pipeline.EntityResolver")
@patch("local_newsifier.tools.entity_tracker_service.EntityExtractor")
def test_process_url_directly(
    mock_extractor_tracker, mock_resolver_class, mock_analyzer_class, mock_extractor_class
):
    """Test processing a URL directly using the pipeline service."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    
    # Setup mocks
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    mock_extractor_tracker.return_value = mock_extractor
    
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer
    
    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver
    
    # Create pipeline with mocked dependencies
    with patch("local_newsifier.flows.news_pipeline.EntityService") as mock_entity_service_class:
        with patch("local_newsifier.flows.news_pipeline.ArticleService") as mock_article_service_class:
            with patch("local_newsifier.flows.news_pipeline.NewsPipelineService") as mock_pipeline_service_class:
                # Create pipeline with mocked entity service
                pipeline = NewsPipelineFlow()
                
                # Mock the pipeline service
                pipeline.pipeline_service.process_url = MagicMock(return_value={
                    "article_id": 1,
                    "title": "Test Article",
                    "url": "https://example.com",
                    "entities": [
                        {
                            "original_text": "John Doe",
                            "canonical_name": "John Doe",
                            "canonical_id": 1
                        }
                    ],
                    "analysis_result": {
                        "entities": [
                            {
                                "original_text": "John Doe",
                                "canonical_name": "John Doe",
                                "canonical_id": 1
                            }
                        ],
                        "statistics": {
                            "total_entities": 1
                        }
                    }
                })
                
                # Act
                result = pipeline.process_url_directly("https://example.com")
                
                # Assert
                assert result["article_id"] == 1
                assert result["title"] == "Test Article"
                assert len(result["entities"]) == 1
                assert result["entities"][0]["original_text"] == "John Doe"
                
                # Verify service was called
                pipeline.pipeline_service.process_url.assert_called_once_with("https://example.com")

@patch("local_newsifier.flows.news_pipeline.EntityExtractor")
@patch("local_newsifier.flows.news_pipeline.ContextAnalyzer")
@patch("local_newsifier.flows.news_pipeline.EntityResolver")
@patch("local_newsifier.tools.entity_tracker_service.EntityExtractor")
def test_integration_with_entity_tracking(
    mock_extractor_tracker, mock_resolver_class, mock_analyzer_class, mock_extractor_class
):
    """Test integration with entity tracking components."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus
    
    # Setup mocks
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    mock_extractor_tracker.return_value = mock_extractor
    
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer
    
    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver
    
    # Create pipeline with mocked dependencies
    with patch("local_newsifier.flows.news_pipeline.EntityService") as mock_entity_service_class:
        with patch("local_newsifier.flows.news_pipeline.ArticleService") as mock_article_service_class:
            # Create pipeline with mocked entity service
            pipeline = NewsPipelineFlow()
            
            # Mock the article service to avoid database operations
            pipeline.article_service.process_article = MagicMock(return_value={
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
                        "framing_category": "neutral"
                    }
                ],
                "analysis_result": {
                    "entities": [
                        {
                            "original_text": "John Doe",
                            "canonical_name": "John Doe",
                            "canonical_id": 1
                        }
                    ],
                    "statistics": {
                        "entity_counts": {
                            "PERSON": 1
                        },
                        "total_entities": 1
                    }
                }
            })
            
            # Mock the scraper to return test data
            pipeline.scraper.scrape = MagicMock(return_value=NewsAnalysisState(
                target_url="https://example.com",
                scraped_text="John Doe visited New York City yesterday.",
                scraped_title="Local Visit",
                scraped_at=datetime(2025, 1, 1),
                status=AnalysisStatus.SCRAPE_SUCCEEDED
            ))
            
            # Mock the file writer
            pipeline.writer.save = MagicMock(return_value=NewsAnalysisState(
                target_url="https://example.com",
                scraped_text="John Doe visited New York City yesterday.",
                scraped_title="Local Visit",
                scraped_at=datetime(2025, 1, 1),
                status=AnalysisStatus.SAVE_SUCCEEDED,
                analysis_results={
                    "entities": [
                        {
                            "original_text": "John Doe",
                            "canonical_name": "John Doe",
                            "canonical_id": 1
                        }
                    ],
                    "statistics": {
                        "entity_counts": {
                            "PERSON": 1
                        },
                        "total_entities": 1
                    }
                }
            ))
            
            # Act
            result = pipeline.start_pipeline("https://example.com")
            
            # Assert
            assert result.status == AnalysisStatus.SAVE_SUCCEEDED
            
            # Verify article service was called
            pipeline.article_service.process_article.assert_called_once()

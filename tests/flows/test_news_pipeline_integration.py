"""Integration tests for the NewsPipelineFlow with the service layer."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

def test_news_pipeline_with_entity_service():
    """Test that the news pipeline works with the entity service."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus
    
    # Create pipeline with mocked dependencies
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

def test_process_url_directly():
    """Test processing a URL directly using the pipeline service."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    
    # Create pipeline with mocked dependencies
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

def test_integration_with_entity_tracking():
    """Test integration with entity tracking components."""
    # Arrange
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus
    
    # Create pipeline with mocked dependencies
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

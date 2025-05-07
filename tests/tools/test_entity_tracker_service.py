"""Tests for the injectable EntityTracker tool."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

def test_entity_tracker_uses_injected_service():
    """Test that EntityTracker uses the injected entity service."""
    # Arrange
    mock_service = MagicMock()
    mock_service.process_article_entities.return_value = [
        {
            "original_text": "John Doe",
            "canonical_name": "John Doe",
            "canonical_id": 1,
            "context": "John Doe visited the city.",
            "sentiment_score": 0.5,
            "framing_category": "neutral"
        }
    ]
    
    # Create EntityTracker with mock service
    from local_newsifier.tools.entity_tracker_service import EntityTracker
    tracker = EntityTracker(entity_service=mock_service)
    
    # Act
    result = tracker.process_article(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Assert
    mock_service.process_article_entities.assert_called_once_with(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    assert len(result) == 1
    assert result[0]["original_text"] == "John Doe"
    assert result[0]["canonical_name"] == "John Doe"
    assert result[0]["sentiment_score"] == 0.5


def test_entity_tracker_provider(monkeypatch):
    """Test that the entity tracker provider creates a properly configured instance."""
    # Arrange
    mock_entity_service = MagicMock()
    
    # Mock the entity service provider
    def mock_get_entity_service():
        return mock_entity_service
    
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_entity_service", 
        mock_get_entity_service
    )
    
    # Import the provider function
    from local_newsifier.di.providers import get_entity_tracker_tool
    
    # Act
    tracker = get_entity_tracker_tool(entity_service=mock_entity_service)
    
    # Assert
    assert tracker.entity_service == mock_entity_service
